#!/usr/bin/env python3
"""
Claude — voice-first conversation prototype.

A minimal, runnable seed for Phase 0 of the PRD: listen to the user, think with
an LLM, and speak back in a British accent. Includes a "discuss a topic" mode so
you can debate / brainstorm out loud.

This is intentionally small and dependency-light so you can run it today and grow
it into the full agent. Voice in/out and the LLM are behind clean interfaces, so
each piece is swappable (on-device vs cloud) as the product matures.

Quick start
-----------
    python3 -m venv .venv && source .venv/bin/activate
    pip install anthropic
    # Optional voice extras (graceful fallback to text if missing):
    pip install SpeechRecognition pyttsx3   # mic STT + offline TTS
    export ANTHROPIC_API_KEY=sk-ant-...
    python prototype/claude_voice.py            # text mode
    python prototype/claude_voice.py --voice    # speak + listen
    python prototype/claude_voice.py --discuss "the future of remote work"

Notes
-----
* If the optional voice libs or API key are absent, it degrades to typed chat so
  the conversation logic is always testable.
* British accent: pyttsx3 will try to pick an English (GB) system voice; for
  production-grade British TTS, swap `Speaker` for a cloud TTS (e.g. ElevenLabs /
  Azure 'en-GB' neural voices) behind the same interface.
"""

from __future__ import annotations

import argparse
import os
import sys

# Latest, most capable Claude model for the agent core. Swap as new models ship.
MODEL = "claude-opus-4-8"

BASE_PERSONA = (
    "You are Claude, a voice-first personal AI assistant with a warm, witty British "
    "personality (RP-leaning). You speak aloud, so keep replies concise and natural — "
    "short sentences, no markdown, no bullet lists, no emoji. Spell things out the way "
    "they should be spoken (say 'three p.m.', 'two hundred and forty pounds'). Be "
    "competent and direct; never sycophantic. If you're unsure, say so plainly."
)

DISCUSS_PERSONA = (
    "You are Claude, in 'discuss a topic' mode: an engaging, sharp British conversation "
    "partner. Hold a real spoken dialogue — share opinions, ask thoughtful questions, "
    "steelman opposing views, and build on what the user said earlier. Keep each turn to "
    "a few spoken sentences so it stays a back-and-forth, not a lecture. No markdown."
)


# --------------------------------------------------------------------------- #
# Voice I/O — both degrade gracefully to the keyboard/console.
# --------------------------------------------------------------------------- #
class Speaker:
    """Text-to-speech with a British accent, falling back to printing."""

    def __init__(self, enabled: bool):
        self.engine = None
        if not enabled:
            return
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 178)  # a touch slower = clearer
            self._select_british_voice()
        except Exception as exc:  # noqa: BLE001
            print(f"[voice output unavailable — falling back to text: {exc}]")

    def _select_british_voice(self) -> None:
        try:
            for v in self.engine.getProperty("voices"):
                blob = f"{v.id} {getattr(v, 'name', '')}".lower()
                if any(k in blob for k in ("en-gb", "english (great", "british", "daniel", "kate")):
                    self.engine.setProperty("voice", v.id)
                    return
        except Exception:  # noqa: BLE001
            pass  # keep default voice

    def say(self, text: str) -> None:
        print(f"\nClaude: {text}")
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()


class Listener:
    """Speech-to-text from the mic, falling back to typed input."""

    def __init__(self, enabled: bool):
        self.recognizer = None
        self.mic = None
        if not enabled:
            return
        try:
            import speech_recognition as sr

            self.recognizer = sr.Recognizer()
            self.mic = sr.Microphone()
        except Exception as exc:  # noqa: BLE001
            print(f"[voice input unavailable — type instead: {exc}]")

    def listen(self) -> str:
        if not self.recognizer:
            return input("\nYou: ").strip()
        import speech_recognition as sr

        with self.mic as source:
            print("\n[listening… speak now]")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = self.recognizer.listen(source, phrase_time_limit=20)
        try:
            text = self.recognizer.recognize_google(audio)  # swap for streaming STT later
            print(f"You: {text}")
            return text
        except sr.UnknownValueError:
            print("[didn't catch that]")
            return ""
        except Exception as exc:  # noqa: BLE001
            print(f"[STT error: {exc}] — type instead:")
            return input("You: ").strip()


# --------------------------------------------------------------------------- #
# The brain — Claude via the Anthropic SDK, with an offline echo fallback.
# --------------------------------------------------------------------------- #
class Brain:
    def __init__(self, system_prompt: str):
        self.system = system_prompt
        self.history: list[dict] = []
        self.client = None
        try:
            from anthropic import Anthropic

            if os.environ.get("ANTHROPIC_API_KEY"):
                self.client = Anthropic()
        except Exception:  # noqa: BLE001
            pass
        if not self.client:
            print("[no ANTHROPIC_API_KEY / sdk — running in offline demo mode]")

    def reply(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        if not self.client:
            answer = (
                "Right — I'd normally think this through properly, but I'm offline just now. "
                "Set ANTHROPIC_API_KEY and I'll give you a real answer."
            )
        else:
            msg = self.client.messages.create(
                model=MODEL,
                max_tokens=400,
                system=self.system,
                messages=self.history,
            )
            answer = "".join(b.text for b in msg.content if b.type == "text").strip()
        self.history.append({"role": "assistant", "content": answer})
        return answer


# --------------------------------------------------------------------------- #
# Conversation loop
# --------------------------------------------------------------------------- #
STOP_WORDS = {"stop", "quit", "exit", "goodbye", "that's all", "bye"}


def run(voice: bool, discuss_topic: str | None) -> None:
    system = DISCUSS_PERSONA if discuss_topic else BASE_PERSONA
    brain = Brain(system)
    speaker = Speaker(enabled=voice)
    listener = Listener(enabled=voice)

    if discuss_topic:
        opener = brain.reply(
            f"Let's discuss this topic together: {discuss_topic}. "
            "Open with a brief, engaging take and a question back to me."
        )
    else:
        opener = "Hello — Claude here. What can I do for you?"
    speaker.say(opener)

    while True:
        try:
            user_text = listener.listen()
        except (KeyboardInterrupt, EOFError):
            speaker.say("Right, I'll leave you to it. Cheerio.")
            break

        if not user_text:
            continue
        if user_text.strip().lower() in STOP_WORDS:
            speaker.say("Cheerio — talk soon.")
            break

        speaker.say(brain.reply(user_text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude — voice conversation prototype")
    parser.add_argument("--voice", action="store_true", help="enable mic + speech output")
    parser.add_argument(
        "--discuss",
        nargs="?",
        const="anything on your mind",
        metavar="TOPIC",
        help="start in 'discuss a topic' mode",
    )
    args = parser.parse_args(argv)
    run(voice=args.voice, discuss_topic=args.discuss)
    return 0


if __name__ == "__main__":
    sys.exit(main())
