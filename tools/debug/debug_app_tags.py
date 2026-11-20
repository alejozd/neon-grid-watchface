"""Debug helper: mines the Watch Face Studio bundle for data-tag names.

The editor keeps the whole tag vocabulary as string literals inside app.asar, so
a regex over the binary is enough to find tags that no sample project uses
(weather high/low, event fields, ...).

Usage:
    python tools/debug_app_tags.py WTHR          # tags containing WTHR
    python tools/debug_app_tags.py "" --all      # every known-looking tag
"""
import os
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

APP = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio\resources"
       r"\app.asar")

TOKEN = re.compile(rb"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+")


def main():
    needle = (sys.argv[1] if len(sys.argv) > 1 else "").encode()
    show_all = "--all" in sys.argv
    found = {}
    with open(APP, "rb") as fh:
        data = fh.read()
    for m in TOKEN.finditer(data):
        tok = m.group().decode()
        if len(tok) > 40:
            continue
        if needle and needle.decode() not in tok:
            continue
        found.setdefault(tok, 0)
        found[tok] += 1
    for tok in sorted(found):
        print("%-34s %d" % (tok, found[tok]))


if __name__ == "__main__":
    main()
