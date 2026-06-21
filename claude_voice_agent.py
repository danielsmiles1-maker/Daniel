#!/usr/bin/env python3
"""
Claude — a voice-first conversational agent.

Pipeline:  mic ──► Deepgram Nova-3 (STT) ──► Anthropic Claude (reasoning + web search)
                                              │
              speaker ◄── Deepgram Aura-2 "Theia" (TTS) ◄── reply text

What it does
------------
- Listens to you, transcribes with Deepgram Nova-3 (smart-formatted, good with
  numbers/currency/names).
- Sends the transcript to Claude, which can use live web search to answer
  current-information questions.
- Speaks the reply back in the Deepgram Aura-2 "theia" voice (the one you uploaded).
- Holds a real multi-turn conversation — you can discuss and argue a topic with it.

Setup
-----
    pip install anthropic SpeechRecognition pyaudio requests pygame

    # PyAudio needs PortAudio:
    #   macOS:   brew install portaudio  &&  pip install pyaudio
    #   Debian:  sudo apt-get install portaudio19-dev python3-pyaudio
    #   Windows: pip install pyaudio   (usually just works)

    export DEEPGRAM_API_KEY="dg_..."      # https://console.deepgram.com
    export ANTHROPIC_API_KEY="sk-ant-..." # https://console.anthropic.com

Run
---
    python claude_voice_agent.py

Say "goodbye" (or Ctrl+C) to stop.
"""

import os
import sys
import time
import tempfile

import requests
import speech_recognition as sr
import pygame
from anthropic import Anthropic

# ───────────────────────────── Config ──────────────────────────────
# Voice — this is the one knob to change the accent/persona.
# "aura-2-theia-en"  = American female (your uploaded sample).
# Want the British accent from the original brief instead? Swap to a British
# Aura voice, e.g.  "aura-athena-en" (British female) / "aura-helios-en" (British male).
VOICE = "aura-2-theia-en"

# Brain — fast model for snappy conversation. For deeper reasoning bump to
# "claude-opus-4-8"; for lowest latency try "claude-haiku-4-5-20251001".
MODEL = "claude-sonnet-4-6"

STT_MODEL = "nova-3"          # Deepgram speech-to-text
ENABLE_WEB_SEARCH = True      # let Claude pull live info from the web
MAX_TOKENS = 400              # keep spoken replies short
HISTORY_TURNS = 20            # rolling window so long chats don't blow the context

EXIT_PHRASES = {"goodbye", "goodbye claude", "stop listening", "that's all", "exit", "quit"}

SYSTEM_PROMPT = (
    "You are Claude, a voice-first personal assistant. You are being spoken aloud, so:\n"
    "- Keep replies to 2-4 sentences unless explicitly asked to go deeper. "
    "No bullet points, no markdown, no headings - this is speech.\n"
    "- Be warm, direct, and quick-witted. Dry humour is welcome. Skip filler "
    "like 'great question' and excessive caveats.\n"
    "- You can discuss and debate: take a position, give your reasons, and push "
    "back when the user is wrong rather than just agreeing.\n"
    "- If a request is genuinely ambiguous, ask one short clarifying question "
    "instead of guessing.\n"
    "- When you use web results, give the bottom line first, then one sentence "
    "on why it matters. Don't read out long URLs."
)

DG_KEY = os.getenv("DEEPGRAM_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

TMP = tempfile.gettempdir()


# ──────────────────────────── Deepgram STT ─────────────────────────
def transcribe(wav_bytes: bytes) -> str:
    """Send recorded WAV audio to Deepgram Nova-3, return the transcript text."""
    resp = requests.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": STT_MODEL, "smart_format": "true", "punctuate": "true"},
        headers={"Authorization": f"Token {DG_KEY}", "Content-Type": "audio/wav"},
        data=wav_bytes,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()


# ──────────────────────────── Deepgram TTS ─────────────────────────
def synthesize(text: str) -> bytes:
    """Convert text to speech with Deepgram Aura-2 (Theia). Returns WAV bytes."""
    resp = requests.post(
        "https://api.deepgram.com/v1/speak",
        params={"model": VOICE},  # REST default output: linear16 / wav / 24 kHz
        headers={"Authorization": f"Token {DG_KEY}", "Content-Type": "application/json"},
        json={"text": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content


def speak(text: str) -> None:
    """Synthesize and play audio, blocking until playback finishes."""
    try:
        audio = synthesize(text)
    except Exception as e:
        print(f"  [TTS error: {e}]")
        return
    path = os.path.join(TMP, "claude_tts.wav")
    with open(path, "wb") as f:
        f.write(audio)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"  [playback error: {e}]")


# ──────────────────────────── Claude brain ─────────────────────────
def ask_claude(client: Anthropic, messages: list) -> str:
    """Get Claude's reply, optionally using live web search."""
    kwargs = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    if ENABLE_WEB_SEARCH:
        # Server-side web search: Deepgram-style single round trip, Claude runs the
        # search and returns final text. If your account/SDK doesn't support this,
        # set ENABLE_WEB_SEARCH = False above.
        kwargs["tools"] = [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 3,
        }]
    resp = client.messages.create(**kwargs)
    parts = [
        block.text.strip()
        for block in resp.content
        if getattr(block, "type", None) == "text" and block.text.strip()
    ]
    return " ".join(parts) or "I'm not sure how to answer that one."


# ────────────────────────────── Main loop ──────────────────────────
def main() -> None:
    if not DG_KEY:
        sys.exit("Set DEEPGRAM_API_KEY first (https://console.deepgram.com).")
    if not ANTHROPIC_KEY:
        sys.exit("Set ANTHROPIC_API_KEY first (https://console.anthropic.com).")

    client = Anthropic()
    pygame.mixer.init()

    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("Calibrating for background noise… (stay quiet for a second)")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    messages: list = []
    greeting = "Hi, Claude here. What would you like to get into?"
    print(f"\nClaude: {greeting}")
    speak(greeting)

    while True:
        # 1) Listen
        with mic as source:
            print("\n🎙️  Listening…  (say 'goodbye' to stop)")
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=25)
            except sr.WaitTimeoutError:
                continue  # nothing said — just keep listening

        # 2) Transcribe (Deepgram Nova-3)
        try:
            user_text = transcribe(audio.get_wav_data())
        except Exception as e:
            print(f"  [STT error: {e}]")
            continue

        if not user_text:
            print("  (didn't catch that)")
            speak("Sorry, I didn't catch that.")
            continue

        print(f"You:    {user_text}")

        # 3) Exit?
        if user_text.lower().strip(" .!?") in EXIT_PHRASES:
            speak("Right, talk soon.")
            break

        # 4) Think (Claude, with web search)
        messages.append({"role": "user", "content": user_text})
        if len(messages) > HISTORY_TURNS:
            messages[:] = messages[-HISTORY_TURNS:]
        try:
            reply = ask_claude(client, messages)
        except Exception as e:
            print(f"  [brain error: {e}]")
            messages.pop()  # don't keep the unanswered turn
            speak("I hit a snag reaching my brain. Want to try that again?")
            continue

        # 5) Speak
        messages.append({"role": "assistant", "content": reply})
        print(f"Claude: {reply}")
        speak(reply)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        try:
            pygame.mixer.quit()
        except Exception:
            pass
