"""
Builds diagnostic variants to find out why the watch face is not listed by the
watch face picker.

  A  control: current watchface.xml + current watch_face_info.xml
  B  same XML, but watch_face_info.xml reduced to the official sample (Preview + Editable)
  C  minimal XML (SimpleAnalog-style: image + 2 hands, no text/variants/complications)
     + minimal watch_face_info.xml

Each variant gets its own package name and label so the picker shows them apart.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "watchface")
OUT = os.path.join(ROOT, "build", "variants")

CURRENT_XML = open(os.path.join(SRC, "res", "raw", "watchface.xml"), encoding="utf-8").read()

INFO_FULL = """<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
  <Preview value="@drawable/preview" />
  <Category value="CATEGORY_EMPTY" />
  <AvailableInRetail value="false" />
  <MultipleInstancesAllowed value="true" />
  <Editable value="true" />
</WatchFaceInfo>
"""

INFO_MIN = """<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
  <Preview value="@drawable/preview" />
  <Editable value="true" />
</WatchFaceInfo>
"""

XML_C = """<?xml version="1.0" encoding="UTF-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="ANALOG"/>
  <Metadata key="PREVIEW_TIME" value="10:08:32"/>
  <Scene backgroundColor="#FF000000">
    <PartImage x="0" y="0" width="480" height="480">
      <Image resource="bg_ambient"/>
    </PartImage>
    <AnalogClock x="0" y="0" width="480" height="480">
      <HourHand resource="hand_hour_ambient" x="231.0" y="124.0" width="18" height="137"
          pivotX="0.5" pivotY="0.846715"/>
      <MinuteHand resource="hand_minute_ambient" x="231.75" y="74.0" width="16" height="189"
          pivotX="0.5" pivotY="0.878307"/>
    </AnalogClock>
    <PartText x="0" y="300" width="480" height="80">
      <Text align="CENTER">
        <Font family="SYNC_TO_DEVICE" size="56" color="#FFFFFFFF">
          <Template><![CDATA[[HOUR_0_23_Z]:[MINUTE_Z]]]></Template>
        </Font>
      </Text>
    </PartText>
  </Scene>
</WatchFace>
"""

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}">
  <uses-feature android:name="android.hardware.type.watch" />
  <application android:label="{label}" android:hasCode="false">
    <meta-data android:name="com.google.android.wearable.standalone" android:value="true" />
    <property android:name="com.google.wear.watchface.format.version" android:value="{fmt}" />
  </application>
</manifest>
"""

VARIANTS = [
    # id, package, label, watchface.xml, watch_face_info, format version
    ("a", "com.relog.vara", "Neon A", CURRENT_XML, INFO_FULL, 2),
    ("b", "com.relog.varb", "Neon B", CURRENT_XML, INFO_MIN, 2),
    ("c", "com.relog.varc", "Neon C", XML_C, INFO_MIN, 2),
]


def build(vid, pkg, label, xml, info, fmt):
    d = os.path.join(OUT, vid)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, "res", "raw"))
    os.makedirs(os.path.join(d, "res", "xml"))
    shutil.copytree(os.path.join(SRC, "res", "drawable-nodpi"),
                    os.path.join(d, "res", "drawable-nodpi"))
    shutil.copytree(os.path.join(SRC, "res", "values"),
                    os.path.join(d, "res", "values"))
    open(os.path.join(d, "AndroidManifest.xml"), "w", encoding="utf-8").write(
        MANIFEST.format(pkg=pkg, label=label, fmt=fmt))
    open(os.path.join(d, "res", "raw", "watchface.xml"), "w", encoding="utf-8").write(xml)
    open(os.path.join(d, "res", "xml", "watch_face_info.xml"), "w", encoding="utf-8").write(info)
    print("variant", vid, "->", d)


if __name__ == "__main__":
    for v in VARIANTS:
        build(*v)
