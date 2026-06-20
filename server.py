#!/usr/bin/env python3
"""
Daniel — personal voice AI agent (local dev server).

Serves a browser UI at http://localhost:4444 and proxies the voice pipeline
server-side (so your API keys never touch the browser):

    browser mic ──► /api/converse ──► Deepgram Nova-3 (STT)
                                       └─► Claude (reasoning + web search)
    browser plays ◄── base64 WAV ◄──── Deepgram Aura-2 "theia" (TTS)

Setup
-----
    pip install -r requirements.txt

    export DEEPGRAM_API_KEY="dg_..."
    export ANTHROPIC_API_KEY="sk-ant-..."

Run
---
    python server.py
    # then open http://localhost:4444  (hold the button to talk; release to send)
"""

import os
import json
import base64

import requests
from flask import Flask, request, jsonify, Response
from anthropic import Anthropic

# ───────────────────────────── Config ──────────────────────────────
PORT = int(os.getenv("PORT", "4444"))
VOICE = "aura-2-theia-en"            # Deepgram Aura-2 "Theia" (American female)
MODEL = os.getenv("MODEL", "claude-opus-4-8")     # opus = depth; sonnet-4-6 = faster, haiku-4-5 = fastest
STT_MODEL = "nova-3"
ENABLE_WEB_SEARCH = True
MAX_TOKENS = 400
HISTORY_TURNS = 20
ASSISTANT_NAME = os.getenv("AGENT_NAME", "Ada")   # what the agent calls itself
USER_NAME = os.getenv("USER_NAME", "Daniel")      # who it's talking to
HISTORY_FILE = os.getenv("HISTORY_FILE", "history.json")  # persisted across restarts

SYSTEM_PROMPT = (
    f"You are {ASSISTANT_NAME}, {USER_NAME}'s personal voice assistant. You are being "
    "spoken aloud, so:\n"
    f"- You're speaking with {USER_NAME}. Address them naturally; you don't need to say "
    "their name in every reply.\n"
    "- Keep replies to 2-4 sentences unless explicitly asked to go deeper. "
    "No bullet points, no markdown, no headings - this is speech.\n"
    "- Be warm, direct, and quick-witted. Dry humour is welcome. Skip filler like "
    "'great question' and excessive caveats.\n"
    "- You can discuss and debate: take a position, give reasons, push back when "
    f"{USER_NAME} is wrong rather than just agreeing.\n"
    "- If a request is genuinely ambiguous, ask one short clarifying question.\n"
    "- When you use web results, give the bottom line first, then one sentence on why "
    "it matters. Don't read out long URLs."
)

app = Flask(__name__)


# ──────────────────────────── Memory ───────────────────────────────
def load_history():
    """Restore conversation memory from disk so it survives restarts."""
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history():
    """Persist the last HISTORY_TURNS messages to disk (best-effort)."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-HISTORY_TURNS:], f)
    except OSError:
        pass


history = load_history()   # conversation memory, persisted across restarts


# ──────────────────────────── Pipeline ─────────────────────────────
def dg_key():
    return os.getenv("DEEPGRAM_API_KEY")


def transcribe(audio_bytes, mimetype):
    r = requests.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": STT_MODEL, "smart_format": "true", "punctuate": "true"},
        headers={"Authorization": f"Token {dg_key()}", "Content-Type": mimetype or "audio/webm"},
        data=audio_bytes, timeout=30,
    )
    r.raise_for_status()
    return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"].strip()


def synthesize(text):
    r = requests.post(
        "https://api.deepgram.com/v1/speak",
        params={"model": VOICE},  # REST default: linear16 / wav / 24 kHz
        headers={"Authorization": f"Token {dg_key()}", "Content-Type": "application/json"},
        json={"text": text}, timeout=30,
    )
    r.raise_for_status()
    return r.content


def ask_claude(messages):
    client = Anthropic()  # reads ANTHROPIC_API_KEY
    kwargs = dict(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM_PROMPT, messages=messages)
    if ENABLE_WEB_SEARCH:
        # _20260209 adds dynamic filtering and is supported on Sonnet 4.6 / Opus 4.6+.
        kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}]
    resp = client.messages.create(**kwargs)
    parts = [b.text.strip() for b in resp.content
             if getattr(b, "type", None) == "text" and b.text.strip()]
    return " ".join(parts) or "I'm not sure how to answer that one."


# ──────────────────────────── Routes ───────────────────────────────
@app.get("/")
def index():
    html = (INDEX_HTML
            .replace("__VOICE__", VOICE)
            .replace("__MODEL__", MODEL)
            .replace("__NAME__", ASSISTANT_NAME))
    return Response(html, mimetype="text/html")


@app.get("/api/health")
def health():
    return jsonify(
        ok=True,
        deepgram_key=bool(os.getenv("DEEPGRAM_API_KEY")),
        anthropic_key=bool(os.getenv("ANTHROPIC_API_KEY")),
        voice=VOICE, model=MODEL, name=ASSISTANT_NAME,
    )


@app.post("/api/reset")
def reset():
    history.clear()
    save_history()
    return jsonify(ok=True)


@app.post("/api/converse")
def converse():
    if not os.getenv("DEEPGRAM_API_KEY") or not os.getenv("ANTHROPIC_API_KEY"):
        return jsonify(error="Set DEEPGRAM_API_KEY and ANTHROPIC_API_KEY, then restart the server."), 400

    user_text = (request.form.get("text") or "").strip()
    try:
        if not user_text:
            f = request.files.get("audio")
            if not f:
                return jsonify(error="No audio or text provided."), 400
            user_text = transcribe(f.read(), f.mimetype)

        if not user_text:
            return jsonify(user_text="", reply_text="Sorry, I didn't catch that.", audio_base64=None)

        history.append({"role": "user", "content": user_text})
        if len(history) > HISTORY_TURNS:
            del history[:-HISTORY_TURNS]

        reply = ask_claude(history)
        history.append({"role": "assistant", "content": reply})
        save_history()

        audio_b64 = base64.b64encode(synthesize(reply)).decode("ascii")
        return jsonify(user_text=user_text, reply_text=reply, audio_base64=audio_b64)

    except requests.HTTPError as e:
        return jsonify(error=f"Upstream API error: {e}"), 502
    except Exception as e:
        return jsonify(error=str(e)), 500


# ──────────────────────────── Front-end ────────────────────────────
INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__ · voice agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root{
    --royal:#3D1B4F; --magenta:#C8378F; --deep:#2D1238;
    --ink:#EDE7F0; --muted:#9B8AA6;
  }
  *{box-sizing:border-box}
  body{
    margin:0; min-height:100vh; color:var(--ink);
    font-family:"JetBrains Mono",ui-monospace,monospace;
    background:radial-gradient(1200px 600px at 50% -10%, #43204f 0%, var(--deep) 55%, #160a1d 100%);
    display:flex; justify-content:center;
  }
  .app{width:100%; max-width:760px; padding:28px 20px 16px; display:flex; flex-direction:column; min-height:100vh}
  header{display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:18px}
  .brand{display:flex; align-items:baseline; gap:10px}
  .brand h1{font-family:"Bebas Neue",sans-serif; font-weight:400; font-size:42px; letter-spacing:2px; margin:0; line-height:1}
  .brand h1 .dot{color:var(--magenta)}
  .brand .sub{font-size:11px; color:var(--muted); letter-spacing:.5px}
  .pill{font-size:11px; padding:6px 12px; border-radius:999px; border:1px solid #5a3a68; color:var(--muted); white-space:nowrap}
  .pill.live{color:#fff; background:var(--magenta); border-color:var(--magenta); box-shadow:0 0 18px rgba(200,55,143,.5)}
  .pill.think{color:#fff; background:var(--royal); border-color:#6c3f80}
  .pill.err{color:#fff; background:#7a1f3d; border-color:#a8294f}
  .btn-ghost{background:transparent; border:1px solid #5a3a68; color:var(--muted); font-family:inherit; font-size:11px; padding:6px 12px; border-radius:8px; cursor:pointer}
  .btn-ghost:hover{color:var(--ink); border-color:var(--magenta)}
  #log{flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:10px; padding:6px 2px 16px}
  .bubble{max-width:80%; padding:11px 14px; border-radius:14px; font-size:13.5px; line-height:1.5; white-space:pre-wrap; word-wrap:break-word}
  .bubble.you{align-self:flex-end; background:var(--royal); border:1px solid #5a3a68; border-bottom-right-radius:4px}
  .bubble.claude{align-self:flex-start; background:rgba(200,55,143,.10); border:1px solid rgba(200,55,143,.35); border-bottom-left-radius:4px}
  .controls{display:flex; flex-direction:column; align-items:center; gap:14px; padding:10px 0 6px}
  #talk{
    width:108px; height:108px; border-radius:50%; border:none; cursor:pointer;
    background:radial-gradient(circle at 30% 25%, #e24fa6, var(--magenta) 55%, var(--royal));
    color:#fff; font-family:"Bebas Neue",sans-serif; letter-spacing:1px; font-size:17px;
    box-shadow:0 10px 30px rgba(200,55,143,.35); transition:transform .12s ease, box-shadow .12s ease;
    user-select:none; touch-action:none;
  }
  #talk:hover{transform:translateY(-1px)}
  #talk.rec{transform:scale(1.06); box-shadow:0 0 0 8px rgba(200,55,143,.18), 0 0 40px rgba(200,55,143,.6)}
  .hint{font-size:11px; color:var(--muted)}
  .textrow{display:flex; gap:8px; width:100%}
  #text{flex:1; background:#1f0f29; border:1px solid #5a3a68; color:var(--ink); font-family:inherit; font-size:13px; padding:10px 12px; border-radius:10px}
  #text:focus{outline:none; border-color:var(--magenta)}
  #sendText{background:var(--royal); border:1px solid #6c3f80; color:var(--ink); font-family:inherit; font-size:12px; padding:0 16px; border-radius:10px; cursor:pointer}
  #sendText:hover{background:#4d2563}
  footer{font-size:10px; color:var(--muted); text-align:center; padding-top:12px; letter-spacing:.4px; border-top:1px solid #3a2247; margin-top:8px}
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="brand">
      <h1>__NAME__<span class="dot">.</span></h1>
      <span class="sub">personal voice agent · localhost:4444</span>
    </div>
    <div style="display:flex; gap:8px; align-items:center">
      <span id="status" class="pill">Idle</span>
      <button id="reset" class="btn-ghost">Reset</button>
    </div>
  </header>

  <div id="log"></div>

  <div class="controls">
    <button id="talk">HOLD&nbsp;TO&nbsp;TALK</button>
    <div class="hint">Hold the button, speak, release — or type below</div>
    <div class="textrow">
      <input id="text" type="text" placeholder="Type a message to __NAME__…" autocomplete="off">
      <button id="sendText">Send</button>
    </div>
  </div>

  <footer>Voice: __VOICE__ · Brain: __MODEL__ · Personal — Confidential</footer>
</div>

<script>
const statusEl=document.getElementById('status');
const talkBtn=document.getElementById('talk');
const log=document.getElementById('log');
const textInput=document.getElementById('text');
let stream=null, recorder=null, chunks=[], busy=false;

function setStatus(s, cls){ statusEl.textContent=s; statusEl.className='pill '+(cls||''); }

function addBubble(role, text){
  const d=document.createElement('div');
  d.className='bubble '+role; d.textContent=text;
  log.appendChild(d); log.scrollTop=log.scrollHeight;
}

async function ensureMic(){
  if(stream) return stream;
  stream=await navigator.mediaDevices.getUserMedia({audio:true});
  return stream;
}

async function startRec(){
  if(busy) return;
  try{ await ensureMic(); }catch(e){ setStatus('Mic blocked','err'); return; }
  chunks=[];
  recorder=new MediaRecorder(stream);
  recorder.ondataavailable=e=>{ if(e.data.size>0) chunks.push(e.data); };
  recorder.onstop=handleStop;
  recorder.start();
  talkBtn.classList.add('rec');
  setStatus('Listening…','live');
}

function stopRec(){
  if(recorder && recorder.state!=='inactive') recorder.stop();
  talkBtn.classList.remove('rec');
}

async function handleStop(){
  const type=recorder.mimeType||'audio/webm';
  const blob=new Blob(chunks,{type});
  if(blob.size===0){ setStatus('Idle'); return; }
  const fd=new FormData();
  fd.append('audio', blob, 'speech.webm');
  await send(fd);
}

async function sendText(){
  const t=textInput.value.trim();
  if(!t || busy) return;
  textInput.value='';
  const fd=new FormData(); fd.append('text', t);
  await send(fd);
}

async function send(fd){
  busy=true; setStatus('Thinking…','think');
  try{
    const r=await fetch('/api/converse',{method:'POST', body:fd});
    const data=await r.json();
    if(data.error){ addBubble('claude','⚠️ '+data.error); setStatus('Idle'); busy=false; return; }
    if(data.user_text) addBubble('you', data.user_text);
    if(data.reply_text) addBubble('claude', data.reply_text);
    if(data.audio_base64){ setStatus('Speaking…','live'); await play(data.audio_base64); }
    setStatus('Idle');
  }catch(e){ addBubble('claude','⚠️ '+e.message); setStatus('Idle'); }
  busy=false;
}

function play(b64){
  return new Promise(res=>{
    const bin=atob(b64); const arr=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++) arr[i]=bin.charCodeAt(i);
    const a=new Audio(URL.createObjectURL(new Blob([arr],{type:'audio/wav'})));
    a.onended=res; a.onerror=res; a.play().catch(res);
  });
}

talkBtn.addEventListener('pointerdown', e=>{ e.preventDefault(); startRec(); });
talkBtn.addEventListener('pointerup',   e=>{ e.preventDefault(); stopRec(); });
talkBtn.addEventListener('pointerleave',()=>{ if(recorder && recorder.state==='recording') stopRec(); });
document.getElementById('sendText').addEventListener('click', sendText);
textInput.addEventListener('keydown', e=>{ if(e.key==='Enter') sendText(); });
document.getElementById('reset').addEventListener('click', async ()=>{
  await fetch('/api/reset',{method:'POST'}); log.innerHTML=''; setStatus('Idle');
});
setStatus('Idle');
</script>
</body>
</html>"""


if __name__ == "__main__":
    print(f"\n  {ASSISTANT_NAME} — {USER_NAME}'s voice agent  →  http://localhost:{PORT}\n")
    app.run(host="127.0.0.1", port=PORT, debug=True, use_reloader=False)
