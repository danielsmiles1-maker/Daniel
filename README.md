# Ada — Daniel's personal voice AI agent

A hold-to-talk voice assistant that runs locally. Your browser captures the mic;
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
