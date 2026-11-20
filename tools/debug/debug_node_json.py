"""Debug helper: prints the full JSON of nodes matching the given names/types.

Usage:
    python tools/debug_node_json.py Minimal_classic_W_B.wfs --name HH --type text --type digitalClock
"""
import argparse
import json
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import zipfile

SAMPLES = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
           r"\tools\wfs_samples")


def walk(node):
    yield node
    for ch in node.get("child") or []:
        yield from walk(ch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wfs")
    ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--type", action="append", default=[])
    ap.add_argument("--id", action="append", default=[])
    args = ap.parse_args()

    path = args.wfs if os.path.isabs(args.wfs) else os.path.join(SAMPLES, args.wfs)
    with zipfile.ZipFile(path) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))

    for scene in model["scene"]:
        for node in walk(scene):
            if ((args.name and node.get("name") in args.name)
                    or (args.type and node.get("type") in args.type)
                    or (args.id and node.get("id") in args.id)):
                print("=" * 70)
                print(json.dumps(node, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
