"""Builds a Watch Face Studio project (.wfs) from the Neon Grid art.

A .wfs file is a ZIP with:
    honeyface.json                  <- the project model (scene graph)
    latest_preview.png              <- preview shown in the project list
    res/drawable-nodpi/*.png        <- the layers
    res/values/strings.xml

WFS cannot import a WFF project, so this script performs *template surgery* on one
of the sample projects that ship with Watch Face Studio: it keeps the node
structure of a working analog project and replaces the art and the geometry with
ours. The result opens with File > Open Project in WFS.
"""
import json
import os
import shutil
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design", "out")
OUT = os.path.join(ROOT, "wfs-project", "NeonGrid.wfs")

SAMPLE = r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio\tools\wfs_samples\Minimal_classic_W_B.wfs"
CANVAS = 480
DRAW = "res/drawable-nodpi"


def new_id():
    return str(uuid.uuid4()).replace("-", "_")


def load_sample():
    with zipfile.ZipFile(SAMPLE) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))
        names = z.namelist()
    return model, names


def find(nodes, typ):
    for n in nodes:
        if n.get("type") == typ:
            return n
        if n.get("child"):
            r = find(n["child"], typ)
            if r:
                return r
    return None


def collect(nodes, typ, out=None):
    out = [] if out is None else out
    for n in nodes:
        if n.get("type") == typ:
            out.append(n)
        if n.get("child"):
            collect(n["child"], typ, out)
    return out


def reid(node):
    """Gives the node (and its conditionalLine) a fresh unique id, recursively."""
    node["id"] = new_id()
    cl = node.get("conditionalLine")
    if isinstance(cl, dict):
        cl["id"] = node["id"]
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


def main():
    model, _ = load_sample()
    scene = model["scene"][0]
    children = scene["child"]

    bg_tpl = find(children, "image")
    clock_tpl = find(children, "analogClock")
    hands = {h["type"]: h for h in collect(clock_tpl["child"], "analogHandHour")}
    for t in ("analogHandHour", "analogHandMin", "analogHandSec"):
        hands[t] = find(clock_tpl["child"], t)

    with open(os.path.join(DESIGN, "hands.json"), encoding="utf-8") as fh:
        hand_geo = json.load(fh)

    # ---- background image node ----
    bg = json.loads(json.dumps(bg_tpl))
    reid(bg)
    bg["name"] = "bg"
    bg["visible"] = True
    bg["visibleOnAOD"] = False
    bg.pop("conditionalLine", None)
    set_geom(bg, 0, 0, CANVAS, CANVAS, pivot=(0, 0))
    set_image(bg, "neon_bg.png")

    # ---- analog clock with our three hands ----
    clock = json.loads(json.dumps(clock_tpl))
    reid(clock)
    clock["name"] = "Hands"
    clock["visible"] = True
    clock["visibleOnAOD"] = True
    clock["child"] = []

    mapping = [
        ("analogHandHour", "hour", "neon_hand_hour.png"),
        ("analogHandMin", "minute", "neon_hand_minute.png"),
        ("analogHandSec", "second", "neon_hand_second.png"),
    ]
    for typ, key, fname in mapping:
        h = json.loads(json.dumps(hands[typ]))
        reid(h)
        g = hand_geo[key]
        h["name"] = key
        h["visible"] = True
        h["visibleOnAOD"] = typ != "analogHandSec"
        h.pop("conditionalLine", None)
        set_geom(h, int(g["x"]), int(g["y"]), int(g["w"]), int(g["h"]),
                 pivot=(g["pivotX"], g["pivotY"]))
        set_image(h, fname)
        clock["child"].append(h)

    scene["child"] = [bg, clock]
    scene["name"] = "Root"

    # ---- project settings ----
    st = model["settings"]
    st["width"] = CANVAS
    st["height"] = CANVAS
    st["clockType"] = "analog"
    st["shape"] = "circle"
    st["tickPerSecond"] = 1
    # the sample ships a bitmap font whose glyph PNGs we do not copy over
    st["bitmapFonts"] = {}
    st["customFonts"] = []

    model["buildData"]["packageName"] = "com.relog.neongrid"
    model["buildData"]["appVersion"] = "1.0.0"
    model["buildData"]["appVersionCode"] = 1
    model["buildData"]["watchType"] = "Analog"

    # ---- write the .wfs ----
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(SAMPLE) as zin, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name = item.filename
            if name in ("honeyface.json", "latest_preview.png",
                        "res/drawable-nodpi/preview.png",
                        "res/drawable-nodpi/preview_circular.png",
                        "res/values/strings.xml",
                        "res/xml/watch_face_shapes.xml"):
                continue
            if name.startswith("res/drawable-nodpi/"):
                continue  # drop the sample art
            if name.endswith("/") or item.is_dir():
                continue
            zout.writestr(name, zin.read(name))

        zout.writestr("honeyface.json", json.dumps(model, ensure_ascii=False))

        preview = os.path.join(DESIGN, "device-render.png")
        if not os.path.exists(preview):
            preview = os.path.join(DESIGN, "preview_full.png")
        with open(preview, "rb") as fh:
            data = fh.read()
        zout.writestr("latest_preview.png", data)
        zout.writestr("%s/preview.png" % DRAW, data)
        zout.writestr("%s/preview_circular.png" % DRAW, data)

        art = {
            "neon_bg.png": os.path.join(DESIGN, "bg.png"),
            "neon_hand_hour.png": os.path.join(DESIGN, "hand_hour.png"),
            "neon_hand_minute.png": os.path.join(DESIGN, "hand_minute.png"),
            "neon_hand_second.png": os.path.join(DESIGN, "hand_second.png"),
        }
        for dst, src in art.items():
            if not os.path.exists(src):
                raise SystemExit("missing art: " + src)
            with open(src, "rb") as fh:
                zout.writestr("%s/%s" % (DRAW, dst), fh.read())

        # the sample declares a 450 canvas in its generated shapes file: rewrite it
        zout.writestr(
            "res/xml/watch_face_shapes.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<WatchFaces>\n'
            '  <WatchFace shape="CIRCLE" width="%d" height="%d" file="@raw/watchface"/>\n'
            '</WatchFaces>\n' % (CANVAS, CANVAS))

        zout.writestr("res/values/strings.xml",
                      '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                      '    <string name="ID_APP_NAME">Neon Grid</string>\n</resources>\n')

    print("wrote", OUT, "%.1f KB" % (os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
