"""Debug helper: dumps the node tree of a .wfs sample project.

Usage:
    python tools\debug_dump_nodes.py <name.wfs> [--full]

Without --full it prints one line per node (type, name, geometry). With --full
it prints the raw JSON of the scene, which is what you need to clone a template.
"""
import json
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import zipfile

SAMPLES = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
           r"\tools\wfs_samples")


def walk(node, depth=0):
    cats = node.get("categories") or {}
    pos = (cats.get("placement", {}).get("properties", {})
           .get("position", {}).get("value", {}))
    dim = (cats.get("dimension", {}).get("properties", {}))
    w = dim.get("width", {}).get("value")
    h = dim.get("height", {}).get("value")
    print("%s%s name=%r x=%s y=%s w=%s h=%s" % (
        "  " * depth, node.get("type"), node.get("name"),
        pos.get("x"), pos.get("y"), w, h))
    for ch in node.get("child") or []:
        walk(ch, depth + 1)


def main():
    name = sys.argv[1]
    path = name if os.path.isabs(name) else os.path.join(SAMPLES, name)
    with zipfile.ZipFile(path) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))
    if "--full" in sys.argv:
        print(json.dumps(model["scene"], ensure_ascii=False, indent=1))
    else:
        print("settings:", {k: model["settings"].get(k) for k in
                            ("width", "height", "clockType", "shape")})
        for scene in model["scene"]:
            walk(scene)


if __name__ == "__main__":
    main()
