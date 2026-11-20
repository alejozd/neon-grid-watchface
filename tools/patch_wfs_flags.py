"""Sets the UTF-8 filename flag (0x0800) in every ZIP entry of a .wfs.

CPython's zipfile resets the general-purpose flag when writing, so the flag is
patched afterwards in both the local headers and the central directory to match
what Watch Face Studio produces.
"""
import struct
import sys

LOCAL = b"PK\x03\x04"
CENTRAL = b"PK\x01\x02"


def patch(path):
    with open(path, "rb") as fh:
        data = bytearray(fh.read())

    count = 0
    for sig, flag_off in ((LOCAL, 6), (CENTRAL, 8)):
        start = 0
        while True:
            idx = data.find(sig, start)
            if idx < 0:
                break
            pos = idx + flag_off
            (flags,) = struct.unpack_from("<H", data, pos)
            if not flags & 0x0800:
                struct.pack_into("<H", data, pos, flags | 0x0800)
                count += 1
            start = idx + 4

    with open(path, "wb") as fh:
        fh.write(data)
    print("patched %d headers in %s" % (count, path))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        patch(p)
