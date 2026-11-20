"""Montaje (solo imagen) de una segunda hora -Barcelona- sobre la esfera.

NO forma parte del pipeline: no toca design/render.py, ni gen_watchface.py, ni el
proyecto de WFS. Dibuja la candidata encima de design/out/device-render.png con
la misma tipografia (Consolas Bold) y los mismos colores del diseno, para poder
juzgar la colocacion.

Uso:  python tools\\debug\\mock_world_clock.py
Salida: build/mock-bcn-<variante>.png y build/mock-bcn-comparativa.png
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(ROOT, "design", "out", "device-render.png")
OUT_DIR = os.path.join(ROOT, "build")

FONT_DIR = r"C:\Windows\Fonts"
CYAN = (34, 231, 255)
DIMM = (143, 182, 201)
VIOLET = (162, 75, 255)
MAGENTA = (255, 42, 109)

# Hora local del mock (10:43) + 6 h -> Barcelona. Es solo de muestra.
BCN = "16:43"


def mono(size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "consolab.ttf"), size)


def draw_tracked(d, xy, text, fnt, fill, anchor, spacing):
    """Texto monoespaciado con letter-spacing, como en design/render.py."""
    if spacing <= 0:
        d.text(xy, text, font=fnt, fill=fill, anchor=anchor)
        return
    total = sum(d.textlength(ch, font=fnt) + spacing for ch in text) - spacing
    x, y = xy
    if anchor == "rm":
        x -= total
    elif anchor == "mm":
        x -= total / 2
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="lm")
        x += d.textlength(ch, font=fnt) + spacing


def glow_layer(layer, radius=2.2):
    return layer.filter(ImageFilter.GaussianBlur(radius))


def paint(base, items):
    """items: (texto, tamano, color, (x, y), anchor, spacing)."""
    img = base.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for text, size, color, xy, anchor, spacing in items:
        draw_tracked(d, xy, text, mono(size), color + (255,), anchor, spacing)
    img = Image.alpha_composite(img, glow_layer(layer))
    img = Image.alpha_composite(img, layer)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# las candidatas (coordenadas a 480x480, las del diseno)
# ---------------------------------------------------------------------------
def variant_a(base):
    """Columna izquierda: tercera linea del bloque BAT / BPM, alineada con ellos."""
    return paint(base, [
        ("BCN", 13, DIMM, (52, 330), "lm", 1.2),
        (BCN, 28, CYAN, (52, 352), "lm", 1.4),
    ])


def variant_b(base):
    """Una linea centrada debajo de la fecha."""
    items = []
    f_lbl, f_val = mono(13), mono(24)
    w_lbl = sum(f_lbl.getlength(c) for c in "BCN")
    w_val = sum(f_val.getlength(c) for c in BCN)
    total = w_lbl + 10 + w_val
    x = 240 - total / 2
    items.append(("BCN", 13, DIMM, (x, 414), "lm", 0))
    items.append((BCN, 24, CYAN, (x + w_lbl + 10, 414), "lm", 1.2))
    return paint(base, items)


def variant_c(base):
    """Bloque de dos lineas flotando en el cuadrante inferior izquierdo."""
    return paint(base, [
        ("BCN", 13, DIMM, (112, 330), "lm", 1.2),
        (BCN, 26, CYAN, (112, 352), "lm", 1.2),
    ])


VARIANTS = [
    ("a-columna-izquierda", "A - columna izquierda, bajo BPM", variant_a),
    ("b-bajo-la-fecha", "B - una linea centrada bajo la fecha", variant_b),
    ("c-abajo-izquierda", "C - bloque flotante abajo izquierda", variant_c),
]


def contact_sheet(images):
    pad, cap = 12, 26
    w = sum(im.width for im in images) + pad * (len(images) + 1)
    h = images[0].height + cap + pad * 2
    sheet = Image.new("RGB", (w, h), (8, 10, 16))
    d = ImageDraw.Draw(sheet)
    fnt = mono(15)
    x = pad
    for im, (_slug, caption, _fn) in zip(images, VARIANTS):
        sheet.paste(im, (x, pad))
        d.text((x + im.width / 2, pad + im.height + cap / 2),
               caption, font=fnt, fill=(200, 220, 230), anchor="mm")
        x += im.width + pad
    return sheet


def main():
    base = Image.open(BASE)
    images = []
    for slug, caption, fn in VARIANTS:
        im = fn(base)
        path = os.path.join(OUT_DIR, "mock-bcn-%s.png" % slug)
        im.save(path)
        images.append(im)
        print("wrote", path)
    sheet = contact_sheet(images)
    path = os.path.join(OUT_DIR, "mock-bcn-comparativa.png")
    sheet.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
