"""Debug helper: prints literal context around a needle inside the WFS bundle.

Usage:
    python tools/debug_app_context.py UNREAD_NOTIFICATION_COUNT [radius]
"""
import re
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

APP = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio\resources"
       r"\app.asar")


def main():
    needle = sys.argv[1].encode()
    radius = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    with open(APP, "rb") as fh:
        data = fh.read()
    for i, m in enumerate(re.finditer(re.escape(needle), data)):
        lo, hi = max(0, m.start() - radius), min(len(data), m.end() + radius)
        chunk = data[lo:hi]
        text = chunk.decode("utf-8", "replace")
        text = re.sub(r"[^\x20-\x7e\n]", ".", text)
        print("--- match %d at %d ---" % (i + 1, m.start()))
        print(text)
        if i >= 5:
            break


if __name__ == "__main__":
    main()
