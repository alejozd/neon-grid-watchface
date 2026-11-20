"""Builds a Watch Face Studio project (.wfs) from the Neon Grid art.

A .wfs file is a ZIP with a very specific layout:
    honeyface.json              <- MUST be the first entry: the project model
    latest_preview.png          <- preview shown in the project list
    res/ ...                    <- directory entries, then the layers

WFS cannot import a WFF project, so this script does *template surgery* on the
sample projects that ship with Watch Face Studio: it keeps the node structure of
working samples and replaces art, geometry and data bindings with ours.

Layer stack (bottom to top), mirroring the WFF watch face in watchface/:
    bg                     image
    Gauges                 two circular progress bars (battery, step goal)
    Hands                  analog clock with the three hands
    HUD labels             baked label PNGs (MSG / BAT / BPM / PASOS / EVENT)
    HUD data               texts and the date
    Tap zones              invisible shapes carrying <Launch> actions

Everything is authored at 480 px (design/out/*.json) and scaled to the 450 px
canvas WFS 1.9.9 accepts.
"""
import json
import os
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design", "out")
OUT = os.path.join(ROOT, "wfs-project", "NeonGrid.wfs")

SAMPLES = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
           r"\tools\wfs_samples")
SAMPLE = os.path.join(SAMPLES, "Minimal_classic_W_B.wfs")      # scene + hands
DATA_SAMPLE = os.path.join(SAMPLES, "Weather_health_D_C.wfs")  # text + gauges
CANVAS = 450          # WFS 1.9.9 only accepts 450x450 projects
DESIGN_CANVAS = 480   # the art is authored at 480
SCALE = CANVAS / DESIGN_CANVAS
DRAW = "res/drawable-nodpi"
LABEL_ID = "ID_MINIMAL_CLASSIC_W_B"   # id already used by buildData.appLabel

# WFS ships system fonts only; SplineSansMono is the monospace one.
FONT = "SplineSansMono-Bold"

# ---------------------------------------------------------------------------
# Taps. Targets verified one by one on the Galaxy Watch 6 (see docs/HANDOFF.md):
# the system shortcuts HEALTH_HEART_RATE / CALENDAR open nothing on this watch,
# so every app is opened by package (or package/activity) instead.
# ---------------------------------------------------------------------------
TAP_TARGETS = [
    # (label, x, y, w, h, appId, customAppId)
    ("ID_TAP_WEATHER", 196, 52, 90, 54,
     "com.samsung.android.watch.weather", None),          # Clima
    ("ID_TAP_MSG", 124, 160, 70, 56, "com.whatsapp", None),  # WhatsApp
    ("ID_TAP_BATTERY", 44, 206, 84, 52, "BATTERY_STATUS", None),  # Ajustes bateria
    ("ID_TAP_HEART", 60, 272, 76, 52,
     "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app."
     "heartrate.view.HeartRateActivity", None),           # pantalla Medir
    ("ID_TAP_STEPS", 326, 228, 84, 52,
     "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app."
     "steps.view.StepsActivity", None),                   # pantalla Pasos
    ("ID_TAP_DATE", 146, 352, 190, 46,
     "com.samsung.android.calendar", None),               # Calendario (dia)
]

TAP_STRINGS = {
    "ID_TAP_WEATHER": "Weather",
    "ID_TAP_MSG": "Messages",
    "ID_TAP_BATTERY": "Battery",
    "ID_TAP_HEART": "Heart rate",
    "ID_TAP_STEPS": "Steps",
    "ID_TAP_DATE": "Calendar",
}

# Horizontal anchoring copied from tools/gen_watchface.py (verified on device):
# the boxes span a whole edge of the canvas so alignment is predictable.
ALIGN = {
    "time": ("end", 326),
    "ampm": ("start", 346),
    "sec": ("start", 350),
    "date": ("center", DESIGN_CANVAS / 2),
    "temp": ("center", DESIGN_CANVAS / 2),
    "cond": ("center", DESIGN_CANVAS / 2),
    "tminmax": ("center", DESIGN_CANVAS / 2),
    "msg_v": ("start", 132),
    "bat_v": ("start", 52),
    "hr_v": ("start", 72),
    "steps_v": ("end", 404),
    "steps_pct": ("end", 404),
}

# Weather condition labels, same mapping as the Condition block of the WFF
# project (WEATHER.CONDITION_NAME renders empty on this firmware, so the label
# is derived from the integer code with a nested ternary).
CONDITION_LABELS = [
    ([1, 8], "DESPEJADO"),
    ([2, 14], "NUBLADO"),
    ([4, 6, 12], "LLUVIA"),
    ([5, 7, 11], "NIEVE"),
    ([3, 13], "NIEBLA"),
    ([9], "TORMENTA"),
    ([10], "AGUANIEVE"),
    ([15], "VIENTO"),
]


def condition_expression():
    """A nested ternary per weather code.

    `||` is only supported by the Watch Face Format runtime, not by the editor's
    expression evaluator (a `||` chain renders the fallback), so every value gets
    its own comparison.
    """
    expr = '"-"'
    for values, label in reversed(CONDITION_LABELS):
        for value in reversed(values):
            expr = '([WTHR_COND]==%d?"%s":%s)' % (value, label, expr)
    return expr


def new_id():
    return str(uuid.uuid4()).replace("-", "_")


def find(nodes, typ):
    for n in nodes:
        if n.get("type") == typ:
            return n
        if n.get("child"):
            r = find(n["child"], typ)
            if r:
                return r
    return None


def walk(node):
    yield node
    for ch in node.get("child") or []:
        yield from walk(ch)


def find_named(nodes, name):
    for node in walk({"child": nodes}):
        if node.get("name") == name:
            return node
    return None


def reid(node):
    node["id"] = new_id()
    cl = node.get("conditionalLine")
    if isinstance(cl, dict):
        cl["id"] = node["id"]
        for item in cl.get("timeItems") or []:
            item["id"] = new_id()
    for ch in node.get("child") or []:
        reid(ch)


def set_geom(node, x, y, w, h, pivot=None):
    cats = node.setdefault("categories", {})
    place = cats.setdefault("placement", {"type": "placement", "properties": {}})
    place.setdefault("properties", {}).setdefault("position", {})["value"] = {"x": x, "y": y}
    dim = cats.setdefault("dimension", {"type": "dimension", "properties": {}})
    props = dim.setdefault("properties", {})
    props.setdefault("width", {})["value"] = w
    props.setdefault("height", {})["value"] = h
    if pivot is not None:
        rot = cats.setdefault("rotate", {"type": "rotate", "properties": {}})
        rot.setdefault("properties", {}).setdefault("pivot", {})["value"] = {
            "x": round(pivot[0] * 100, 4),
            "y": round(pivot[1] * 100, 4),
        }


def set_image(node, filename):
    props = node["categories"].setdefault("image", {"type": "image", "properties": {}})["properties"]
    props.setdefault("image", {})["value"] = "file://%s/%s" % (DRAW, filename)
    props.setdefault("displayName", {})["value"] = filename
    props.setdefault("referenceInfo", {})["value"] = 0


def rgba(hexstr):
    """'#AARRGGBB' or '#RRGGBB' -> WFS colour object."""
    h = hexstr.lstrip("#")
    if len(h) == 8:
        a, r, g, b = h[0:2], h[2:4], h[4:6], h[6:8]
    else:
        a, r, g, b = "FF", h[0:2], h[2:4], h[4:6]
    return {"r": int(r, 16), "g": int(g, 16), "b": int(b, 16), "a": int(a, 16)}


def set_color(node, hexstr, expression=None):
    props = node["categories"]["color"]["properties"]
    props["color"]["value"] = rgba(hexstr)
    props["color"].pop("type", None)
    if expression is None:
        props["color"].pop("expression", None)
    else:
        props["color"]["expression"] = expression


# ---------------------------------------------------------------------------
# texts
# ---------------------------------------------------------------------------
# WFS keeps text as a list of segments; `text.value` is the editable template
# (`(expression)` for tags, bare characters for literals).
STRING_TAGS = ("[AMPM]", "[DAY_WEEK_S]", "[DAY_WEEK_F]", "[MON_S]", "[MON_F]")


def text_segments(parts):
    """[(expr|str, value)] -> (display string, WFS expression list)."""
    display, segments = [], []
    for kind, value in parts:
        if kind == "expr":
            display.append("(%s)" % value)
            is_string = any(t in value for t in STRING_TAGS)
            segments.append({
                "format": "expression",
                "value": value,
                "result": "AM" if is_string else 0,
                "resultFormat": "string" if is_string else "number",
            })
        else:
            display.append(value)
            segments.append({"format": "string", "value": value})
    return "".join(display), segments


def set_text(node, parts):
    display, segments = text_segments(parts)
    props = node["categories"]["text"]["properties"]
    props["text"]["value"] = display
    props["text"]["expression"] = segments


def tidy_text(node, size, align, color, letter_spacing=0.0, hexcolor=None):
    """Forces a ttf style (the samples use bitmap fonts we do not ship)."""
    appear = node["categories"]["textAppearance"]["properties"]
    appear["font"]["value"] = {"type": "system", "value": FONT,
                               "name": FONT, "file": FONT + ".ttf", "height": size}
    appear["ttf"]["value"] = {"type": "system", "value": FONT,
                              "name": FONT, "file": FONT + ".ttf", "height": size}
    appear["bitmapFont"]["value"] = {"type": "bitmap", "value": "Bitmap font 1",
                                     "name": "Bitmap font 1"}
    appear["applyBitmapFontSize"]["value"] = False
    appear["textSize"]["value"] = size
    appear["textAlign"]["value"] = align
    appear["letterSpacing"]["value"] = letter_spacing
    appear["ellipsis"]["value"] = False
    appear["referenceInfo"] = 0
    style = node["categories"].get("style", {}).get("properties")
    if style is not None:
        style["ttfs"] = []
        style["bitmapFonts"] = []
        node["categories"]["style"]["styleType"] = "ttfs"
    curved = node["categories"].get("curvedText", {}).get("properties")
    if curved is not None:
        curved["enabled"]["value"] = False
    set_color(node, color)


def place_text(node, key, size, layout):
    align, anchor = ALIGN[key]
    height = size * 1.45
    y = layout[key]["y"] * SCALE - height / 2
    if align == "center":
        x, w = 0, CANVAS
    elif align == "start":
        x = anchor * SCALE
        w = CANVAS - x
    else:  # end
        x, w = 0, anchor * SCALE
    set_geom(node, round(x, 3), round(y, 3), round(w, 3), round(height, 3))
    return align


def build_texts(text_tpl, layout, palette):
    """All the HUD texts, in the order they should be drawn."""
    def tpl(name, key, size, color, parts, aod=False, ls_key=None):
        node = json.loads(json.dumps(text_tpl))
        reid(node)
        node["name"] = name
        node["visible"] = True
        node["visibleOnAOD"] = aod
        node["applyThemeColor"] = False
        align = place_text(node, key, size * SCALE, layout)
        ls = layout[key].get("ls", 0.0) if ls_key is None else layout[ls_key].get("ls", 0.0)
        tidy_text(node, round(size * SCALE, 3), align, color,
                  letter_spacing=round(ls / size * 100, 3))
        set_text(node, parts)
        return node

    return [
        # seconds + AM/PM sit right of the big time
        tpl("sec", "sec", layout["sec"]["size"], palette["cyan"],
            [("expr", "[SEC_Z]")]),
        # 12-hour clock: hour without leading zero, minutes zero-padded ("7:05")
        tpl("time", "time", layout["time"]["size"], palette["time"],
            [("expr", "[HOUR_1_12]"), ("str", ":"), ("expr", "[MIN_Z]")], aod=True),
        tpl("ampm", "ampm", layout["ampm"]["size"], palette["cyan"],
            [("expr", "[AMPM]")]),
        tpl("date", "date", layout["date"]["size"], palette["magenta"],
            [("expr", "[DAY_WEEK_S]"), ("str", " "), ("expr", "[DAY_1_31_Z]"),
             ("str", " "), ("expr", "[MON_S]")], aod=True),
        tpl("temp", "temp", layout["temp"]["size"], palette["cyan"],
            [("expr", "[WTHR_TEM]"), ("str", "\u00b0")]),
        tpl("cond", "cond", layout["cond"]["size"], palette["dim"],
            [("expr", condition_expression())]),
        tpl("tminmax", "tminmax", layout["tminmax"]["size"], palette["dim"],
            [("expr", "[WTHR_DAY_TEM_HIGH]"), ("str", "\u00b0 / "),
             ("expr", "[WTHR_DAY_TEM_LOW]"), ("str", "\u00b0")]),
        tpl("msg_v", "msg_v", layout["msg_v"]["size"], palette["magenta"],
            [("expr", "[UNREAD_NC]")]),
        tpl("bat_v", "bat_v", layout["bat_v"]["size"], palette["cyan"],
            [("expr", "[BATT_PER]"), ("str", "%")]),
        tpl("hr_v", "hr_v", layout["hr_v"]["size"], palette["magenta"],
            [("expr", "[HR]")]),
        tpl("steps_v", "steps_v", layout["steps_v"]["size"], palette["cyan"],
            [("expr", "[SC]")]),
        tpl("steps_pct", "steps_pct", layout["steps_pct"]["size"], palette["dim"],
            [("expr", "[SC_PER]"), ("str", "%")]),
    ]


# ---------------------------------------------------------------------------
# gauges (real meters, like the WFF arcs)
# ---------------------------------------------------------------------------
GAUGES = [
    # (name, expression, startAngle, sweepAngle, colour)
    ("gauge_battery", "[BATT_PER]", 246, 48, "cyan"),
    ("gauge_steps", "[SC_PER]", 300, 40, "magenta"),
]


def build_gauges(tpl, palette):
    out = []
    for name, expression, start, sweep, color_key in GAUGES:
        node = json.loads(json.dumps(tpl))
        reid(node)
        node["name"] = name
        node["visible"] = True
        node["visibleOnAOD"] = False
        node["applyThemeColor"] = False
        set_geom(node, 0, 0, CANVAS, CANVAS)
        props = node["categories"]
        props["dimension"]["properties"]["thickness"]["value"] = round(4 * SCALE, 3)
        props["dimension"]["properties"]["cap"]["value"] = "round"
        props["progressBarType"]["properties"]["barType"]["value"] = "circular"
        rng = props["range"]["properties"]
        rng["value"] = {"value": 0, "expression": expression}
        rng["min"]["value"] = 0
        rng["max"]["value"] = 100
        rng["circularRangeStartAngle"]["value"] = start
        rng["circularRangeSweepAngle"]["value"] = sweep
        rng["circularDirection"]["value"] = "CW"
        size = round(410 * SCALE, 3)
        rng["circularWidth"]["value"] = size
        rng["circularHeight"]["value"] = size
        rng["circularCenterX"]["value"] = CANVAS / 2
        rng["circularCenterY"]["value"] = CANVAS / 2
        set_color(node, palette[color_key])
        color = props["color"]["properties"]
        color["colorType"] = {"value": "solid"}
        if "backgroundOpacity" in color:
            color["backgroundOpacity"]["value"] = 20     # dim track behind the bar
        out.append(node)
    return out


# ---------------------------------------------------------------------------
# labels + tap zones
# ---------------------------------------------------------------------------
def build_labels(tpl, labels_json):
    out = []
    for name, meta in labels_json.items():
        node = json.loads(json.dumps(tpl))
        reid(node)
        node["name"] = name
        node["visible"] = True
        node["visibleOnAOD"] = False
        node["applyThemeColor"] = False
        set_geom(node, round(meta["x"] * SCALE, 3), round(meta["y"] * SCALE, 3),
                 round(meta["w"] * SCALE, 3), round(meta["h"] * SCALE, 3))
        set_image(node, "neon_%s.png" % name)
        out.append(node)
    return out


def set_action(node, app_id, custom_app_id, string_res_id):
    act = node["categories"]["action"]
    props = act["properties"]
    value = {
        "type": "openApp",
        "display": "Open App",
        "value": {
            "type": "custom" if custom_app_id is not None else "system",
            "appId": app_id,
            "customAppId": custom_app_id or "",
            "stringResId": string_res_id,
        },
    }
    props["enabled"]["value"] = True
    props["interaction"]["value"] = "tap"
    props["actionType"]["value"] = "openApp"
    props["action"]["value"] = value
    props["actionOpenApp"]["value"] = json.loads(json.dumps(value["value"]))


def build_tap_zones(tpl):
    out = []
    for res_id, x, y, w, h, app_id, custom in TAP_TARGETS:
        node = json.loads(json.dumps(tpl))
        reid(node)
        node["name"] = "tap_" + res_id.replace("ID_TAP_", "").lower()
        node["visible"] = True
        node["visibleOnAOD"] = False
        node["applyThemeColor"] = False
        set_geom(node, round(x * SCALE, 3), round(y * SCALE, 3),
                 round(w * SCALE, 3), round(h * SCALE, 3))
        # almost transparent: it only exists to catch taps
        set_color(node, "#02000000")
        set_action(node, app_id, custom, res_id)
        out.append(node)
    return out


# ---------------------------------------------------------------------------
# hands (unchanged convention: tall narrow slice, 50%/50% pivot)
# ---------------------------------------------------------------------------
HAND_PAD = 6          # transparent margin around the hand slice, in 480-space


def hand_crop(geo):
    """Horizontal slice of the 480 canvas that contains the hand, scaled to CANVAS."""
    x0 = max(0, int(geo["x"]) - HAND_PAD)
    x1 = min(DESIGN_CANVAS, int(geo["x"]) + int(geo["w"]) + HAND_PAD)
    return {
        "x": int(round(x0 * SCALE)),
        "w": max(1, int(round((x1 - x0) * SCALE))),
        "crop": (x0, 0, x1, DESIGN_CANVAS),
        "png": (max(1, int(round((x1 - x0) * SCALE))), CANVAS),
    }


# ---------------------------------------------------------------------------
# event complication slot
# ---------------------------------------------------------------------------
# A complicationSlot is the heaviest node in the model: `complicationTypes`
# holds one template list per complication type and per layout, and the
# `categories.shortText/shortTitle/icon` categories point (linkedElementId) at
# the two or three "live" elements in `child`. The template is the `line` slot
# of Large_letters_D_C.wfs, which is the only sample with a two-line layout.
SLOT_SAMPLE = os.path.join(SAMPLES, "Large_letters_D_C.wfs")
SLOT_NAME = "Line Complication"
EVENT_BOX = (262, 156, 156, 54)      # design space, same as the WFF slot


def reid_slot(slot):
    """Unique ids everywhere, then relink clipper and per-field references."""
    reid(slot)
    for layout in slot["complicationTypes"]["shortText"]["layouts"].values():
        for element in layout.get("elements") or []:
            reid(element)
    by_field = {}
    for child in slot.get("child") or []:
        by_field[child.get("complicationField")] = child["id"]
    slot["clipper"] = by_field.get("clipper", "")
    for field, cat in (slot.get("categories") or {}).items():
        props = (cat or {}).get("properties") or {}
        if "linkedElementId" in props:
            props["linkedElementId"]["value"] = by_field.get(field, "")


def build_event_slot(layout, palette):
    with zipfile.ZipFile(SLOT_SAMPLE) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))
    tpl = find_named(model["scene"][0]["child"], SLOT_NAME)
    if tpl is None:
        raise SystemExit("template slot not found: " + SLOT_NAME)

    slot = json.loads(json.dumps(tpl))
    x, y, w, h = [round(v * SCALE, 3) for v in EVENT_BOX]
    set_geom(slot, x, y, w, h)
    slot["name"] = "event_slot"
    slot["visible"] = True
    slot["visibleOnAOD"] = False
    slot["applyThemeColor"] = False

    # two lines: title (dim, small) over the event text (violet)
    text_tpl = find_named([c for c in slot["child"]
                           if c.get("complicationField") == "shortText"], "Steps")
    title_tpl = None
    for lay in slot["complicationTypes"]["shortText"]["layouts"].values():
        for element in lay.get("elements") or []:
            if element.get("complicationField") == "shortTitle":
                title_tpl = element
    if text_tpl is None or title_tpl is None:
        raise SystemExit("slot template lacks the text/title elements")

    def line(source, field, box, size, color, name):
        node = json.loads(json.dumps(source))
        reid(node)
        node["name"] = name
        node["complicationField"] = field
        node["visible"] = True
        node["visibleOnAOD"] = False
        node["applyThemeColor"] = False
        lx, ly, lw, lh = [round(v * SCALE, 3) for v in box]
        set_geom(node, lx, ly, lw, lh)
        tidy_text(node, round(size * SCALE, 3), "center", color)
        return node

    title = line(title_tpl, "shortTitle", (0, 2, w / SCALE, 22),
                 12, palette["dim"], "event_title")
    text = line(text_tpl, "shortText", (0, 24, w / SCALE, 27),
                16, palette["violet"], "event_text")

    # the slot bound rectangle comes first, then the two texts (no icon: the
    # "EVENT" word is already baked into the background)
    bound = [c for c in slot["child"] if c.get("complicationField") == "clipper"][0]
    bound = json.loads(json.dumps(bound))
    reid(bound)
    slot["child"] = [bound, title, text]
    set_geom(bound, 0, 0, w, h)

    # every layout shows the same two lines (icon variants drop the icon)
    type_def = slot["complicationTypes"]["shortText"]
    for lname, lay in type_def["layouts"].items():
        keeps = []
        for element in lay.get("elements") or []:
            field = element.get("complicationField")
            if field == "clipper":
                keeps.append(json.loads(json.dumps(bound)))
            elif field == "shortTitle":
                keeps.append(json.loads(json.dumps(title)))
            elif field == "shortText":
                keeps.append(json.loads(json.dumps(text)))
            # icons are dropped; anything else (the sample carries an extra,
            # unbound text used for its preview) would duplicate a line
        for element in keeps:
            reid(element)
        lay["elements"] = keeps
        lay["activated"] = True
    type_def["activated"] = True
    slot["complicationTypeOrder"] = ["shortText"]
    slot["fixedComplicationType"] = "shortText"

    preview = slot["categories"]["complicationSlotPreview"]["properties"]
    preview["selectedComplicationType"]["value"] = "shortText"
    preview["layout"] = {"value": "shortTextTitle", "type": "shortText"}
    preview["defaultProvider"]["value"] = "NEXT_EVENT"
    preview["fixedProvider"]["value"] = "NEXT_EVENT"
    preview["isFixed"]["value"] = False

    reid_slot(slot)
    return slot


def load_layout():
    with open(os.path.join(DESIGN, "layout.json"), encoding="utf-8") as fh:
        return json.load(fh)["layout"]


def load_palette():
    with open(os.path.join(DESIGN, "palette.json"), encoding="utf-8") as fh:
        return json.load(fh)


def build_model():
    with zipfile.ZipFile(SAMPLE) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))
    with zipfile.ZipFile(DATA_SAMPLE) as z:
        data_model = json.loads(z.read("honeyface.json").decode("utf-8"))

    scene = model["scene"][0]
    children = scene["child"]
    bg_tpl = find(children, "image")
    clock_tpl = find(children, "analogClock")
    touch_tpl = find_named(children, "Touch area_Calendar link")
    hands = {t: find(clock_tpl["child"], t)
             for t in ("analogHandHour", "analogHandMin", "analogHandSec")}

    data_children = data_model["scene"][0]["child"]
    text_tpl = find(data_children, "text")
    gauge_tpl = find(data_children, "progressBar")

    with open(os.path.join(DESIGN, "hands.json"), encoding="utf-8") as fh:
        hand_geo = json.load(fh)
    with open(os.path.join(DESIGN, "labels", "labels.json"), encoding="utf-8") as fh:
        labels_json = json.load(fh)
    layout = load_layout()
    palette = load_palette()

    bg = json.loads(json.dumps(bg_tpl))
    reid(bg)
    bg["name"] = "bg"
    bg["visible"] = True
    bg["visibleOnAOD"] = False
    set_geom(bg, 0, 0, CANVAS, CANVAS, pivot=(0, 0))
    set_image(bg, "neon_bg.png")

    clock = json.loads(json.dumps(clock_tpl))
    reid(clock)
    clock["name"] = "Hands"
    clock["visible"] = True
    clock["visibleOnAOD"] = True
    clock["child"] = []

    for typ, key, fname in (
        ("analogHandHour", "hour", "neon_hand_hour.png"),
        ("analogHandMin", "minute", "neon_hand_minute.png"),
        ("analogHandSec", "second", "neon_hand_second.png"),
    ):
        h = json.loads(json.dumps(hands[typ]))
        reid(h)
        g = hand_geo[key]
        h["name"] = key
        h["visible"] = True
        h["visibleOnAOD"] = typ != "analogHandSec"
        # WFS stretches the image to the node box, and the samples use a tall,
        # narrow image (40x450 on a 450 canvas) whose box matches the image size
        # and whose 50%/50% pivot lands on the dial centre. So the box is the
        # hand's horizontal slice of the canvas: full height, hand width.
        crop = hand_crop(g)
        set_geom(h, crop["x"], 0, crop["w"], CANVAS, pivot=(0.5, 0.5))
        set_image(h, fname)
        # the sample's hour hand is tinted black (it is the AOD variant); a white
        # tint leaves the artwork untouched
        set_color(h, "#FFFFFFFF")
        clock["child"].append(h)

    gauges = build_gauges(gauge_tpl, palette)
    labels = build_labels(bg_tpl, labels_json)
    texts = build_texts(text_tpl, layout, palette)
    event_slot = build_event_slot(layout, palette)
    taps = build_tap_zones(touch_tpl)

    # z-order: background, meters, hands, labels, data, event slot, tap zones
    scene["child"] = [bg] + gauges + [clock] + labels + texts + [event_slot] + taps
    scene["name"] = "Root"

    # every container must agree with the canvas, otherwise WFS reports
    # "Unsupported project size": the root group and the analog clock keep the
    # 450x450 geometry they had in the sample.
    set_geom(scene, 0, 0, CANVAS, CANVAS, pivot=(0, 0))
    set_geom(clock, 0, 0, CANVAS, CANVAS)

    st = model["settings"]
    st["width"] = CANVAS
    st["height"] = CANVAS
    st["clockType"] = "analog"
    st["shape"] = "circle"
    st["tickPerSecond"] = 1
    # the sample ships a bitmap font whose glyphs we do not copy over
    st["bitmapFonts"] = {}
    st["customFonts"] = []
    st["defaultFont"] = {"type": "system", "value": FONT, "name": FONT,
                         "file": FONT + ".ttf"}
    st["defaultBitmapFont"] = {"type": "system", "value": "SYNC_TO_DEVICE",
                               "name": "Sync to Device"}

    # keep string ids consistent with buildData.appLabel
    strings = {LABEL_ID: "Neon Grid"}
    strings.update(TAP_STRINGS)
    model["stringResource"] = {"default": strings}
    model["buildData"]["packageName"] = "com.relog.neongrid"
    model["buildData"]["appVersion"] = "1.0.0"
    model["buildData"]["appVersionCode"] = 1
    model["buildData"]["watchType"] = "Analog"
    model["buildData"]["appLabel"] = {"stringResId": LABEL_ID}
    return model


def strings_xml(model):
    """res/values/strings.xml for the project's string table."""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    for key, value in sorted(model["stringResource"]["default"].items()):
        lines.append('  <string name="%s">%s</string>' % (key, value))
    lines.append("</resources>")
    return "\n".join(lines).encode("utf-8")


def main():
    model = build_model()
    with open(os.path.join(DESIGN, "device-render.png"), "rb") as fh:
        preview = fh.read()

    shapes = ('<?xml version="1.0" encoding="utf-8"?>\n<WatchFaces>\n'
              '  <WatchFace shape="CIRCLE" width="%d" height="%d" file="@raw/watchface"/>\n'
              '</WatchFaces>\n' % (CANVAS, CANVAS)).encode("utf-8")

    strings_xml_bytes = strings_xml(model)

    art = {
        "neon_bg.png": os.path.join(DESIGN, "bg.png"),
        "neon_hand_hour.png": os.path.join(DESIGN, "hand_hour.png"),
        "neon_hand_minute.png": os.path.join(DESIGN, "hand_minute.png"),
        "neon_hand_second.png": os.path.join(DESIGN, "hand_second.png"),
    }
    with open(os.path.join(DESIGN, "labels", "labels.json"), encoding="utf-8") as fh:
        for name, meta in json.load(fh).items():
            art["neon_%s.png" % name] = os.path.join(DESIGN, "labels", meta["file"])
    for src in art.values():
        if not os.path.exists(src):
            raise SystemExit("missing art: " + src)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(SAMPLE) as zin, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        # 1) honeyface.json MUST come first
        zout.writestr("honeyface.json", json.dumps(model, ensure_ascii=False))
        zout.writestr("latest_preview.png", preview)

        # 2) walk the sample entries, keeping its order and directory entries
        for item in zin.infolist():
            name = item.filename
            if name in ("honeyface.json", "latest_preview.png"):
                continue
            if name.startswith(DRAW + "/") and name.endswith(".png"):
                if name.endswith("preview.png") or name.endswith("preview_circular.png"):
                    zout.writestr(item, preview)
                continue  # other sample art is dropped
            if name == "res/xml/watch_face_shapes.xml":
                zout.writestr(item, shapes)
                continue
            if name == "res/values/strings.xml":
                zout.writestr(item, strings_xml_bytes)
                continue
            if item.is_dir():
                zout.writestr(item, b"")
                continue
            zout.writestr(item, zin.read(name))

        # 3) our layers
        for dst, src in art.items():
            with open(src, "rb") as fh:
                zout.writestr("%s/%s" % (DRAW, dst), fh.read())

    print("wrote", OUT, "%.1f KB" % (os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
