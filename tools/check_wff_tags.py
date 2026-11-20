"""Checks every data tag used by the watch face against the device runtime.

The Watch Face Format runtime refuses to start a face that references a data
source it does not know, and it does so with a NullPointerException that says
nothing about the tag (see docs/HANDOFF.md 4.12). The name table lives inside
`DeclarativeWatchFaceRuntime.apk`, so the check is a plain byte search over its
dex files.

Usage:
    python tools\\check_wff_tags.py [--apk build\\wfrt.apk] [xml]
    python tools\\check_wff_tags.py --pull        # trae el APK del reloj primero
"""
import os
import re
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_XML = os.path.join(ROOT, "watchface", "res", "raw", "watchface.xml")
DEFAULT_APK = os.path.join(ROOT, "build", "wfrt.apk")
ADB = r"C:\Users\alejo\AppData\Local\Android\Sdk\platform-tools\adb.exe"
SERIAL = os.environ.get("WATCH_SERIAL", "192.168.1.11:36673")
PACKAGE = "com.samsung.wear.watchface.runtime"

TAG = re.compile(r"\[([A-Z][A-Z0-9_.]*)\]")
# only attribute values carry expressions; element text is literal
ATTR = re.compile(r'(?:expression|value)="([^"]*)"')


def pull_runtime(apk_path):
    out = subprocess.run([ADB, "-s", SERIAL, "shell", "pm", "path", PACKAGE],
                         capture_output=True, text=True)
    path = out.stdout.replace("package:", "").strip()
    if not path:
        raise SystemExit("no encuentro el paquete %s en el reloj" % PACKAGE)
    subprocess.run([ADB, "-s", SERIAL, "pull", path, apk_path],
                   check=True, capture_output=True)


def known_names(apk_path):
    with zipfile.ZipFile(apk_path) as z:
        blob = b"".join(z.read(n) for n in z.namelist() if n.endswith(".dex"))
    return blob


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    xml = args[0] if args else DEFAULT_XML
    apk = DEFAULT_APK
    for a in sys.argv[1:]:
        if a.startswith("--apk="):
            apk = a.split("=", 1)[1]
    if "--pull" in sys.argv or not os.path.exists(apk):
        print("trayendo el runtime del reloj ...")
        pull_runtime(apk)

    blob = known_names(apk)
    with open(xml, encoding="utf-8") as fh:
        text = fh.read()

    # a malformed XML makes the runtime die with the same useless NPE
    import xml.etree.ElementTree as ET
    try:
        ET.parse(xml)
        print("XML              : bien formado")
    except ET.ParseError as exc:
        print("ERROR XML mal formado: %s" % exc)
        return 1

    exprs = " ".join(ATTR.findall(text))
    # dotted names (WEATHER.*, COMPLICATION.*) live in another table of the
    # runtime, so they cannot be checked with a plain byte search
    tags = sorted({t for t in TAG.findall(exprs) if "." not in t})

    unknown = []
    for tag in tags:
        if tag.encode() not in blob:
            unknown.append(tag)
    print("etiquetas usadas : %s" % ", ".join(tags))
    print("runtime          : %s" % apk)
    for tag in unknown:
        print("ERROR el runtime no conoce [%s]" % tag)
    print("RESULT: %d desconocidas de %d" % (len(unknown), len(tags)))
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
