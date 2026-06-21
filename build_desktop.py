#!/usr/bin/env python3
"""
Build the Daniel Junior desktop app into a standalone executable.

    pip install -r requirements.txt -r requirements-desktop.txt
    python build_desktop.py

The result lands in dist/ (DanielJunior, DanielJunior.exe, or DanielJunior.app).
Build on the OS you want to ship to — PyInstaller does not cross-compile.

Ship the executable together with a `.env` file (see .env.example) placed next to
it: the packaged app reads keys, password, and SECRET_KEY from there, since a
double-launched app has no shell environment.
"""

import sys

try:
    import PyInstaller.__main__ as pyi
except ImportError:
    sys.exit("PyInstaller is not installed. Run:\n"
             "    pip install -r requirements-desktop.txt")

if __name__ == "__main__":
    pyi.run(["DanielJunior.spec", "--noconfirm", "--clean"])
