# Daniel Junior — Daniel's personal voice AI agent

A hold-to-talk voice assistant that runs locally and installs as an app. Your
browser captures the mic;
a small Flask server proxies the whole pipeline so your API keys **never touch the
browser**:

```
browser mic ──► /api/converse ──► Deepgram Nova-3 (speech → text)
                                   └─► Claude (reasoning + live web search)
browser plays ◄── WAV audio ◄──── Deepgram Aura-2 "Theia" (text → speech)
```

- **Brain:** Claude (`claude-opus-4-8` by default — set `MODEL=claude-sonnet-4-6`
  for faster, lower-cost replies, or `claude-haiku-4-5` for fastest).
- **Voice in:** Deepgram Nova-3 STT.
- **Voice out:** Deepgram Aura-2 "Theia" TTS.
- **Live info:** Claude's built-in web search tool (`web_search_20260209`).
- **Memory:** last 20 turns, **persisted to `history.json`** so it survives restarts.
  Resettable from the UI.

## Setup

```bash
pip install -r requirements.txt

cp .env.example .env        # then fill in your keys
export DEEPGRAM_API_KEY="dg_..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Get keys from [console.deepgram.com](https://console.deepgram.com) and
[console.anthropic.com](https://console.anthropic.com).

## Run

```bash
python server.py
```

Open <http://localhost:4444>, **hold** the button to talk and release to send — or
type in the box. Mic capture needs `localhost` (or HTTPS), which this dev server
provides.

## Install it as an app

Daniel Junior is a **PWA (Progressive Web App)**, so you can install it and launch
it full-screen like a native app — no browser tabs, its own icon.

- **Desktop (Chrome/Edge):** click **Install** in the header, or the install icon
  in the address bar.
- **Android (Chrome):** menu → *Add to Home screen* / *Install app*.
- **iOS (Safari):** Share → *Add to Home Screen*.

It also caches its shell so it opens instantly and survives a flaky connection
(the voice/chat itself still needs the network and your API keys).

> To use it as an app on your **phone**, the page must be served over HTTPS (or
> `localhost`). Easiest path: run the server on your machine and expose it with a
> tunnel like `cloudflared tunnel --url http://localhost:4444` or `ngrok http 4444`,
> then open the HTTPS URL on your phone and install from there.

### Regenerating the app icons

The icons in `static/` are committed, so you don't need anything extra to run the
app. To change them, edit and run the generator (needs Pillow):

```bash
pip install pillow
python generate_icons.py
```

## Personalise

Tune behaviour via environment variables (or edit the config block at the top of
`server.py`):

| Variable          | Default            | What it does                          |
| ----------------- | ------------------ | ------------------------------------- |
| `AGENT_NAME`      | `Ada`              | What the agent calls itself / UI title |
| `USER_NAME`       | `Daniel`           | Who it's talking to                   |
| `PORT`            | `4444`             | Server port                           |
| `MODEL`           | `claude-opus-4-8`  | Reasoning model                       |
| `HISTORY_FILE`    | `history.json`     | Where conversation memory is stored   |
| `VOICE` (in code) | `aura-2-theia-en`  | TTS voice                             |

The persona, reply length, and tone live in `SYSTEM_PROMPT` in `server.py` — edit
it to make the agent yours.

## Notes

- This is a **local dev server** (single session, `debug=True`, bound to
  `127.0.0.1`). Don't expose it to the internet as-is.
- `.env` is gitignored — keep your real keys out of version control.
