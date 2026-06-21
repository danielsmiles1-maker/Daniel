#!/usr/bin/env python3
"""
Generate the PWA app icons for Daniel Junior into static/.

    pip install pillow
    python generate_icons.py

Produces a "DJ" monogram on the app's royal/magenta palette in the sizes a
Progressive Web App needs (192, 512, a maskable 512, and a 180px Apple touch icon).
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROYAL = (61, 27, 79)
DEEP = (45, 18, 56)
MAGENTA = (200, 55, 143)
INK = (237, 231, 240)


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make(size, path, maskable=False):
    img = Image.new("RGB", (size, size), DEEP)
    d = ImageDraw.Draw(img)
    # vertical gradient: deep -> royal
    for y in range(size):
        t = y / size
        d.line([(0, y), (size, y)],
               fill=tuple(int(DEEP[i] + (ROYAL[i] - DEEP[i]) * t) for i in range(3)))
    # maskable icons need extra safe-zone padding (smaller circle)
    pad = int(size * 0.10) if maskable else int(size * 0.16)
    r = (size - 2 * pad) // 2
    cx = cy = size // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MAGENTA)
    f = _font(int(r * 1.05))
    bb = d.textbbox((0, 0), "DJ", font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((cx - tw / 2 - bb[0], cy - th / 2 - bb[1]), "DJ", font=f, fill=INK)
    img.save(path)
    print("wrote", path)


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    make(192, "static/icon-192.png")
    make(512, "static/icon-512.png")
    make(512, "static/icon-maskable-512.png", maskable=True)
    make(180, "static/apple-touch-icon.png")
