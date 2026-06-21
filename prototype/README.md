# Claude — voice conversation prototype

A small, runnable seed for **Phase 0** of [`../PRD-Claude-Voice-Agent.md`](../PRD-Claude-Voice-Agent.md):
talk to Claude out loud and have her reply in a British accent, including a
free-flowing **"discuss a topic"** mode for debate and brainstorming.

It's deliberately minimal and dependency-light. Voice in/out and the LLM each sit
behind a clean class, so you can later swap in streaming STT, cloud British TTS,
and tool-use without rewriting the loop.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic                      # the brain
pip install SpeechRecognition pyttsx3      # optional: mic + offline speech
export ANTHROPIC_API_KEY=sk-ant-...

python claude_voice.py                      # typed chat
python claude_voice.py --voice              # speak + listen
python claude_voice.py --discuss "the ethics of AI agents"   # discussion mode
```

Everything degrades gracefully: no mic, no TTS, or no API key → it falls back to
typed console chat so the logic is always testable.

Say `stop`, `bye`, or press `Ctrl-C` to end.

## What it demonstrates (and what's next)

| In the prototype | Grows into (per PRD) |
|------------------|----------------------|
| `Listener` (Google STT / typed) | Streaming STT + wake word + barge-in (§5.1) |
| `Speaker` (pyttsx3 GB voice) | Cloud `en-GB` neural TTS, configurable accent (§6) |
| `Brain` (Claude, conversation memory) | Agent core with tool-use planner (§7) |
| `--discuss` mode | Full conversation mode with stances (§5.2) |
| Offline fallback | Local-only degradation path (§9 connectivity) |

The next build step is the **tool/integration layer** (calendar, email, Stripe,
filesystem, web) with the Tier 0/1/2 consent model from §8.
