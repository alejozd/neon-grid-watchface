"""Repackages a .wfs replicating byte-level details of the original archives.

Watch Face Studio rejects archives that do not look like the ones it writes
itself, so entries are created with the same attributes as the sample projects:
create_system=10, UTF-8 flag (0x0800) in every entry, same external_attr and
the honeyface.json as the first entry.

Usage:
    python tools/repack_wfs.py --control     # sample repacked untouched (A/B test)
"""
import argparse
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = (r"C:\Users\alejo\AppData\Local\Programs\WatchFaceStudio"
          r"\tools\wfs_samples\Minimal_classic_W_B.wfs")


def make_info(src_info, is_dir=False):
    zi = zipfile.ZipInfo(src_info.filename, date_time=src_info.date_time)
    zi.create_system = src_info.create_system        # 10 (unix) as the samples
    zi.create_version = src_info.create_version
    zi.extract_version = src_info.extract_version
    zi.external_attr = src_info.external_attr
    zi.internal_attr = src_info.internal_attr
    zi.compress_type = zipfile.ZIP_STORED if is_dir else zipfile.ZIP_DEFLATED
    zi.flag_bits |= 0x800                            # UTF-8 filenames
    return zi


def repack(dest, model=None, preview=None, extra=None, shapes=None, drop_sample_art=True):
    """Writes `dest` from the sample, optionally replacing the model and art."""
    extra = extra or {}
    with zipfile.ZipFile(SAMPLE) as zin, zipfile.ZipFile(dest, "w") as zout:
        # 1) honeyface.json first
        src = zin.getinfo("honeyface.json")
        data = (json.dumps(model, ensure_ascii=False) if model is not None
                else zin.read("honeyface.json"))
        zout.writestr(make_info(src), data)

        # 2) latest_preview.png
        src = zin.getinfo("latest_preview.png")
        zout.writestr(make_info(src), preview if preview is not None else zin.read("latest_preview.png"))

        # 3) everything else, in the original order
        for item in zin.infolist():
            name = item.filename
            if name in ("honeyface.json", "latest_preview.png"):
                continue
            if item.is_dir():
                zout.writestr(make_info(item, is_dir=True), b"")
                continue
            if drop_sample_art and name.startswith("res/drawable-nodpi/") and name.endswith(".png"):
                if preview is not None and (name.endswith("preview.png")
                                            or name.endswith("preview_circular.png")):
                    zout.writestr(make_info(item), preview)
                continue
            if shapes is not None and name == "res/xml/watch_face_shapes.xml":
                zout.writestr(make_info(item), shapes)
                continue
            zout.writestr(make_info(item), zin.read(name))

        # 4) our layers, as extra entries
        for fname, blob in extra.items():
            zi = zipfile.ZipInfo("res/drawable-nodpi/%s" % fname, date_time=(2025, 8, 11, 11, 32, 20))
            zi.create_system = 10
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0x81B60000
            zi.flag_bits |= 0x800
            zout.writestr(zi, blob)

    # WFS validates a project by looking at the LAST bytes of the file: it must end
    # with the literal marker "normal_watchface" (or "normal_honeyface"). Python's
    # zipfile drops everything after the ZIP, so the marker is appended back,
    # byte for byte as the original archives carry it.
    with open(SAMPLE, "rb") as fh:
        fh.seek(-20, os.SEEK_END)
        tail = fh.read()
    with open(dest, "ab") as fh:
        fh.write(tail)

    print("wrote", dest, "%.1f KB" % (os.path.getsize(dest) / 1024))
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true",
                    help="repack the sample untouched, to test the writer itself")
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, "wfs-project")
    os.makedirs(out_dir, exist_ok=True)
    if args.control:
        repack(os.path.join(out_dir, "ZZ_control_sample.wfs"),
               drop_sample_art=False)
    else:
        import io
        import json
        from PIL import Image

        from make_wfs_project import CANVAS, DESIGN_CANVAS, SCALE, build_model  # noqa: E402

        model = build_model()
        hands = json.load(open(os.path.join(ROOT, "design", "out", "hands.json"),
                               encoding="utf-8"))

        def load_resized(path, size=None):
            im = Image.open(path).convert("RGBA")
            if size:
                im = im.resize(size, Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            return buf.getvalue()

        # preview scaled to the project canvas
        preview = load_resized(os.path.join(ROOT, "design", "out", "device-render.png"),
                               (CANVAS, CANVAS))

        shapes = ('<?xml version="1.0" encoding="utf-8"?>\n<WatchFaces>\n'
                  '  <WatchFace shape="CIRCLE" width="%d" height="%d" file="@raw/watchface"/>\n'
                  '</WatchFaces>\n' % (CANVAS, CANVAS)).encode("utf-8")

        art = {
            "neon_bg.png": load_resized(os.path.join(ROOT, "design", "out", "bg.png"),
                                        (CANVAS, CANVAS)),
        }
        # full-canvas hands (exported by tools/export_wfs_assets.py)
        for fname, src in (("neon_hand_hour.png", "hand_hour_480.png"),
                           ("neon_hand_minute.png", "hand_minute_480.png"),
                           ("neon_hand_second.png", "hand_second_480.png")):
            art[fname] = load_resized(os.path.join(ROOT, "wfs-assets", src),
                                      (CANVAS, CANVAS))

        repack(os.path.join(out_dir, "NeonGrid.wfs"),
               model=model, preview=preview, extra=art, shapes=shapes)
