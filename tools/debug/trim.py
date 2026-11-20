"""Trims the generated watch face document to bisect rendering problems on device.

  --no-label-imgs   drop every PartImage whose resource starts with lbl_
  --no-second-hand  drop the SecondHand from every AnalogClock
  --no-texts        drop every PartText
  --ascii           replace non-ASCII characters (the degree sign) with plain ASCII
  --keep TEXT       only keep these element tags in the Scene (comma separated)
"""
import argparse
import os

from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "build", "keep-watchface.xml")


def drop_label_imgs(scene):
    for p in list(scene.findall("PartImage")):
        img = p.find("Image")
        if img is not None and (img.get("resource") or "").startswith("lbl_"):
            scene.remove(p)


def drop_second_hand(scene):
    for clk in scene.findall("AnalogClock"):
        for h in list(clk):
            if h.tag == "SecondHand":
                clk.remove(h)


def drop_texts(scene):
    for p in list(scene.findall("PartText")):
        scene.remove(p)


def keep_only(scene, tags):
    for el in list(scene):
        if not isinstance(el.tag, str):
            continue
        if el.tag not in tags:
            scene.remove(el)


def ascii_only(root):
    for el in root.iter():
        if el.text and any(ord(c) > 127 for c in el.text):
            el.text = "".join(c if ord(c) < 128 else "C" for c in el.text)
        if el.tail and any(ord(c) > 127 for c in el.tail):
            el.tail = "".join(c if ord(c) < 128 else " " for c in el.tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-label-imgs", action="store_true")
    ap.add_argument("--no-second-hand", action="store_true")
    ap.add_argument("--no-texts", action="store_true")
    ap.add_argument("--ascii", action="store_true")
    ap.add_argument("--no-comments", action="store_true")
    ap.add_argument("--keep", default="")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=os.path.join(ROOT, "watchface", "res", "raw", "watchface.xml"))
    a = ap.parse_args()

    parser = etree.XMLParser(remove_comments=a.no_comments)
    tree = etree.parse(a.src, parser)
    scene = tree.getroot().find("Scene")
    if a.keep:
        keep_only(scene, set(t.strip() for t in a.keep.split(",")))
    if a.no_label_imgs:
        drop_label_imgs(scene)
    if a.no_second_hand:
        drop_second_hand(scene)
    if a.no_texts:
        drop_texts(scene)
    if a.ascii:
        ascii_only(tree.getroot())
    tree.write(a.out, xml_declaration=True, encoding="UTF-8")
    print("wrote", a.out, "| scene children:",
          [el.tag for el in scene if isinstance(el.tag, str)])


if __name__ == "__main__":
    main()
