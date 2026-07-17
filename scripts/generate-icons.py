#!/usr/bin/env python3
"""Generate favicon / PWA icon set from public/logo.png"""
from PIL import Image
from collections import Counter
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "public")
SRC = os.path.join(ROOT, "logo.png")

src = Image.open(SRC).convert("RGBA")

# Trim transparent border, then pad back to square
bbox = src.getbbox()
logo = src.crop(bbox)
side = max(logo.size)
square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
square.paste(logo, ((side - logo.width) // 2, (side - logo.height) // 2), logo)

# Sample dominant opaque color (for reporting theme color)
small = square.resize((64, 64), Image.LANCZOS)
px = [p[:3] for p in small.getdata() if p[3] > 200]
print("dominant colors:", Counter(px).most_common(5))


def resized(size):
    return square.resize((size, size), Image.LANCZOS)


def on_bg(size, scale, bg=(255, 255, 255, 255)):
    canvas = Image.new("RGBA", (size, size), bg)
    inner = int(size * scale)
    icon = square.resize((inner, inner), Image.LANCZOS)
    off = (size - inner) // 2
    canvas.paste(icon, (off, off), icon)
    return canvas


out = lambda name: os.path.join(ROOT, name)
os.makedirs(out("icons"), exist_ok=True)

# Plain favicons (transparent bg)
resized(16).save(out("icons/favicon-16x16.png"))
resized(32).save(out("icons/favicon-32x32.png"))
resized(48).save(out("icons/favicon-48x48.png"))
resized(96).save(out("icons/favicon-96x96.png"))

# Multi-size .ico
resized(48).save(out("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

# Apple touch icon: opaque white bg, ~82% logo
on_bg(180, 0.82).convert("RGB").save(out("icons/apple-touch-icon.png"))

# PWA icons, purpose "any" (transparent)
resized(192).save(out("icons/icon-192x192.png"))
resized(384).save(out("icons/icon-384x384.png"))
resized(512).save(out("icons/icon-512x512.png"))

# PWA maskable icons: white bg, logo inside 62% safe zone
on_bg(192, 0.62).convert("RGB").save(out("icons/icon-maskable-192x192.png"))
on_bg(512, 0.62).convert("RGB").save(out("icons/icon-maskable-512x512.png"))

# Windows tile
on_bg(270, 0.62).convert("RGB").save(out("icons/mstile-150x150.png"))

# Header / footer display versions (2x retina)
resized(96).save(out("images/logo-header.png"))   # displayed ~48px
resized(360).save(out("images/logo-footer.png"))  # displayed ~180px

print("done")
