# Claude — a voice-first personal AI agent

A voice-first agent that runs on your machine: you talk, it reasons with Claude,
researches the web, and (in staged, permission-gated phases) reads/edits your
files and reaches into your calendar, email, and Stripe. The design treats the
**trust boundary** — what leaves your machine, what the agent may *do* vs merely
*propose*, and an audit trail of everything — as the primary feature.

Pipeline: `mic → Deepgram Nova-3 (STT) → Claude (reasoning + web search + tools) → Deepgram Aura-2 (TTS) → speaker`

## What's here

| File | What it is |
|------|------------|
| [`Claude_Voice_Agent_PRD.md`](Claude_Voice_Agent_PRD.md) | The full product spec — goals, architecture, phased roadmap, action-authorization tiers, security model, and edge cases. **Start here.** |
| [`jarvis.py`](jarvis.py) | The flagship build: a local Flask web app with an agentic Claude tool-use loop (run shell, read/write files), three **autonomy tiers** (A0 advisory / A1 guarded / A2 free), hard-stop safety rails, MCP connectors, and a browser UI. → `http://localhost:4444` |
| [`claude_voice_agent.py`](claude_voice_agent.py) | A simpler CLI voice loop — listen, reason (with web search), speak. Good for a quick conversation/discussion without the web UI. |
| [`mcp-test/`](mcp-test/) | Prove the Anthropic MCP connector reaches a remote server **before** wrestling with Google OAuth. See [`mcp-test/CONNECTOR_TEST.md`](mcp-test/CONNECTOR_TEST.md). |

## Quick start

```bash
# Keys (both apps need these)
export DEEPGRAM_API_KEY="dg_..."      # https://console.deepgram.com
export ANTHROPIC_API_KEY="sk-ant-..." # https://console.anthropic.com

# Flagship web app (shell + file tools, autonomy dial, browser UI)
pip install flask anthropic requests
python jarvis.py                       # → http://localhost:4444

# Or the simple CLI voice loop
pip install anthropic SpeechRecognition pyaudio requests pygame
python claude_voice_agent.py           # say "goodbye" or Ctrl+C to stop
```

## Safety model in one breath

- **Autonomy tiers** (`jarvis.py`): A0 reads/researches only · A1 writes files & runs safe
  commands (destructive ones skipped) · A2 does everything except the `HARD_STOPS`.
- **Propose, then act:** anything irreversible or outbound is proposed in plain language and
  run only on explicit confirmation; reversible low-risk actions run directly.
- **Content is data, not commands:** text read from files/web/email can never instruct the
  agent — only your voice does.
- **Everything is logged**, and writes are backed up (`.bak`) before overwrite.

See the PRD's §9 (action authorization) and §10 (security, privacy & governance) for the
full discipline.

## Voice / accent

Voice is a single config constant. `jarvis.py` and `claude_voice_agent.py` default to the
Deepgram Aura-2 `theia` voice; swap `VOICE` to a British Aura voice
(e.g. `aura-athena-en` / `aura-helios-en`) for the British accent. Tracked as an open
decision in the PRD (§14, Q1).
