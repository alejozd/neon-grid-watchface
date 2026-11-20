"""Tres redisenos totales (solo imagen): otra paleta y otra geometria.

No toca el diseno ni el proyecto. Cada concepto usa su propio fondo, su propia
paleta, su propia tipografia y su propia forma de colocar los datos; comparten
solo la informacion que debe estar (hora, fecha, clima, MSG, evento, bateria,
pulso, pasos, hora mundial).

    python tools\\debug\\mock_redesign.py
Salida: build/mock-redesign-d..f.png y build/mock-redesigns.png
"""
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import mock_layouts as ml  # noqa: E402
import render as g  # noqa: E402

OUT = os.path.join(ml.ROOT, "build")
FONTS = r"C:\Windows\Fonts"

DATE = "VIE 20 NOV"
TIME, SECS, AMPM = "9:54", "12", "A.M."
TEMP, COND, MINMAX = "18°", "NUBLADO", "20° / 11°"
BAT, BPM, STEPS, STEPPCT, MSG, BCN = "23%", "76", "266", "4%", "1", "15:54"
EVENT, EVENT_TXT = "12:00 P.M.", "Daily sync"

HH, MM, SS = 9, 54, 12
C = g.C
K = g.K


def font(name, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), int(size))
    except OSError:
        return g.mono(int(size), True)


def tracked(d, xy, s, f, fill, anchor="mm", ls=0.0):
    if ls <= 0:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    total = sum(d.textlength(ch, font=f) + ls for ch in s) - ls
    x, y = xy
    if anchor[0] == "r":
        x -= total
    elif anchor[0] == "m":
        x -= total / 2
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(ch, font=f) + ls


def hands(img, color, hub, width=8.2, mwidth=5.4, swidth=1.9, glow_r=2.2, gain=1.1,
          sec_color=None):
    h = g.make_hand(112, width, color, tail=7, shape="blade")
    m = g.make_hand(162, mwidth, color, tail=8, shape="blade")
    s = g.make_hand(178, swidth, sec_color or g.MAGENTA, tail=24, shape="needle")
    out = img.copy()
    for im, ang in ((h, HH % 12 * 30 + MM * 0.5), (m, MM * 6 + SS * 0.1), (s, SS * 6)):
        out = Image.alpha_composite(out, im.rotate(-ang, resample=Image.BICUBIC,
                                                    center=(g.CX, g.CY)))
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    r = 8.0 * K
    d.ellipse([g.CX - r, g.CY - r, g.CX + r, g.CY + r], fill=hub + (255,),
              outline=color + (235,), width=int(1.6 * K))
    r2 = 2.8 * K
    d.ellipse([g.CX - r2, g.CY - r2, g.CX + r2, g.CY + r2], fill=g.MAGENTA + (255,))
    return Image.alpha_composite(out, g.glow(lay, 3.0, 1.25))


def paint(img, painter, glow_r=3, gain=1.15):
    lay = g.new_layer()
    painter(ImageDraw.Draw(lay))
    return Image.alpha_composite(Image.alpha_composite(img, g.glow(lay, glow_r, gain)), lay)


# ===========================================================================
# D — SUNSET SYNTH: gradient calido, sol rayado, capsulas redondas
# ===========================================================================
SUN_CREAM = (255, 241, 220)
SUN_PINK = (255, 79, 203)
SUN_ORANGE = (255, 162, 58)
SUN_VIOLET = (196, 122, 255)


def sky():
    img = Image.new("RGBA", (C, C), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    stops = [(0, (24, 10, 48)), (110, (58, 18, 82)), (190, (124, 30, 104)),
             (250, (200, 42, 96)), (300, (255, 90, 70)), (330, (255, 150, 60)),
             (352, (26, 12, 40)), (480, (14, 8, 26))]
    for y in range(0, 480):
        # color interpolado por tramos
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= y <= y1:
                f = (y - y0) / max(1, y1 - y0)
                col = tuple(int(c0[j] + (c1[j] - c0[j]) * f) for j in range(3))
                d.rectangle([0, y * K, C, (y + 1) * K], fill=col + (255,))
                break
    # sol rayado
    lay = g.new_layer()
    ld = ImageDraw.Draw(lay)
    cx, cy, r = 240 * K, 236 * K, 92 * K
    ld.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 214, 130, 235))
    for i in range(6):
        yy = cy + r * 0.10 + i * r * 0.16
        ld.rectangle([cx - r, yy, cx + r, yy + r * 0.075], fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img, lay)
    # recorta las rayas del sol con el color del cielo
    hole = g.new_layer()
    hd = ImageDraw.Draw(hole)
    for i in range(6):
        yy = cy + r * 0.10 + i * r * 0.16
        hd.rectangle([cx - r, yy, cx + r, yy + r * 0.075], fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img, hole)
    # rejilla en perspectiva
    lay = g.new_layer()
    ld = ImageDraw.Draw(lay)
    horizon = 352 * K
    for i in range(-10, 11):
        x = 240 * K + i * 34 * K
        ld.line([(240 * K + i * 8 * K, horizon), (x * 1.0, C)],
                fill=(180, 90, 220, 90), width=int(1.2 * K))
    yy = horizon
    step = 3 * K
    while yy < C:
        ld.line([(0, yy), (C, yy)], fill=(180, 90, 220, 80), width=int(1.0 * K))
        step *= 1.35
        yy += step
    return Image.alpha_composite(img, lay)


def pill(img, b, radius=16, fill=(14, 8, 26, 190), outline=None):
    lay = g.new_layer()
    ImageDraw.Draw(lay).rounded_rectangle(
        [v * K for v in b], radius=radius * K, fill=fill,
        outline=outline or (255, 241, 220, 110), width=2 * K)
    return Image.alpha_composite(img, lay)


def concept_d():
    img = sky()
    img = hands(img, (44, 12, 56), (255, 241, 220), width=7.4, mwidth=5.0,
                sec_color=SUN_CREAM)
    img = pill(img, (34, 150, 168, 246), radius=24)
    img = pill(img, (312, 150, 446, 246), radius=24)
    img = pill(img, (34, 318, 176, 432), radius=24)
    img = pill(img, (312, 318, 446, 432), radius=24)

    def body(d):
        f_t = font("bahnschrift.ttf", 66 * K)
        f_sec = font("bahnschrift.ttf", 22 * K)
        f_lbl = font("bahnschrift.ttf", 14 * K)
        f_val = font("bahnschrift.ttf", 30 * K)
        # hora grande arriba, con brillo calido
        tracked(d, (232 * K, 84 * K), TIME, f_t, SUN_CREAM + (255,), "rm", 2 * K)
        tracked(d, (286 * K, 58 * K), SECS, f_sec, SUN_CREAM + (235,), "lm", 1 * K)
        tracked(d, (286 * K, 88 * K), AMPM, f_lbl, SUN_PINK + (255,), "lm", 1 * K)
        tracked(d, (240 * K, 132 * K), DATE, font("bahnschrift.ttf", 18 * K),
                SUN_PINK + (255,), "mm", 3 * K)

        # esquina superior izquierda: clima
        tracked(d, (52 * K, 172 * K), TEMP, font("bahnschrift.ttf", 40 * K),
                SUN_CREAM + (255,), "lm", 1 * K)
        tracked(d, (52 * K, 206 * K), COND, f_lbl, SUN_ORANGE + (255,), "lm", 2 * K)
        tracked(d, (52 * K, 228 * K), MINMAX, f_lbl, (255, 225, 205, 210), "lm", 1 * K)

        # superior derecha: avisos y evento
        tracked(d, (330 * K, 168 * K), "MSG", f_lbl, (255, 200, 220, 220), "lm", 2 * K)
        tracked(d, (330 * K, 196 * K), MSG, f_val, SUN_PINK + (255,), "lm", 1 * K)
        tracked(d, (330 * K, 224 * K), EVENT, font("bahnschrift.ttf", 16 * K),
                SUN_VIOLET + (255,), "lm", 0.5 * K)

        # inferior izquierda: bateria y pulso
        tracked(d, (52 * K, 338 * K), "BATERIA", f_lbl, (255, 220, 210, 220), "lm", 2 * K)
        tracked(d, (52 * K, 372 * K), BAT, font("bahnschrift.ttf", 34 * K),
                SUN_ORANGE + (255,), "lm", 1 * K)
        tracked(d, (52 * K, 408 * K), "BPM " + BPM, font("bahnschrift.ttf", 16 * K),
                (255, 225, 235, 235), "lm", 1 * K)

        # inferior derecha: pasos y hora mundial
        tracked(d, (428 * K, 338 * K), "PASOS", f_lbl, (255, 220, 210, 220), "rm", 2 * K)
        tracked(d, (428 * K, 372 * K), STEPS, font("bahnschrift.ttf", 34 * K),
                SUN_CREAM + (255,), "rm", 1 * K)
        tracked(d, (428 * K, 408 * K), "BCN " + BCN, font("bahnschrift.ttf", 16 * K),
                SUN_ORANGE + (255,), "rm", 1 * K)
    return paint(img, body, glow_r=4, gain=1.2)


# ===========================================================================
# E — PIXEL RAID: 8 bits, verde acido, bloques duros
# ===========================================================================
PX_LIME = (140, 255, 61)
PX_AMBER = (255, 176, 32)
PX_RED = (255, 61, 90)
PX_WHITE = (236, 255, 240)


def pixel_bg():
    img = Image.new("RGBA", (C, C), (6, 7, 10, 255))
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    # scanlines
    for y in range(0, 480, 3):
        d.rectangle([0, y * K, C, y * K + K], fill=(255, 255, 255, 10))
    # marco de bloques
    blk = 12 * K
    for i in range(0, 480, 12):
        if (i // 12) % 2 == 0:
            d.rectangle([i * K, 18 * K, i * K + blk, 26 * K], fill=PX_LIME + (55,))
            d.rectangle([i * K, 454 * K, i * K + blk, 462 * K], fill=PX_LIME + (55,))
    return Image.alpha_composite(img, lay)


def pixelate(img, block):
    small = img.resize((C // block, C // block), Image.BOX)
    return small.resize((C, C), Image.NEAREST)


def hearts(img, x, y, total, filled, color):
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    u = 7            # unidad de pixel en espacio 480
    for i in range(total):
        hx = x + i * (u * 6)
        on = i < filled
        col = color if on else (44, 52, 48)
        # corazon de bloques 5x4
        rows = [(1, 1, 0, 1, 1), (1, 1, 1, 1, 1), (0, 1, 1, 1, 0), (0, 0, 1, 0, 0)]
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit:
                    d.rectangle([(hx + rx * u) * K, (y + ry * u) * K,
                                 (hx + (rx + 1) * u) * K, (y + (ry + 1) * u) * K],
                                fill=col + (255,))
    return Image.alpha_composite(img, lay)


def concept_e():
    img = pixel_bg()
    img = hands(img, PX_LIME, (10, 14, 10), width=8.6, mwidth=5.6, glow_r=0.2, gain=0.0)
    img = pixelate(img, 3)          # fondo y agujas en bloques

    # cajas duras
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    d.rectangle([36 * K, 180 * K, 444 * K, 272 * K], outline=PX_LIME + (80,), width=1 * K)
    d.rectangle([36 * K, 284 * K, 444 * K, 376 * K], outline=PX_AMBER + (80,), width=1 * K)
    for x0 in (36, 176, 316):
        d.rectangle([x0 * K, 388 * K, (x0 + 128) * K, 444 * K],
                    outline=PX_WHITE + (55,), width=1 * K)
    img = Image.alpha_composite(img, lay)

    def body(d):
        f_time = font('consolab.ttf', 90 * K)
        f_lbl = font('consolab.ttf', 14 * K)
        f_val = font('consolab.ttf', 30 * K)
        tracked(d, (222 * K, 96 * K), TIME, f_time, PX_WHITE + (255,), "rm", 2 * K)
        tracked(d, (252 * K, 68 * K), SECS, font('consolab.ttf', 26 * K), PX_LIME + (255,), "lm", 1 * K)
        tracked(d, (252 * K, 100 * K), AMPM, f_lbl, PX_AMBER + (255,), "lm", 1 * K)
        tracked(d, (240 * K, 152 * K), DATE, font('consolab.ttf', 18 * K), PX_AMBER + (255,), "mm", 3 * K)

        # caja 1: clima (izq) + evento (der)
        tracked(d, (56 * K, 206 * K), TEMP, font('consolab.ttf', 38 * K), PX_LIME + (255,), "lm", 1 * K)
        tracked(d, (56 * K, 234 * K), COND, f_lbl, PX_WHITE + (225,), "lm", 2 * K)
        tracked(d, (56 * K, 254 * K), MINMAX, f_lbl, (150, 200, 160, 225), "lm", 1 * K)
        tracked(d, (424 * K, 206 * K), EVENT, font('consolab.ttf', 17 * K), PX_AMBER + (255,), "rm", 0.5 * K)
        tracked(d, (424 * K, 232 * K), EVENT_TXT, f_lbl, PX_WHITE + (205,), "rm", 0.5 * K)

        # caja 2: bateria (izq) + pasos (der)
        tracked(d, (56 * K, 304 * K), "BATERIA " + BAT, f_lbl, PX_WHITE + (230,), "lm", 1 * K)
        tracked(d, (248 * K, 304 * K), "PASOS " + STEPS + "  " + STEPPCT, f_lbl,
                PX_LIME + (255,), "lm", 1 * K)
        tracked(d, (248 * K, 352 * K), "PULSO " + BPM, f_val, PX_RED + (255,), "lm", 1 * K)

        # fichas
        tracked(d, (100 * K, 404 * K), "BPM", f_lbl, PX_WHITE + (150,), "mm", 1 * K)
        tracked(d, (100 * K, 426 * K), BPM, font("consolab.ttf", 24 * K), PX_RED + (255,), "mm", 1 * K)
        tracked(d, (240 * K, 404 * K), "MSG", f_lbl, PX_WHITE + (150,), "mm", 1 * K)
        tracked(d, (240 * K, 426 * K), MSG, font("consolab.ttf", 24 * K), PX_AMBER + (255,), "mm", 1 * K)
        tracked(d, (380 * K, 404 * K), "BCN", f_lbl, PX_WHITE + (150,), "mm", 1 * K)
        tracked(d, (380 * K, 426 * K), BCN, font("consolab.ttf", 22 * K), PX_LIME + (255,), "mm", 1 * K)
    img = paint(img, body, glow_r=0.2, gain=0.0)
    # corazones: bateria (2/5) y pulso (4/5), en su carril
    img = hearts(img, 56, 318, 5, 2, PX_LIME)
    return img


# ===========================================================================
# F — PAPER NEON: fondo claro, tinta negra, un acento electrico
# ===========================================================================
PAPER = (242, 237, 228)
INK = (22, 20, 26)
BLUE = (11, 95, 255)
ORANGE = (255, 90, 31)
PLUM = (107, 43, 255)


def paper_bg():
    img = Image.new("RGBA", (C, C), PAPER + (255,))
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    # rejilla muy suave
    for i in range(0, 480, 20):
        d.line([(i * K, 0), (i * K, C)], fill=INK + (10,), width=K)
        d.line([(0, i * K), (C, i * K)], fill=INK + (10,), width=K)
    # circulo y marcas
    r = 224 * K
    d.ellipse([240 * K - r, 240 * K - r, 240 * K + r, 240 * K + r],
              outline=INK + (60,), width=int(1.4 * K))
    for m in range(60):
        a = math.radians(m * 6 - 90)
        r1, r2 = (206 * K, 214 * K) if m % 5 else (200 * K, 216 * K)
        d.line([(240 * K + r1 * math.cos(a), 240 * K + r1 * math.sin(a)),
                (240 * K + r2 * math.cos(a), 240 * K + r2 * math.sin(a))],
               fill=INK + (90 if m % 5 else 150,), width=int(1.2 * K))
    return Image.alpha_composite(img, lay)


def concept_f():
    img = paper_bg()
    img = hands(img, INK, (255, 255, 255), width=5.6, mwidth=3.6, glow_r=0.2, gain=0.0)

    def body(d):
        f_time = font("segoeuil.ttf", 104 * K)
        f_lbl = font("segoeuisb.ttf", 14 * K)
        f_val = font("segoeuil.ttf", 34 * K)
        tracked(d, (232 * K, 288 * K), TIME, f_time, INK + (255,), "rm", 3 * K)
        tracked(d, (276 * K, 252 * K), SECS, font("segoeuil.ttf", 28 * K), BLUE + (255,),
                "lm", 1 * K)
        tracked(d, (276 * K, 288 * K), AMPM, f_lbl, INK + (200,), "lm", 2 * K)
        # regla bajo la hora
        d.line([(150 * K, 330 * K), (330 * K, 330 * K)], fill=INK + (70,), width=K)
        tracked(d, (240 * K, 348 * K), DATE, font("segoeuisb.ttf", 17 * K), INK + (235,),
                "mm", 3 * K)

        # clima arriba izquierda
        tracked(d, (112 * K, 150 * K), TEMP, font("segoeuil.ttf", 46 * K), INK + (255,),
                "lm", 1 * K)
        tracked(d, (112 * K, 182 * K), COND, f_lbl, ORANGE + (255,), "lm", 2 * K)
        tracked(d, (112 * K, 202 * K), MINMAX, f_lbl, INK + (150,), "lm", 1 * K)

        # evento arriba derecha
        tracked(d, (372 * K, 118 * K), "EVENTO", f_lbl, INK + (150,), "rm", 2 * K)
        tracked(d, (372 * K, 142 * K), EVENT, font("segoeuisb.ttf", 17 * K), PLUM + (255,),
                "rm", 0.5 * K)
        tracked(d, (372 * K, 162 * K), EVENT_TXT, f_lbl, INK + (170,), "rm", 0.5 * K)

        # metricas abajo, en tres columnas separadas por filetes
        cols = [(96, "BATERIA", BAT, BLUE), (240, "PULSO", BPM, ORANGE),
                (384, "PASOS", STEPS, INK)]
        for x, name, value, color in cols:
            tracked(d, (x * K, 384 * K), name, f_lbl, INK + (140,), "mm", 2 * K)
            tracked(d, (x * K, 410 * K), value, f_val, color + (255,), "mm", 1 * K)
        d.line([(168 * K, 374 * K), (168 * K, 424 * K)], fill=INK + (55,), width=K)
        d.line([(312 * K, 374 * K), (312 * K, 424 * K)], fill=INK + (55,), width=K)

        # avisos y hora mundial
        tracked(d, (240 * K, 442 * K), "MSG " + MSG + "   ·   BCN " + BCN, f_lbl,
                INK + (215,), "mm", 3 * K)
    img = paint(img, body, glow_r=0.2, gain=0.0)

    # arco de bateria y de pasos sobre el borde, en tinta
    lay = g.new_layer()
    d = ImageDraw.Draw(lay)
    bb = [240 * K - 216 * K, 240 * K - 216 * K, 240 * K + 216 * K, 240 * K + 216 * K]
    d.arc(bb, start=246 - 90, end=294 - 90, fill=BLUE + (235,), width=int(4 * K))
    d.arc(bb, start=300 - 90, end=340 - 90, fill=ORANGE + (235,), width=int(4 * K))
    return Image.alpha_composite(img, lay)


def main():
    variants = [("d-sunset", concept_d), ("e-pixel", concept_e), ("f-paper", concept_f)]
    made = []
    for slug, fn in variants:
        im = fn().convert("RGB").resize((480, 480), Image.LANCZOS)
        path = os.path.join(OUT, "mock-redesign-%s.png" % slug)
        im.save(path)
        made.append((slug, im))
        print("wrote", path)

    pad, cap = 12, 26
    w = sum(im.width for _s, im in made) + pad * (len(made) + 1)
    h = made[0][1].height + cap + pad * 2
    sheet = Image.new("RGB", (w, h), (30, 30, 34))
    d = ImageDraw.Draw(sheet)
    f = g.mono(14, True)
    x = pad
    for slug, im in made:
        sheet.paste(im, (x, pad))
        d.text((x + im.width / 2, pad + im.height + cap / 2), slug,
               font=f, fill=(235, 235, 240), anchor="mm")
        x += im.width + pad
    path = os.path.join(OUT, "mock-redesigns.png")
    sheet.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
