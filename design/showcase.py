"""Composes the showcase image: interactive face + always-on (ambient) view."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
S = 480
PAD = 26
BG = (12, 15, 20)

face = Image.open(os.path.join(OUT, "preview_full.png")).convert("RGB")
amb = Image.open(os.path.join(OUT, "preview_ambient.png")).convert("RGB")

W = S * 2 + PAD * 3
H = S + PAD * 2 + 34
canvas = Image.new("RGB", (W, H), BG)
canvas.paste(face, (PAD, PAD))
canvas.paste(amb, (PAD * 2 + S, PAD))

d = ImageDraw.Draw(canvas)
try:
    f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
except OSError:
    f = ImageFont.load_default()
d.text((PAD, H - 26), "NEON GRID  /  MODO NORMAL", font=f, fill=(120, 160, 180))
d.text((PAD * 2 + S, H - 26), "MODO AMBIENTE (SIEMPRE ENCENDIDO)", font=f, fill=(120, 160, 180))

path = os.path.join(OUT, "showcase.png")
canvas.save(path, "PNG", optimize=True)
print("wrote", path, canvas.size)
