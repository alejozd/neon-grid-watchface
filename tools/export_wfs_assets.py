"""Exports the art as a Watch Face Studio friendly asset pack.

WFS cannot import a WFF project, but it can consume flat PNG assets. This writes
wfs-assets/ with full-canvas 480x480 layers (pivot at canvas centre), the baked
labels and a preview, so the face can be rebuilt visually in WFS.
"""
import os
import shutil
import sys

DESIGN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design")
sys.path.insert(0, DESIGN)

import render as R  # noqa: E402

ROOT = os.path.dirname(DESIGN)
OUT = os.path.join(ROOT, "wfs-assets")


def main():
    os.makedirs(OUT, exist_ok=True)

    bg = R.make_bg()
    R.save(bg, "wfs_bg.png")
    shutil.copyfile(os.path.join(R.OUT, "wfs_bg.png"), os.path.join(OUT, "bg_480.png"))

    hour = R.make_hand(112, 7.6, R.CYAN, tail=15, shape="spear")
    minute = R.make_hand(162, 5.6, R.CYAN, tail=17, shape="spear")
    second = R.make_hand(178, 1.7, R.MAGENTA, tail=26, shape="needle")
    for img, name in ((hour, "hand_hour_480"), (minute, "hand_minute_480"),
                      (second, "hand_second_480")):
        R.save(img, name + ".png")
        shutil.copyfile(os.path.join(R.OUT, name + ".png"), os.path.join(OUT, name + ".png"))

    # baked HUD labels
    for f in os.listdir(os.path.join(R.OUT, "labels")):
        if f.endswith(".png"):
            shutil.copyfile(os.path.join(R.OUT, "labels", f), os.path.join(OUT, f))

    # preview: the real device render if available, else the mock
    dev = os.path.join(R.OUT, "device-render.png")
    src = dev if os.path.exists(dev) else os.path.join(R.OUT, "preview_full.png")
    shutil.copyfile(src, os.path.join(OUT, "preview_480.png"))

    print("exported to", OUT)


if __name__ == "__main__":
    main()
