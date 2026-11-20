"""Sanity checks for the generated .wfs project.

WFS only tells you that something is wrong by failing to open the project (or by
a white window + a trace in renderer.log), so the structural invariants it
relies on are checked here instead:

  * honeyface.json is the first entry and the file ends with the project seal
  * every node carries a conditionalLine with activatedCondition (see HANDOFF
    4.4: without it the React renderer throws on `activatedCondition`)
  * ids are unique and every layer image referenced by a node exists in the ZIP
  * no node references a bitmap font we do not ship
  * geometry agrees with the 450x450 canvas
  * data tags are known tag names
  * actions are well formed

Usage:  python tools\\check_wfs.py [path-to.wfs]
"""
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "wfs-project", "NeonGrid.wfs")
SEAL = b"\x05\x00\x00\x00normal_watchface"
CANVAS = 450
DRAW = "res/drawable-nodpi"

# Every tag the WFS expression engine knows (mined from app.asar; see
# docs/HANDOFF.md). A tag outside this list renders as literal text on device.
KNOWN_TAGS = set("""
UTC_TS MSEC SEC SEC_Z SEC_MSEC SEC_IN_DAY MIN MIN_Z MIN_SEC
HOUR_0_11 HOUR_0_11_Z HOUR_0_11_MIN HOUR_1_12 HOUR_1_12_Z HOUR_1_12_MIN
HOUR_0_23 HOUR_0_23_Z HOUR_0_23_MIN HOUR_1_24 HOUR_1_24_Z HOUR_1_24_MIN
DAY_1_31 DAY_1_31_Z DAY_1_31_HOUR DAY_WEEK DAY_WEEK_F DAY_WEEK_S DAY_IN_YEAR
DAYS_IN_MON MON MON_Z MON_F MON_S MON_DAY YEAR YEAR_S YEAR_MON WEEK_IN_YEAR
WEEK_IN_MON IS_24H IS_DST TMZN_ABB TMZN_OFS TMZN_OFS_WITH_DST TMZN_ID
IS_AFTNOON AMPM_PO AMPM FIRST_DAY_WEEK LANG_LOC
BATT_PER BATT_IS_CHARGE BATT_IS_LOW BATT_TEM_C BATT_TEM_F UNREAD_NC
IS_ACC ACC_X ACC_Y ACC_Z ACC_A_X ACC_A_Y ACC_A_Z ACC_A_XY
HR HR_Z SC SC_GOAL SC_PER HR_IS_MEASURING HR_MEASURE_RESULT HR_LAST_MEASURED_TIME
MOON_PO MOON_TY MOON_TY_NAME
WTHR_IS_AVAIL WTHR_IS_DAY WTHR_TEM_UNIT WTHR_TEM WTHR_DAY_TEM_LOW
WTHR_DAY_TEM_HIGH WTHR_COND WTHR_COND_NAME WTHR_CHANCE_PPTN WTHR_UV_INDEX
WTHR_LAST_UPDATED WTHR_PREVIEW_TYPE
""".split())

TAG_RE = re.compile(r"\[([A-Z0-9_]+)\]")

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def walk(node):
    yield node
    for ch in node.get("child") or []:
        yield from walk(ch)


def leaves(value, out):
    if isinstance(value, dict):
        for v in value.values():
            leaves(v, out)
    elif isinstance(value, list):
        for v in value:
            leaves(v, out)
    elif isinstance(value, str):
        out.append(value)


def check_node(node, names, pattern):
    node_type = node.get("type")
    label = "%s/%r" % (node_type, node.get("name"))
    cl = node.get("conditionalLine")
    if not isinstance(cl, dict):
        err("%s: no conditionalLine (renderer crash)" % label)
    elif not cl.get("activatedCondition"):
        err("%s: conditionalLine.activatedCondition missing" % label)

    if not node.get("id"):
        err("%s: no id" % label)
    names.append(node.get("id"))

    cats = node.get("categories") or {}
    for required in ("placement", "dimension"):
        if required not in cats:
            err("%s: missing %s category" % (label, required))

    place = cats.get("placement", {}).get("properties", {})
    pos = place.get("position", {}).get("value", {})
    dim = cats.get("dimension", {}).get("properties", {})
    w = dim.get("width", {}).get("value")
    h = dim.get("height", {}).get("value")
    if w is not None and (w <= 0 or h is None or h <= 0):
        err("%s: bad box %sx%s" % (label, w, h))
    if (pos.get("x", 0) > CANVAS or pos.get("y", 0) > CANVAS
            or pos.get("x", 0) + (w or 0) < 0 or pos.get("y", 0) + (h or 0) < 0):
        warn("%s: box outside the canvas (%s,%s,%s,%s)"
             % (label, pos.get("x"), pos.get("y"), w, h))

    strings = []
    leaves(cats, strings)
    blob = " ".join(strings)
    for tag in TAG_RE.findall(blob):
        if tag not in KNOWN_TAGS:
            err("%s: unknown tag [%s]" % (label, tag))

    appear = cats.get("textAppearance", {}).get("properties", {})
    font = appear.get("font", {}).get("value", {})
    if isinstance(font, dict) and font.get("type") == "bitmap":
        err("%s: uses bitmap font %r (not shipped)" % (label, font.get("value")))
    style = cats.get("style", {}).get("properties", {})
    if style.get("bitmapFonts"):
        warn("%s: style references bitmap fonts" % label)

    if node_type in ("text", "digitalClock", "date"):
        text = cats.get("text", {}).get("properties", {}).get("text", {})
        if "value" not in text:
            err("%s: no text value" % label)
        if node_type == "text" and "supportExpression" not in cats.get("text", {}):
            warn("%s: text category without supportExpression" % label)

    if node_type == "image":
        image = cats.get("image", {}).get("properties", {}).get("image", {})
        path = image.get("value", "").replace("file://", "")
        if path not in pattern:
            err("%s: image %r not in the archive" % (label, path))

    action = cats.get("action", {}).get("properties", {})
    if action.get("enabled", {}).get("value"):
        value = action.get("action", {}).get("value", {})
        target = value.get("value") or {}
        if value.get("type") != "openApp":
            err("%s: action is not openApp" % label)
        elif not (target.get("appId") or target.get("customAppId")):
            err("%s: action without target" % label)
        elif target.get("type") == "custom" and not target.get("customAppId"):
            err("%s: custom action without customAppId" % label)
        if "actionOpenApp" not in action:
            err("%s: actionOpenApp mirror missing" % label)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT

    raw = open(path, "rb").read()
    if not raw.endswith(SEAL):
        err("file does not end with the 'normal_watchface' seal")

    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if names[0] != "honeyface.json":
            err("honeyface.json is not the first entry (got %r)" % names[0])
        model = json.loads(z.read("honeyface.json").decode("utf-8"))
        archived = set(names)

    st = model["settings"]
    for key in ("width", "height"):
        if st.get(key) != CANVAS:
            err("settings.%s is %r, expected %d" % (key, st.get(key), CANVAS))
    if st.get("bitmapFonts"):
        warn("settings still lists bitmap fonts: %s" % list(st["bitmapFonts"]))

    scene = model["scene"][0]
    sdim = scene["categories"]["dimension"]["properties"]
    if (sdim["width"]["value"], sdim["height"]["value"]) != (CANVAS, CANVAS):
        err("root group is not %dx%d" % (CANVAS, CANVAS))

    ids = []
    counts = {}
    for node in walk(scene):
        check_node(node, ids, archived)
        counts[node.get("type")] = counts.get(node.get("type"), 0) + 1
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        err("%d duplicated ids (e.g. %s)" % (len(dupes), sorted(dupes)[:3]))

    tags = sorted(set(TAG_RE.findall(json.dumps(model["stringResource"]) +
                                    json.dumps(scene))))
    print("file      : %s (%.1f KB)" % (path, os.path.getsize(path) / 1024))
    print("settings  : %s %dx%d, %s" % (st.get("clockType"), st.get("width"),
                                        st.get("height"), st.get("shape")))
    print("layers    : %s" % ", ".join("%s=%d" % kv for kv in sorted(counts.items())))
    print("tags      : %s" % ", ".join(tags))
    print("images    : %d" % len([n for n in archived if n.startswith(DRAW) and n.endswith(".png")]))
    print("strings   : %s" % ", ".join(sorted(model["stringResource"]["default"])))
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    print("RESULT: %d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
