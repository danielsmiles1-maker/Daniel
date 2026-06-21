# PyInstaller spec for the Daniel Junior desktop app.
#
#   pip install -r requirements.txt -r requirements-desktop.txt
#   pyinstaller DanielJunior.spec --noconfirm
#       (or: python build_desktop.py)
#
# Produces a single, double-clickable executable in dist/.
# Build on the OS you want to target — PyInstaller does not cross-compile.

import sys
from PyInstaller.utils.hooks import collect_all

# Bundle the static assets (PWA icons) so Flask can serve them when frozen.
datas = [("static", "static")]
binaries = []
hiddenimports = []

# Pull in everything pywebview and the Anthropic SDK need (platform webview
# backends, data files, lazy imports PyInstaller can't see statically).
for pkg in ("webview", "anthropic", "dotenv"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# Platform-appropriate app icon (Windows needs .ico; mac/Linux fall back to png).
if sys.platform == "win32":
    app_icon = "static/icon.ico"
elif sys.platform == "darwin":
    app_icon = "static/icon-512.png"
else:
    app_icon = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DanielJunior",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed app — no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,   # set True on macOS if you need file-drop onto the app
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
