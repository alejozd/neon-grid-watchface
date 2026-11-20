"""
Cyberpunk watch face design renderer (480x480, Galaxy Watch 6 44mm).

Produces:
  design/out/preview_full.png   -> what the final face looks like
  design/out/bg.png             -> static background layer only (no hands/no live text)
  design/out/hand_hour.png      -> hour hand, 480x480 canvas, pivot at center
  design/out/hand_minute.png
  design/out/hand_second.png
  design/out/ticks.png          -> optional tick ring overlay
All final art is 480x480, drawn at 4x and downsampled (anti-aliasing).
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 480
K = 4           # supersample factor
C = S * K       # canvas size at high res
CX = CY = C / 2

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# ---------------- palette ----------------
VOID      = (5, 8, 14)
PANEL     = (10, 17, 28)
CYAN      = (34, 231, 255)
CYAN_DIM  = (18, 108, 124)
MAGENTA   = (255, 42, 109)
Violet    = (162, 75, 255)
AMBER     = (255, 176, 32)
TEXT      = (198, 235, 245)
TEXT_DIM  = (74, 112, 132)
WHITE     = (235, 250, 255)

# Named palettes: (primary/hands, secondary/seconds, accent, base void, panel)
PALETTES = {
    "neon": {
        "cyan": (34, 231, 255), "dim": (18, 108, 124),
        "magenta": (255, 42, 109), "violet": (162, 75, 255),
        "void": (5, 8, 14), "panel": (10, 17, 28),
    },
    "gold": {
        "cyan": (255, 205, 94), "dim": (140, 108, 40),
        "magenta": (255, 122, 61), "violet": (232, 168, 74),
        "void": (8, 7, 5), "panel": (18, 15, 10),
    },
    "ice": {
        "cyan": (158, 232, 255), "dim": (92, 124, 146),
        "magenta": (86, 138, 240), "violet": (208, 228, 248),
        "void": (4, 8, 15), "panel": (9, 16, 27),
    },
}

PALETTE_NAME = "neon"


def apply_palette(name):
    """Rebinds the module-level colour constants from a named palette."""
    global PALETTE_NAME, CYAN, CYAN_DIM, MAGENTA, Violet, VOID, PANEL
    p = PALETTES[name]
    PALETTE_NAME = name
    CYAN = p["cyan"]
    CYAN_DIM = p["dim"]
    MAGENTA = p["magenta"]
    Violet = p["violet"]
    VOID = p["void"]
    PANEL = p["panel"]

FONT_DIR = r"C:\Windows\Fonts"


def font(name, size):
    p = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(p, size)
    except OSError:
        return ImageFont.load_default()


def mono(size, bold=False):
    return font("consolab.ttf" if bold else "consola.ttf", size)


def polar(cx, cy, r, deg):
    """deg measured clockwise from 12 o'clock."""
    a = math.radians(deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def glow(img, radius, gain=1.0):
    """Extract bright pixels, blur them, add back -> neon bloom."""
    small = img.resize((C // 4, C // 4), Image.LANCZOS)
    b = small.filter(ImageFilter.GaussianBlur(radius * K / 4.0))
    b = b.resize((C, C), Image.LANCZOS)
    if gain != 1.0:
        b = Image.eval(b, lambda v: min(255, int(v * gain)))
    return Image.alpha_composite(img, b)


def new_layer():
    return Image.new("RGBA", (C, C), (0, 0, 0, 0))


# ---------------- background ----------------
def make_bg():
    img = Image.new("RGBA", (C, C), VOID + (255,))

    # radial gradient: slightly lighter in the middle
    grad = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    steps = 90
    for i in range(steps, 0, -1):
        t = i / steps
        r = (C / 2) * t
        # deep blue-teal core -> void edges
        col = (
            int(6 + 12 * (1 - t)),
            int(9 + 22 * (1 - t)),
            int(16 + 34 * (1 - t)),
            int(255 * 0.10 * (t ** 0.6)),
        )
        gd.ellipse([CX - r, CY - r, CX + r, CY + r], fill=col)
    img = Image.alpha_composite(img, grad)

    d = ImageDraw.Draw(img)

    # --- fine tech grid, clipped to the circle ---
    grid = new_layer()
    gd2 = ImageDraw.Draw(grid)
    cell = 20 * K
    for x in range(0, C + 1, cell):
        gd2.line([(x, 0), (x, C)], fill=(20, 60, 80, 26), width=1 * K)
    for y in range(0, C + 1, cell):
        gd2.line([(0, y), (C, y)], fill=(20, 60, 80, 26), width=1 * K)
    # neon horizontal scan bands
    for i, y in enumerate(range(int(0.16 * C), int(0.86 * C), int(0.055 * C))):
        a = 16 if i % 2 == 0 else 8
        gd2.line([(0, y), (C, y)], fill=(34, 231, 255, a), width=1 * K)

    mask = Image.new("L", (C, C), 0)
    ImageDraw.Draw(mask).ellipse([4 * K, 4 * K, C - 4 * K, C - 4 * K], fill=255)
    img.paste(Image.alpha_composite(img, grid), (0, 0), mask)

    d = ImageDraw.Draw(img)

    # --- vignette ---
    vig = new_layer()
    vd = ImageDraw.Draw(vig)
    for i in range(60):
        r = (C / 2) * (0.62 + 0.38 * i / 59)
        vd.ellipse([CX - r, CY - r, CX + r, CY + r], outline=(0, 0, 0, 10), width=6 * K)
    img = Image.alpha_composite(img, vig)
    d = ImageDraw.Draw(img)

    # --- concentric rings ---
    def ring(r, col, w):
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=col, width=int(w * K))

    ring(229 * K, (34, 231, 255, 70), 1.2)
    ring(224 * K, (34, 231, 255, 22), 0.8)

    # --- tick marks: 60 minor, 12 major ---
    for i in range(60):
        deg = i * 6
        major = (i % 5 == 0)
        r1 = 210 * K if major else 215 * K
        r2 = 223 * K
        w = 2.0 if major else 1.0
        col = (34, 231, 255, 190) if major else (74, 112, 132, 150)
        x1, y1 = polar(CX, CY, r1, deg)
        x2, y2 = polar(CX, CY, r2, deg)
        d.line([(x1, y1), (x2, y2)], fill=col, width=int(w * K))

    # NOTE: the inner dashed ring was removed on purpose: it created a dead gap
    # between itself and the bezel, and the face now uses that space for data.

    # NOTE: the two arcs are NOT part of the background any more: they are real
    # gauges (battery and step goal) drawn by the watch face XML, so the mock draws
    # them in compose_preview() with the live values.
    return img


def arc_gauge(r, a1, a2, frac, col_a, col_b, bg_a=26):
    lay = new_layer()
    ld = ImageDraw.Draw(lay)
    bb = [CX - r * K, CY - r * K, CX + r * K, CY + r * K]
    # track
    ld.arc(bb, start=a1 - 90, end=a2 - 90, fill=(col_a[0], col_a[1], col_a[2], bg_a), width=int(3.4 * K))
    # value: small arc segments = "energy bar"
    segs = 18
    total = a2 - a1
    on = int(segs * max(0.0, min(1.0, frac)))
    for i in range(segs):
        s1 = a1 + total * i / segs + 0.6
        s2 = a1 + total * (i + 1) / segs - 0.6
        t = i / max(1, segs - 1)
        col = tuple(int(col_a[j] + (col_b[j] - col_a[j]) * t) for j in range(3))
        if i < on:
            ld.arc(bb, start=s1 - 90, end=s2 - 90, fill=col + (235,), width=int(3.2 * K))
    return glow(lay, 4, 1.35)


# ---------------- hands ----------------
def make_hand(length, width, color, tail=14, taper=0.35, hub=None, shape="blade"):
    """Hand pointing UP (12 o'clock) on a square canvas, pivot at canvas center.

    "blade"  -> tapered blade: pointed spike, chamfered shoulders, a bright spine
                and a slim skeleton window in the upper third (hour + minute).
    "needle" -> hairline needle with a tip dot and a disc counterweight (second).
    """
    lay = new_layer()
    ld = ImageDraw.Draw(lay)
    L = length * K
    W = width * K
    T = tail * K
    cxx, cyy = CX, CY

    if shape == "blade":
        y_tip = cyy - L
        y_base = cyy + T
        span = y_base - y_tip

        def half_at(t):
            """Half width at t (0 = tip, 1 = base): pointed, widest at 75 %."""
            w = (W / 2.0) * (0.05 + 0.95 * (t ** 0.6))
            if t > 0.75:
                w *= 1.0 - 0.55 * (t - 0.75) / 0.25
            return w

        n = 22
        right = [(cxx + half_at(i / n), y_tip + span * i / n) for i in range(n + 1)]
        left = [(cxx - half_at(i / n), y_tip + span * i / n) for i in range(n, -1, -1)]
        ld.polygon(right + left, fill=color + (255,))
        # bright spine: the neon "filament" running down the blade
        ld.line([(cxx, y_tip + span * 0.10), (cxx, y_base - 1.4 * K)],
                fill=(240, 252, 255, 190), width=max(1, int(0.8 * K)))
        # segment mark near the tip, like an etched scale
        ty = y_tip + span * 0.66
        ld.line([(cxx - half_at(0.66), ty), (cxx + half_at(0.66), ty)],
                fill=(3, 8, 13, 160), width=max(1, int(0.5 * K)))
        # rim: dark on the outside so it separates from the dial grid
        ld.line(right + left, fill=(3, 8, 13, 150), width=max(1, int(0.4 * K)))
    elif shape == "needle":
        tip = 2.6 * K
        # hairline with a slightly wider base and a pointed tip
        ld.line([(cxx, cyy - L + tip), (cxx, cyy + T)], fill=color + (255,),
                width=max(1, int(W)))
        ld.polygon([(cxx, cyy - L), (cxx + tip * 0.55, cyy - L + tip * 1.9),
                    (cxx - tip * 0.55, cyy - L + tip * 1.9)], fill=color + (255,))
        # white hot core
        ld.line([(cxx, cyy - L + tip * 1.4), (cxx, cyy + T * 0.8)],
                fill=(255, 236, 246, 175), width=max(1, int(W * 0.42)))
        # counterweight disc + hub ring
        cr = W * 3.1
        ld.ellipse([cxx - cr, cyy + T - cr, cxx + cr, cyy + T + cr], fill=color + (255,))
        ld.ellipse([cxx - cr * 0.52, cyy + T - cr * 0.52, cxx + cr * 0.52, cyy + T + cr * 0.52],
                   fill=(6, 10, 16, 235))
    else:  # "spear" (legacy)
        tip_w = 1.4 * K
        shoulder = 0.70 * L
        bw = W * 0.80
        pts = [
            (cxx, cyy - L),
            (cxx + tip_w, cyy - shoulder),
            (cxx + bw / 2, cyy - W * 0.7),
            (cxx + bw * 0.46, cyy + T * 0.5),
            (cxx + W * 0.26, cyy + T),
            (cxx - W * 0.26, cyy + T),
            (cxx - bw * 0.46, cyy + T * 0.5),
            (cxx - bw / 2, cyy - W * 0.7),
            (cxx - tip_w, cyy - shoulder),
        ]
        ld.polygon(pts, fill=color + (255,))
        ld.line(pts + [pts[0]], fill=(2, 6, 10, 210), width=int(0.45 * K))
        ld.line([(cxx, cyy - L * 0.94), (cxx, cyy + T * 0.75)],
                fill=(255, 255, 255, 150), width=max(1, int(0.75 * K)))
    return glow(lay, 2.2 if shape == "blade" else 3.2, 1.10)


def make_hub():
    lay = new_layer()
    ld = ImageDraw.Draw(lay)
    r = 8.6 * K
    ld.ellipse([CX - r, CY - r, CX + r, CY + r], fill=(8, 14, 22, 255), outline=CYAN + (235,), width=int(1.6 * K))
    r2 = 2.6 * K
    ld.ellipse([CX - r2, CY - r2, CX + r2, CY + r2], fill=MAGENTA + (255,))
    return glow(lay, 3.0, 1.25)


# ---------------- text helpers ----------------
def text_c(d, xy, s, f, fill, anchor="mm", spacing_=0):
    if spacing_ <= 0:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    # manual letter-spacing
    total = sum(d.textlength(ch, font=f) + spacing_ * K for ch in s) - spacing_ * K
    x, y = xy
    if anchor == "rm":
        x -= total
    elif anchor == "mm":
        x -= total / 2
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, anchor="lm")
        x += d.textlength(ch, font=f) + spacing_ * K


# ---------------- layout (single source of truth for mock + watch face XML) ----------------
LAYOUT = {
    # the time is right-anchored on x so the seconds column always clears it,
    # no matter whether the hour has one or two digits.
    "time":    {"x": 326, "y": 302, "size": 66, "ls": 1.4, "anchor": "rm"},
    "sec":     {"x": 362, "y": 290, "size": 22, "ls": 1.0},
    "ampm":    {"x": 360, "y": 318, "size": 15, "ls": 0.3},
    "date":    {"x": 240, "y": 366, "size": 26, "ls": 1.2},
    "temp":    {"x": 240, "y": 78,  "size": 30, "ls": 1.0},
    "cond":    {"x": 240, "y": 114, "size": 18, "ls": 0.3},
    "msg_v":   {"x": 152, "y": 188, "size": 30, "ls": 0.0},
    "evt_v":   {"x": 342, "y": 178, "size": 18, "ls": 0.0},
    "bat_v":   {"x": 78,  "y": 228, "size": 30, "ls": 0.0},
    "hr_v":    {"x": 92,  "y": 300, "size": 32, "ls": 0.0},
    "steps_v": {"x": 368, "y": 244, "size": 26, "ls": 0.0},
    "steps_pct": {"x": 380, "y": 268, "size": 15, "ls": 0.0},
    "tminmax": {"x": 240, "y": 142, "size": 16, "ls": 0.3},
    # world clock under the date: label anchored to the right of the divider,
    # 24 h value anchored left, so the pair stays centred whatever the hour is
    "wl_lbl":  {"x": 232, "y": 400, "size": 13, "ls": 0.9, "anchor": "rm"},
    "wclock":  {"x": 240, "y": 400, "size": 24, "ls": 1.0, "anchor": "lm"},
}


def compose_preview(bg, hour, minute, second, hh=22, mm=47, ss=5, date="VIE 12 SEP",
                    hr="72", steps="8,240", batt="64", temp="18°", notif="3", evt="2",
                    bcn="16:43"):
    img = bg.copy()
    img = Image.alpha_composite(img, arc_gauge(205, 246, 294, float(str(batt).replace("%","")) / 100.0,
                                              CYAN, MAGENTA))
    img = Image.alpha_composite(img, arc_gauge(205, 300, 340, 0.33, MAGENTA, Violet, bg_a=40))
    # hands
    hd = hour.rotate(-(hh % 12 * 30 + mm * 0.5), resample=Image.BICUBIC, center=(CX, CY))
    md = minute.rotate(-(mm * 6 + ss * 0.1), resample=Image.BICUBIC, center=(CX, CY))
    sd = second.rotate(-(ss * 6), resample=Image.BICUBIC, center=(CX, CY))
    img = Image.alpha_composite(img, hd)
    img = Image.alpha_composite(img, md)
    img = Image.alpha_composite(img, sd)
    img = Image.alpha_composite(img, make_hub())

    lay = new_layer()
    d = ImageDraw.Draw(lay)

    def val(key, s, col):
        L = LAYOUT[key]
        text_c(d, (L["x"] * K, L["y"] * K), s, mono(L["size"] * K, True), col,
               anchor=L.get("anchor", "mm"), spacing_=L.get("ls", 0) * K)

    # --- digital time block: big time, seconds and am/pm stacked to its right ---
    h12 = hh % 12 or 12
    ampm = "AM" if hh < 12 else "PM"
    val("time", f"{h12}:{mm:02d}", CYAN)
    val("sec", f"{ss:02d}", CYAN)
    val("ampm", ampm, CYAN)
    val("date", date, MAGENTA)

    # --- top: temperature + condition + daily min/max ---
    val("temp", temp, CYAN)
    val("tminmax", "18° / 9°", TEXT_DIM)

    # --- notification chip (upper-left) / events chip (upper-right) ---
    val("msg_v", notif, MAGENTA)
    val("evt_v", evt, Violet)

    # --- left: battery ---
    val("bat_v", batt + "%", CYAN)

    # --- bottom-left: heart rate + ecg ---
    val("hr_v", hr, MAGENTA)
    hx, hy = LAYOUT["hr_v"]["x"], LAYOUT["hr_v"]["y"]
    ecg = [(hx - 40, hy + 30), (hx - 26, hy + 30), (hx - 20, hy + 22),
           (hx - 14, hy + 40), (hx - 8, hy + 26), (hx - 2, hy + 30), (hx + 38, hy + 30)]
    d.line([(x * K, y * K) for x, y in ecg], fill=MAGENTA + (195,), width=int(1.5 * K))

    # --- bottom-right: steps + goal progress ---
    val("steps_v", steps, CYAN)
    val("steps_pct", "34%", CYAN_DIM)

    # --- world clock (Barcelona) under the date ---
    val("wl_lbl", "BCN", TEXT_DIM)
    val("wclock", bcn, CYAN)


    img = Image.alpha_composite(img, glow(lay, 3, 1.22))

    # --- static HUD labels (same source as the baked PNGs) ---
    llay = new_layer()
    ld = ImageDraw.Draw(llay)
    for _n, txt, sz, col, ls, cx, cy in LABELS:
        text_c(ld, (cx * K, cy * K), txt, mono(sz * K, True), col, spacing_=ls * K)
    img = Image.alpha_composite(img, llay)
    return img


def make_bg_ambient():
    """Burn-in-safe ambient background: near black, only a faint bezel ring and
    the 12 hour indices survive."""
    img = Image.new("RGBA", (C, C), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    r = 229 * K
    d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=(120, 140, 155, 46), width=int(1.2 * K))
    for i in range(12):
        deg = i * 30
        r1, r2 = 214 * K, 222 * K
        x1, y1 = polar(CX, CY, r1, deg)
        x2, y2 = polar(CX, CY, r2, deg)
        d.line([(x1, y1), (x2, y2)], fill=(150, 170, 185, 110), width=int(1.6 * K))
    return img


def make_hand_ambient(length, width, tail=14, shape="spear"):
    return make_hand(length, width, (170, 186, 198), tail=tail, shape=shape)


def compose_ambient(bg, hour, minute, hh=22, mm=47, date="VIE 12 SEP"):
    img = bg.copy()
    hd = hour.rotate(-(hh % 12 * 30 + mm * 0.5), resample=Image.BICUBIC, center=(CX, CY))
    md = minute.rotate(-(mm * 6), resample=Image.BICUBIC, center=(CX, CY))
    img = Image.alpha_composite(img, hd)
    img = Image.alpha_composite(img, md)
    lay = new_layer()
    d = ImageDraw.Draw(lay)
    text_c(d, (CX, 314 * K), f"{hh:02d}:{mm:02d}", mono(56 * K, True), (176, 192, 204), spacing_=2.0 * K)
    text_c(d, (CX, 352 * K), date, mono(15 * K, True), (128, 146, 160), spacing_=2.0 * K)
    img = Image.alpha_composite(img, lay)
    r = 7.0 * K
    hd2 = new_layer()
    ImageDraw.Draw(hd2).ellipse([CX - r, CY - r, CX + r, CY + r], fill=(16, 20, 26, 255),
                               outline=(150, 168, 182, 220), width=int(1.4 * K))
    return Image.alpha_composite(img, hd2)


def save_hand(img, name):
    """Crop a hand to its bounding box and emit its placement metadata so the
    watch face XML can position/rotate it exactly (pivot = original center)."""
    import json
    bbox = img.getbbox()
    if bbox is None:
        raise SystemExit("empty hand: " + name)
    x0, y0, x1, y1 = bbox
    crop = img.crop(bbox).resize((round((x1 - x0) / K), round((y1 - y0) / K)), Image.LANCZOS)
    path = os.path.join(OUT, name + ".png")
    crop.save(path, "PNG", optimize=True)
    meta = {
        "file": name + ".png",
        "x": round(x0 / K, 2), "y": round(y0 / K, 2),
        "w": crop.size[0], "h": crop.size[1],
        "pivotX": round((CX - x0) / (x1 - x0), 6),
        "pivotY": round((CY - y0) / (y1 - y0), 6),
    }
    print("wrote", path, crop.size, "pivot", meta["pivotX"], meta["pivotY"])
    return meta


def save(img, name, size=S):
    out = img.convert("RGB").resize((size, size), Image.LANCZOS) if img.mode == "RGBA" and False else img
    out = img.resize((size, size), Image.LANCZOS)
    path = os.path.join(OUT, name)
    out.save(path, "PNG", optimize=True)
    print("wrote", path, out.size, out.mode)
    return path


# ---------------- static labels baked as images ----------------
# (name, text, size_px, color, letter_spacing, center_x, center_y)
# NOTE: there is no baked label for the weather condition: that text is dynamic,
# and a baked "NUBLADO" on top of it produced garbled overlapping text on device.
LABELS = [
    ("lbl_bat",    "BAT",     13.0, TEXT_DIM, 0.9, 78,  202),
    ("lbl_bpm",    "BPM",     13.0, TEXT_DIM, 0.9, 88,  276),
    ("lbl_pasos",  "PASOS",   13.0, TEXT_DIM, 0.9, 368, 218),
    ("lbl_msg",    "MSG",     13.0, TEXT_DIM, 0.9, 150, 160),
    # la etiqueta EVENT va encima de la ranura de complicacion, no dentro
    ("lbl_event",  "EVENT",   13.0, TEXT_DIM, 0.9, 352, 138),
]


def bake_labels():
    """Render each static label on its own transparent canvas, tight-cropped,
    and emit a JSON manifest with the anchor position and crop offset so the
    watch face XML can place them precisely."""
    import json
    ldir = os.path.join(OUT, "labels")
    os.makedirs(ldir, exist_ok=True)
    manifest = {}
    for name, txt, sz, col, ls, cx, cy in LABELS:
        f = mono(int(round(sz * K)), True)
        tmp = Image.new("RGBA", (C, C), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        left = 0.0
        total = sum(td.textlength(ch, font=f) + ls * K for ch in txt) - ls * K
        x = cx * K - total / 2
        asc, desc = f.getmetrics()
        y = cy * K
        for ch in txt:
            td.text((x, y), ch, font=f, fill=col + (255,), anchor="lm")
            x += td.textlength(ch, font=f) + ls * K
        bbox = tmp.getbbox()
        if bbox is None:
            continue
        img = tmp.crop(bbox)
        w, h = img.size
        img = img.resize((max(1, round(w / K)), max(1, round(h / K))), Image.LANCZOS)
        img.save(os.path.join(ldir, name + ".png"), "PNG", optimize=True)
        # position of the crop's top-left in the 480x480 design space
        manifest[name] = {
            "file": name + ".png",
            "x": round(bbox[0] / K, 1), "y": round(bbox[1] / K, 1),
            "w": img.size[0], "h": img.size[1],
        }
    with open(os.path.join(ldir, "labels.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("baked", len(manifest), "labels")


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Renders the Neon Grid art.")
    ap.add_argument("--palette", default="neon", choices=sorted(PALETTES),
                    help="colour palette to render")
    ap.add_argument("--suffix", default="",
                    help="suffix for the generated PNGs / JSONs (e.g. -gold)")
    args = ap.parse_args()
    apply_palette(args.palette)
    sfx = args.suffix

    def named(base):
        return base + sfx + ".png"

    bg = make_bg()
    hour = make_hand(112, 8.2, CYAN, tail=7, shape="blade")
    minute = make_hand(162, 5.4, CYAN, tail=8, shape="blade")
    second = make_hand(178, 1.9, MAGENTA, tail=24, shape="needle")

    full = compose_preview(bg, hour, minute, second)
    save(full, named("preview_full"))
    save(bg, named("bg"))

    hands = {
        "hour": save_hand(hour, "hand_hour" + sfx),
        "minute": save_hand(minute, "hand_minute" + sfx),
        "second": save_hand(second, "hand_second" + sfx),
    }
    with open(os.path.join(OUT, "hands" + sfx + ".json"), "w", encoding="utf-8") as fh:
        json.dump(hands, fh, indent=2)
    bake_labels()

    # ambient (always-on) variant
    abg = make_bg_ambient()
    ah = make_hand_ambient(112, 7.8, tail=7, shape="blade")
    am = make_hand_ambient(162, 5.2, tail=8, shape="blade")
    save(abg, named("bg_ambient"))
    hands_amb = {
        "hour": save_hand(ah, "hand_hour_ambient" + sfx),
        "minute": save_hand(am, "hand_minute_ambient" + sfx),
    }
    with open(os.path.join(OUT, "hands_ambient" + sfx + ".json"), "w", encoding="utf-8") as fh:
        json.dump(hands_amb, fh, indent=2)
    save(compose_ambient(abg, ah, am), named("preview_ambient"))

    with open(os.path.join(OUT, "layout" + sfx + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"layout": LAYOUT, "labels": {n: {"x": x, "y": y, "size": s}
                                                for n, _t, s, _c, _ls, x, y in LABELS}}, fh, indent=2)

    # text colours for the watch face generator
    def hx(c):
        return "#FF%02X%02X%02X" % c

    with open(os.path.join(OUT, "palette" + sfx + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"name": PALETTE_NAME, "cyan": hx(CYAN), "magenta": hx(MAGENTA),
                   "violet": hx(Violet), "dim": "#FF8FB6C9", "time": hx(CYAN),
                   "time_alt": "#FFEAF7FF"}, fh, indent=2)
    print("layout exported | palette", PALETTE_NAME)
