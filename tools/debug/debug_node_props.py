"""Debug helper: compact flattened view of node properties.

Prints `category.property = value` lines instead of the full JSON, which is far
easier to scan when comparing templates.

Usage:
    python tools/debug_node_props.py Info_clocks.wfs --type digitalClock
"""
import argparse
import json
import os
import zipfile

import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SAMPLES = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
           r"\tools\wfs_samples")


def walk(node):
    yield node
    for ch in node.get("child") or []:
        yield from walk(ch)


def leaves(prefix, value, out):
    if isinstance(value, dict):
        if "value" in value and len(value) <= 4 and not any(
                isinstance(v, dict) for v in value.values()):
            out.append("%s = %s" % (prefix, json.dumps(value.get("value"), ensure_ascii=False)))
            if "expression" in value:
                out.append("%s.expression = %s" % (
                    prefix, json.dumps(value["expression"], ensure_ascii=False)))
            return
        for k, v in value.items():
            leaves("%s.%s" % (prefix, k) if prefix else k, v, out)
        return
    out.append("%s = %s" % (prefix, json.dumps(value, ensure_ascii=False)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wfs")
    ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--type", action="append", default=[])
    ap.add_argument("--props", default="true",
                    help="which categories to show, comma separated (default: all)")
    args = ap.parse_args()

    path = args.wfs if os.path.isabs(args.wfs) else os.path.join(SAMPLES, args.wfs)
    with zipfile.ZipFile(path) as z:
        model = json.loads(z.read("honeyface.json").decode("utf-8"))

    for scene in model["scene"]:
        for node in walk(scene):
            if not ((args.name and node.get("name") in args.name)
                    or (args.type and node.get("type") in args.type)):
                continue
            print("=" * 70)
            print("%s  name=%r  id=%s" % (node.get("type"), node.get("name"), node.get("id")))
            cl = node.get("conditionalLine")
            if isinstance(cl, dict):
                print("conditionalLine.activatedCondition = %r" % cl.get("activatedCondition"))
            cats = node.get("categories") or {}
            for cname, cat in cats.items():
                out = []
                leaves(cname, cat.get("properties") or {}, out)
                if not out:
                    continue
                for line in out:
                    print("  " + line)


if __name__ == "__main__":
    main()
