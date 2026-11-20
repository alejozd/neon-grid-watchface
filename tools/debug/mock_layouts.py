"""Bocetos de distribucion alternativa de la esfera (solo imagen).

NO toca el diseno ni el proyecto: reutiliza las primitivas de design/render.py
(fondo, manecillas, arcos, tipografia Consolas Bold y paleta) para dibujar otras
formas de repartir la misma informacion.

    python tools\\debug\\mock_layouts.py
Salida: build/mock-layout-v1..v3.png y build/mock-layouts.png
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "design"))
import render as g  # noqa: E402

OUT = os.path.join(ROOT, "build")

DATE = "VIE 20 NOV"
TIME, SECS, AMPM = "9:54", "12", "A.M."
TEMP, COND, MINMAX = "18°", "NUBLADO", "20° / 11°"
BAT, BPM, STEPS, STEPPCT, MSG, BCN = "23%", "76", "266", "4%", "1", "15:54"
EVENT, EVENT_TXT = "12:00 p.m.", "Daily sync"


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------
def dial(hh=9, mm=54, ss=12):
    """Fondo + las tres agujas nuevas, con el pivote en el centro del lienzo."""
    bg = g.make_bg()
    hour = g.make_hand(112, 8.2, g.CYAN, tail=7, shape="blade")
    minute = g.make_hand(162, 5.4, g.CYAN, tail=8, shape="blade")
    second = g.make_hand(178, 1.9, g.MAGENTA, tail=24, shape="needle")
    img = bg.copy()
    img = Image.alpha_composite(img, hour.rotate(-(hh % 12 * 30 + mm * 0.5),
                                                 resample=Image.BICUBIC, center=(g.CX, g.CY)))
    img = Image.alpha_composite(img, minute.rotate(-(mm * 6 + ss * 0.1),
                                                   resample=Image.BICUBIC, center=(g.CX, g.CY)))
    img = Image.alpha_composite(img, second.rotate(-(ss * 6),
                                                   resample=Image.BICUBIC, center=(g.CX, g.CY)))
    return Image.alpha_composite(img, g.make_hub())


def box(b):
    """Caja en espacio 480 -> pixeles del lienzo interno (K=4)."""
    return [v * g.K for v in b]


def panel(img, b, radius=18, fill=(6, 12, 20, 205), outline=None):
    lay = g.new_layer()
    ImageDraw.Draw(lay).rounded_rectangle(
        box(b), radius=radius * g.K, fill=fill,
        outline=outline or g.CYAN_DIM + (120,), width=2 * g.K)
    return Image.alpha_composite(img, lay)


def draw(img, painter):
    lay = g.new_layer()
    painter(ImageDraw.Draw(lay))
    return Image.alpha_composite(Image.alpha_composite(img, g.glow(lay, 3, 1.2)), lay)


def t(d, xy, s, size, color, anchor="mm", ls=0.0):
    g.text_c(d, (xy[0] * g.K, xy[1] * g.K), s, g.mono(int(size * g.K), True), color,
             anchor=anchor, spacing_=ls * g.K)


def label(d, xy, s, color=None, ls=0.9, anchor="mm"):
    t(d, xy, s, 11, color or g.TEXT_DIM, ls=ls, anchor=anchor)


# ---------------------------------------------------------------------------
# V1: capsula con la hora abajo, datos en dos columnas simetricas
# ---------------------------------------------------------------------------
def v1():
    img = dial()
    img = Image.alpha_composite(img, g.arc_gauge(205, 246, 294, 0.23, g.CYAN, g.MAGENTA))
    img = Image.alpha_composite(img, g.arc_gauge(205, 300, 340, 0.04, g.MAGENTA, g.Violet))
    img = panel(img, (96, 362, 384, 406), radius=22)

    def paint(d):
        t(d, (240, 74), TEMP, 34, g.CYAN)
        t(d, (240, 108), COND, 15, g.TEXT_DIM, ls=0.3)
        t(d, (240, 130), MINMAX, 14, g.TEXT_DIM, ls=0.3)

        label(d, (86, 168), "MSG")
        t(d, (86, 192), MSG, 26, g.MAGENTA)
        label(d, (86, 240), "BPM")
        t(d, (86, 264), BPM, 26, g.MAGENTA)
        label(d, (86, 312), "BAT")
        t(d, (86, 336), BAT, 26, g.CYAN)

        label(d, (394, 168), "EVENTO")
        t(d, (394, 192), EVENT, 17, g.Violet)
        label(d, (394, 240), "PASOS")
        t(d, (394, 262), STEPS, 24, g.CYAN)
        t(d, (394, 282), STEPPCT, 13, g.TEXT_DIM)
        label(d, (394, 312), "MUNDO")
        t(d, (394, 336), BCN, 22, g.CYAN)

        t(d, (232, 384), TIME, 38, g.CYAN, anchor="rm", ls=1.2)
        t(d, (338, 372), SECS, 17, g.CYAN, anchor="lm")
        t(d, (338, 392), AMPM, 12, g.CYAN, anchor="lm")
        t(d, (240, 430), DATE, 17, g.MAGENTA, ls=1.0)
    return draw(img, paint)


# ---------------------------------------------------------------------------
# V2: dos anillos completos, insignias en las diagonales y hora dentro
# ---------------------------------------------------------------------------
def v2():
    img = dial()
    img = Image.alpha_composite(img, g.arc_gauge(212, 150, 390, 0.23, g.CYAN, g.CYAN, bg_a=30))
    img = Image.alpha_composite(img, g.arc_gauge(196, 150, 390, 0.04, g.MAGENTA, g.MAGENTA, bg_a=30))
    # el cristal va ANTES del texto, si no lo tapa
    img = panel(img, (176, 268, 330, 318), radius=24, fill=(4, 9, 16, 175),
                outline=g.CYAN_DIM + (90,))

    def paint(d):
        t(d, (240, 58), TEMP, 30, g.CYAN)
        t(d, (240, 80), COND, 13, g.TEXT_DIM, ls=0.3)
        t(d, (240, 430), DATE, 16, g.MAGENTA, ls=1.0)
        label(d, (240, 406), "MUNDO  " + BCN, g.CYAN, ls=0.6)

        label(d, (120, 140), "MSG")
        t(d, (120, 164), MSG, 24, g.MAGENTA)
        label(d, (120, 216), "BPM")
        t(d, (120, 240), BPM, 24, g.MAGENTA)
        label(d, (120, 308), "BAT")
        t(d, (120, 332), BAT, 24, g.CYAN)

        label(d, (360, 140), "EVENTO")
        t(d, (360, 164), EVENT, 15, g.Violet)
        label(d, (360, 216), "PASOS")
        t(d, (360, 240), STEPS, 22, g.CYAN)
        t(d, (360, 260), STEPPCT, 12, g.TEXT_DIM)
        label(d, (360, 348), "MAX/MIN")
        t(d, (360, 366), MINMAX, 13, g.TEXT_DIM)

        t(d, (244, 292), TIME, 42, g.CYAN, ls=1.4)
        t(d, (312, 280), SECS, 15, g.CYAN, anchor="lm")
        t(d, (312, 298), AMPM, 11, g.CYAN, anchor="lm")
    return draw(img, paint)


# ---------------------------------------------------------------------------
# V3: rail lateral tipo terminal, dial limpio a la izquierda
# ---------------------------------------------------------------------------
def v3():
    img = dial()
    img = Image.alpha_composite(img, g.arc_gauge(205, 246, 294, 0.23, g.CYAN, g.MAGENTA))
    img = panel(img, (300, 92, 470, 400), radius=18)

    rows = [
        ("MSG", MSG, g.MAGENTA),
        ("BAT", BAT, g.CYAN),
        ("BPM", BPM, g.MAGENTA),
        ("STP", STEPS, g.CYAN),
        ("PCT", STEPPCT, g.TEXT_DIM),
        ("BCN", BCN, g.CYAN),
        ("EVT", EVENT, g.Violet),
    ]

    def paint(d):
        t(d, (170, 108), TEMP, 30, g.CYAN)
        t(d, (170, 132), COND, 13, g.TEXT_DIM, ls=0.3)
        t(d, (170, 300), TIME, 54, g.CYAN, ls=1.6)
        t(d, (170, 350), DATE, 17, g.MAGENTA, ls=1.1)

        y = 118
        for key, value, color in rows:
            label(d, (310, y), key, anchor="lm")
            t(d, (352, y + 1), value, 12, color, anchor="lm", ls=0.4)
            y += 26
        label(d, (310, y + 8), "EVENTO", anchor="lm")
        t(d, (310, y + 28), EVENT_TXT, 12, g.Violet, anchor="lm", ls=0.4)
        t(d, (310, y + 50), MINMAX, 11, g.TEXT_DIM, anchor="lm", ls=0.3)
    return draw(img, paint)


def main():
    variants = [("v1-capsula", v1), ("v2-anillos", v2), ("v3-rail", v3)]
    made = []
    for slug, fn in variants:
        im = fn().convert("RGB").resize((480, 480), Image.LANCZOS)
        path = os.path.join(OUT, "mock-layout-%s.png" % slug)
        im.save(path)
        made.append((slug, im))
        print("wrote", path)

    pad, cap = 12, 26
    w = sum(im.width for _s, im in made) + pad * (len(made) + 1)
    h = made[0][1].height + cap + pad * 2
    sheet = Image.new("RGB", (w, h), (8, 10, 16))
    d = ImageDraw.Draw(sheet)
    f = g.mono(14, True)
    x = pad
    for slug, im in made:
        sheet.paste(im, (x, pad))
        d.text((x + im.width / 2, pad + im.height + cap / 2), slug,
               font=f, fill=(200, 220, 230), anchor="mm")
        x += im.width + pad
    path = os.path.join(OUT, "mock-layouts.png")
    sheet.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
