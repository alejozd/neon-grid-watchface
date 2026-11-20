"""Composes a test scene: the working debug document's skeleton (bg + hands)
plus the real generated PartText parts, so we can tell whether the text parts
or the surrounding elements break the render."""
import os
import sys

from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "build", "keep-watchface.xml")
OUT = os.path.join(ROOT, "watchface", "res", "raw", "watchface.xml")

SKELETON = """<?xml version="1.0" encoding="UTF-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="ANALOG"/>
  <Scene backgroundColor="#FF101820">
    <PartImage x="0" y="0" width="480" height="480">
      <Image resource="bg_ambient"/>
    </PartImage>
    <AnalogClock x="0" y="0" width="480" height="480">
      <HourHand resource="hand_hour_ambient" x="231.0" y="124.0" width="18" height="137"
          pivotX="0.5" pivotY="0.846715"/>
      <MinuteHand resource="hand_minute_ambient" x="231.75" y="74.0" width="16" height="189"
          pivotX="0.5" pivotY="0.878307"/>
    </AnalogClock>
  </Scene>
</WatchFace>
"""


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    gen = etree.parse(GEN)
    texts = gen.getroot().find("Scene").findall("PartText")
    labels = [p for p in gen.getroot().find("Scene").findall("PartImage")
              if (p.find("Image").get("resource") or "").startswith("lbl_")]

    sk = etree.fromstring(SKELETON.encode("utf-8"))
    scene = sk.find("Scene")

    if which == "first":
        picked = [texts[0]]
    elif which == "two":
        picked = texts[:2]
    elif which == "labels":
        picked = labels
    else:
        picked = texts

    for el in picked:
        scene.append(el)

    etree.ElementTree(sk).write(OUT, xml_declaration=True, encoding="UTF-8")
    print("wrote", OUT, "with", len(picked), "elements;", which)


if __name__ == "__main__":
    main()
