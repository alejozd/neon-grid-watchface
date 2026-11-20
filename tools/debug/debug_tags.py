"""Debug helper: inventories data tags and action targets across the samples.

Usage:
    python tools/debug_tags.py tabs      # every [TAG] found in any sample
    python tools/debug_tags.py actions   # every openApp / custom app id used
    python tools/debug_tags.py texts     # static text strings (for wording ideas)
"""
import glob
import json
import os
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import zipfile

SAMPLES = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
           r"\tools\wfs_samples")
TAG = re.compile(r"\[[A-Z0-9_]+\]")


def models():
    for path in sorted(glob.glob(os.path.join(SAMPLES, "*.wfs"))):
        with zipfile.ZipFile(path) as z:
            yield os.path.basename(path), json.loads(
                z.read("honeyface.json").decode("utf-8"))


def walk(node):
    yield node
    for ch in node.get("child") or []:
        yield from walk(ch)


def all_nodes(model):
    for scene in model["scene"]:
        yield from walk(scene)


def collect(value, out):
    if isinstance(value, dict):
        for v in value.values():
            collect(v, out)
    elif isinstance(value, list):
        for v in value:
            collect(v, out)
    elif isinstance(value, str):
        for m in TAG.findall(value):
            out.setdefault(m, set()).add(CUR[0])


CUR = [None]


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "tags"
    if what == "tags":
        tags = {}
        for name, model in models():
            CUR[0] = name
            collect(model, tags)
        for tag in sorted(tags):
            print("%-22s %s" % (tag, ", ".join(sorted(tags[tag]))))
    elif what == "actions":
        found = {}
        for name, model in models():
            for node in all_nodes(model):
                act = (node.get("categories") or {}).get("action")
                if not act:
                    continue
                props = act.get("properties") or {}
                if not (props.get("enabled") or {}).get("value"):
                    continue
                t = (props.get("actionType") or {}).get("value")
                val = (props.get("action") or {}).get("value")
                found.setdefault(json.dumps([t, val], sort_keys=True),
                                 set()).add("%s:%s" % (name, node.get("name")))
        for k in sorted(found):
            print("%-90s %s" % (k, ", ".join(sorted(found[k]))))
    elif what == "texts":
        for name, model in models():
            for node in all_nodes(model):
                if node.get("type") != "text":
                    continue
                props = ((node.get("categories") or {}).get("text") or {}).get("properties") or {}
                val = (props.get("text") or {}).get("value")
                if isinstance(val, str) and val and not TAG.search(val):
                    print("%-28s %-30r %s" % (name, val, node.get("name")))


if __name__ == "__main__":
    main()
