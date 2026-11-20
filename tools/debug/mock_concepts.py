"""Bocetos de conceptos NUEVOS para la esfera (solo imagen).

No toca el diseno ni el proyecto. Reutiliza las primitivas de design/render.py
para que el resultado hable el mismo idioma visual (paleta neon, Consolas Bold,
bloom), pero cambia la composicion y sube mucho el tamano de la tipografia.

    python tools\\debug\\mock_concepts.py
Salida: build/mock-concept-a..c.png y build/mock-concepts.png
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw  # noqa: E402

import mock_layouts as ml  # noqa: E402  (dial, draw, t, label, box, panel)
import render as g  # noqa: E402

OUT = os.path.join(ml.ROOT, "build")

DATE = "VIE 20 NOV"
TIME, SECS, AMPM = "9:54", "12", "A.M."
TEMP, COND, MINMAX = "18°", "NUBLADO", "20° / 11°"
BAT, BPM, STEPS, STEPPCT, MSG, BCN = "23%", "76", "266", "4%", "1", "15:54"
EVENT, EVENT_TXT = "12:00 P.M.", "Daily sync"

INK = (5, 9, 16)


# ---------------------------------------------------------------------------
# formas: nada de esquinas redondeadas, cortes en diagonal (look de juego)
# ---------------------------------------------------------------------------
def cut_rect(img, b, cut=16, fill=(8, 14, 24, 225), outline=None, width=2):
    x0, y0, x1, y1 = b
    c = cut
    pts480 = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
              (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    pts = [(px * g.K, py * g.K) for px, py in pts480]
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline or g.CYAN_DIM + (170,), width=width * g.K)
    return Image.alpha_composite(img, lay)


def chip(img, b, outline=None, fill=(10, 17, 28, 220)):
    return cut_rect(img, b, cut=10, fill=fill, outline=outline, width=2)


def seg_bar(img, b, frac, color, segs=12, gap=3, off=(30, 40, 55, 230)):
    """Barra segmentada tipo medidor de juego."""
    x0, y0, x1, y1 = b
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    w = (x1 - x0 - gap * (segs - 1)) / segs
    on = int(round(segs * max(0.0, min(1.0, frac))))
    for i in range(segs):
        sx0 = x0 + i * (w + gap)
        col = color if i < on else off
        d.rectangle([sx0 * g.K, y0 * g.K, (sx0 + w) * g.K, y1 * g.K], fill=col)
    return Image.alpha_composite(img, lay)


def hex_badge(img, cx, cy, r, color):
    import math
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        pts.append(((cx + r * math.cos(a)) * g.K, (cy + r * math.sin(a)) * g.K))
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    d.polygon(pts, fill=(9, 15, 25, 235))
    d.line(pts + [pts[0]], fill=color + (220,), width=2 * g.K)
    return Image.alpha_composite(img, lay)


# ---------------------------------------------------------------------------
# A: consola radar (mantiene agujas, datos enormes en los bordes)
# ---------------------------------------------------------------------------
def concept_a():
    img = ml.dial()
    img = Image.alpha_composite(img, g.arc_gauge(206, 246, 294, 0.23, g.CYAN, g.MAGENTA))
    img = Image.alpha_composite(img, g.arc_gauge(206, 300, 340, 0.04, g.MAGENTA, g.Violet))

    def paint(d):
        # clima grande arriba
        ml.t(d, (240, 54), TEMP, 44, g.CYAN, ls=1.0)
        ml.t(d, (240, 90), COND, 18, g.TEXT_DIM, ls=1.2)
        ml.t(d, (240, 112), MINMAX, 16, g.TEXT_DIM, ls=0.8)

        # insignia MSG arriba izquierda
        ml.label(d, (58, 174), "MSG", ls=1.6)
        # evento arriba derecha
        ml.label(d, (428, 128), "EVENTO", ls=1.4, anchor="rm")
        ml.t(d, (428, 152), EVENT, 20, g.Violet, anchor="rm", ls=0.8)
        ml.t(d, (428, 176), EVENT_TXT, 16, g.TEXT_DIM, anchor="rm", ls=0.6)

        # bateria y pasos pegados a los arcos
        ml.label(d, (86, 244), "BAT", ls=1.6)
        ml.t(d, (86, 272), BAT, 40, g.CYAN, ls=1.2)
        ml.label(d, (404, 244), "PASOS", ls=1.6)
        ml.t(d, (404, 272), STEPS, 40, g.CYAN, ls=1.2)
        ml.t(d, (404, 298), STEPPCT + " META", 16, g.TEXT_DIM, ls=0.8)

        # pulso abajo izquierda, con traza
        ml.label(d, (86, 330), "BPM", ls=1.6)
        ml.t(d, (86, 358), BPM, 40, g.MAGENTA, ls=1.0)
        hx, hy = 86, 388
        ecg = [(hx - 46, hy), (hx - 30, hy), (hx - 22, hy - 12), (hx - 14, hy + 12),
               (hx - 6, hy - 4), (hx + 2, hy), (hx + 46, hy)]
        d.line([(x * g.K, y * g.K) for x, y in ecg], fill=g.MAGENTA + (210,), width=2 * g.K)

        # hora: la protagonista, a la derecha
        ml.t(d, (330, 344), TIME, 60, g.CYAN, anchor="rm", ls=1.6)
        ml.t(d, (356, 316), SECS, 24, g.CYAN, anchor="lm")
        ml.t(d, (356, 344), AMPM, 16, g.CYAN, anchor="lm")

        # fila inferior
        ml.t(d, (206, 418), DATE, 20, g.MAGENTA, ls=1.4)
        ml.label(d, (420, 400), "BCN", g.CYAN, ls=1.4, anchor="rm")
        ml.t(d, (420, 424), BCN, 28, g.CYAN, anchor="rm", ls=1.0)
    img = ml.draw(img, paint)
    img = hex_badge(img, 58, 142, 26, g.MAGENTA)
    return ml.draw(img, lambda d: ml.t(d, (58, 142), MSG, 30, g.MAGENTA))


# ---------------------------------------------------------------------------
# B: tarjetas (digital, tipo app; sin agujas)
# ---------------------------------------------------------------------------
def concept_b():
    bg = g.make_bg()
    img = bg.copy()
    img = cut_rect(img, (70, 62, 410, 196), cut=22, fill=(7, 13, 22, 225),
                   outline=g.CYAN + (150,), width=2)
    img = cut_rect(img, (70, 204, 232, 300), cut=16, fill=(7, 13, 22, 215))
    img = cut_rect(img, (240, 204, 410, 300), cut=16, fill=(7, 13, 22, 215))
    for x0 in (70, 186, 302):
        img = cut_rect(img, (x0, 308, x0 + 108, 392), cut=14, fill=(7, 13, 22, 215))
    img = cut_rect(img, (70, 400, 410, 452), cut=14, fill=(9, 15, 26, 225),
                   outline=g.CYAN + (120,), width=2)
    img = hex_badge(img, 384, 92, 26, g.MAGENTA)

    def paint(d):
        # tarjeta de la hora
        ml.t(d, (176, 118), TIME, 68, g.CYAN, ls=1.6)
        ml.t(d, (286, 98), SECS, 22, g.CYAN, anchor="lm")
        ml.t(d, (286, 124), AMPM, 15, g.CYAN, anchor="lm")
        ml.t(d, (110, 172), DATE, 21, g.MAGENTA, anchor="lm", ls=1.2)
        ml.t(d, (384, 92), MSG, 30, g.MAGENTA)
        ml.label(d, (384, 122), "MSG", ls=1.2)

        # clima
        ml.label(d, (92, 224), "AHORA", ls=1.4, anchor="lm")
        ml.t(d, (92, 254), TEMP, 42, g.CYAN, anchor="lm", ls=1.0)
        ml.t(d, (92, 284), COND, 15, g.TEXT_DIM, anchor="lm", ls=0.6)

        # evento
        ml.label(d, (262, 224), "EVENTO", ls=1.4, anchor="lm")
        ml.t(d, (262, 250), EVENT, 19, g.Violet, anchor="lm", ls=0.6)
        ml.t(d, (262, 276), EVENT_TXT, 15, g.TEXT_DIM, anchor="lm", ls=0.4)

        # tres metricas
        for x, name, value, color in ((124, "BAT", BAT, g.CYAN),
                                      (240, "BPM", BPM, g.MAGENTA),
                                      (356, "PASOS", STEPS, g.CYAN)):
            ml.label(d, (x, 328), name, ls=1.4)
            ml.t(d, (x, 360), value, 32, color, ls=0.8)

        # hora mundial
        ml.label(d, (92, 416), "MUNDO", g.CYAN, ls=1.6, anchor="lm")
        ml.t(d, (160, 416), "BCN", 17, g.TEXT_DIM, anchor="lm", ls=0.8)
        ml.t(d, (398, 416), BCN, 30, g.CYAN, anchor="rm", ls=1.0)
        ml.t(d, (398, 440), MINMAX, 14, g.TEXT_DIM, anchor="rm", ls=0.4)
    return ml.draw(img, paint)


# ---------------------------------------------------------------------------
# C: arcade (marcador grande, barras segmentadas, fichas)
# ---------------------------------------------------------------------------
def concept_c():
    bg = g.make_bg()
    img = bg.copy()

    def paint(d):
        ml.t(d, (214, 96), TIME, 96, g.CYAN, ls=2.2)
        ml.t(d, (330, 62), SECS, 28, g.CYAN, anchor="lm")
        ml.t(d, (330, 96), AMPM, 18, g.CYAN, anchor="lm")
        ml.t(d, (240, 160), DATE, 22, g.MAGENTA, ls=2.0)

        ml.t(d, (108, 214), TEMP, 44, g.CYAN, anchor="lm", ls=1.0)
        ml.t(d, (108, 244), COND, 17, g.TEXT_DIM, anchor="lm", ls=1.0)
        ml.t(d, (108, 266), MINMAX, 14, g.TEXT_DIM, anchor="lm", ls=0.6)
    img = ml.draw(img, paint)

    # barras: pasos (grande) y bateria (fina)
    img = seg_bar(img, (96, 274, 384, 296), 0.04, g.MAGENTA, segs=16, gap=4)
    img = seg_bar(img, (96, 306, 384, 318), 0.23, g.CYAN, segs=16, gap=4)

    def paint2(d):
        ml.label(d, (96, 292), "", ls=0)
        ml.t(d, (96, 346), STEPS, 26, g.CYAN, anchor="lm", ls=0.8)
        ml.t(d, (196, 346), "PASOS", 14, g.TEXT_DIM, anchor="lm", ls=0.8)
        ml.t(d, (96, 372), BAT, 26, g.CYAN, anchor="lm", ls=0.8)
        ml.t(d, (196, 372), "BATERIA", 14, g.TEXT_DIM, anchor="lm", ls=0.8)
        ml.t(d, (384, 346), STEPPCT, 24, g.MAGENTA, anchor="rm", ls=0.8)
        ml.t(d, (384, 372), BCN, 24, g.CYAN, anchor="rm", ls=0.8)
        ml.t(d, (384, 396), "BCN", 13, g.TEXT_DIM, anchor="rm", ls=0.8)
    img = ml.draw(img, paint2)

    # fichas inferiores
    for x0, w, name in ((64, 116, "BPM"), (188, 116, "MSG"), (312, 108, "EVT")):
        img = chip(img, (x0, 404, x0 + w, 452), outline=g.CYAN_DIM + (150,))

    def paint3(d):
        ml.label(d, (122, 418), "BPM", ls=1.2)
        ml.t(d, (122, 438), BPM, 26, g.MAGENTA)
        ml.label(d, (246, 418), "MSG", ls=1.2)
        ml.t(d, (246, 438), MSG, 26, g.MAGENTA)
        ml.label(d, (366, 418), "EVENTO", ls=1.0)
        ml.t(d, (366, 438), EVENT, 14, g.Violet)
    return ml.draw(img, paint3)


def main():
    variants = [("a-consola", concept_a), ("b-tarjetas", concept_b), ("c-arcade", concept_c)]
    made = []
    for slug, fn in variants:
        im = fn().convert("RGB").resize((480, 480), Image.LANCZOS)
        path = os.path.join(OUT, "mock-concept-%s.png" % slug)
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
    path = os.path.join(OUT, "mock-concepts.png")
    sheet.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
