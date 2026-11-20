"""Builds a Watch Face Studio project (.wfs) from the Neon Grid art.

A .wfs file is a ZIP with a very specific layout:
    honeyface.json              <- MUST be the first entry: the project model
    latest_preview.png          <- preview shown in the project list
    res/ ...                    <- directory entries, then the layers

WFS cannot import a WFF project, so this script does *template surgery* on one of
the sample projects that ship with Watch Face Studio: it keeps the node structure
of a working analog project and replaces art and geometry with ours.
"""
import json
import os
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design", "out")
OUT = os.path.join(ROOT, "wfs-project", "NeonGrid.wfs")

SAMPLE = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
          r"\tools\wfs_samples\Minimal_classic_W_B.wfs")
CANVAS = 450          # WFS 1.9.9 only accepts 450x450 projects
DESIGN_CANVAS = 480   # the art is authored at 480
SCALE = CANVAS / DESIGN_CANVAS
DRAW = "res/drawable-nodpi"
LABEL_ID = "ID_MINIMAL_CLASSIC_W_B"   # id already used by buildData.appLabel


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


def reid(node):
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


def build_model():
    with zipfile.ZipFile(SAMPLE) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))

    scene = model["scene"][0]
    children = scene["child"]
    bg_tpl = find(children, "image")
    clock_tpl = find(children, "analogClock")
    hands = {t: find(clock_tpl["child"], t)
             for t in ("analogHandHour", "analogHandMin", "analogHandSec")}

    with open(os.path.join(DESIGN, "hands.json"), encoding="utf-8") as fh:
        hand_geo = json.load(fh)

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
        set_geom(h, int(round(g["x"] * SCALE)), int(round(g["y"] * SCALE)),
                 max(1, int(round(g["w"] * SCALE))), max(1, int(round(g["h"] * SCALE))),
                 pivot=(g["pivotX"], g["pivotY"]))
        set_image(h, fname)
        clock["child"].append(h)

    scene["child"] = [bg, clock]
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
    st["defaultBitmapFont"] = {"type": "system", "value": "SYNC_TO_DEVICE",
                               "name": "Sync to Device"}

    # keep string ids consistent with buildData.appLabel
    model["stringResource"] = {"default": {LABEL_ID: "Neon Grid"}}
    model["buildData"]["packageName"] = "com.relog.neongrid"
    model["buildData"]["appVersion"] = "1.0.0"
    model["buildData"]["appVersionCode"] = 1
    model["buildData"]["watchType"] = "Analog"
    model["buildData"]["appLabel"] = {"stringResId": LABEL_ID}
    return model


def main():
    model = build_model()
    with open(os.path.join(DESIGN, "device-render.png"), "rb") as fh:
        preview = fh.read()

    shapes = ('<?xml version="1.0" encoding="utf-8"?>\n<WatchFaces>\n'
              '  <WatchFace shape="CIRCLE" width="%d" height="%d" file="@raw/watchface"/>\n'
              '</WatchFaces>\n' % (CANVAS, CANVAS)).encode("utf-8")

    art = {
        "neon_bg.png": os.path.join(DESIGN, "bg.png"),
        "neon_hand_hour.png": os.path.join(DESIGN, "hand_hour.png"),
        "neon_hand_minute.png": os.path.join(DESIGN, "hand_minute.png"),
        "neon_hand_second.png": os.path.join(DESIGN, "hand_second.png"),
    }
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
