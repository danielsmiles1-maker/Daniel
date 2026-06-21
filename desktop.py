#!/usr/bin/env python3
"""
Daniel Junior — desktop app launcher.

Runs the Flask server in a background thread and opens it in a native desktop
window (via pywebview), so the agent feels like a real installed app instead of
a browser tab.

Setup
-----
    pip install -r requirements.txt -r requirements-desktop.txt

    export DEEPGRAM_API_KEY="dg_..."
    export ANTHROPIC_API_KEY="sk-ant-..."
    # optional but recommended so your login persists between launches:
    export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
    export APP_PASSWORD="choose-a-password"

Run
---
    python desktop.py

You'll see the sign-in screen first (same credentials as the web app), then the
agent. Microphone access uses the OS webview's permissions — grant it when asked.
"""

import threading
import time

import webview   # pywebview

import server


def _serve():
    # use_reloader=False is required: the reloader spawns a second process,
    # which would fight the desktop window. threaded=True lets the mic upload
    # and the TTS response overlap.
    server.app.run(host="127.0.0.1", port=server.PORT,
                   debug=False, use_reloader=False, threaded=True)


def main():
    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    time.sleep(0.6)  # give Flask a moment to bind the port

    webview.create_window(
        title=f"{server.ASSISTANT_NAME} — {server.USER_NAME}'s voice agent",
        url=f"http://127.0.0.1:{server.PORT}/",
        width=820,
        height=900,
        min_size=(420, 600),
    )
    # http_server=False — we run our own Flask server above and just point at it.
    webview.start()


if __name__ == "__main__":
    main()
