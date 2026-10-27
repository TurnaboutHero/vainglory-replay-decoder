"""Locate absolute 32-bit references to selected literals in a PE32 image.

Reads only headers and bytes: no execution, unpacking or relocation. PE32 code
commonly references read-only strings with absolute ImageBase-relative VAs, so
each literal's VA is searched as a little-endian dword inside ``.text``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

DEFAULT_LITERALS = (
    "%s/%s.%d.vgr",
    "%s/%s",
    "replayManifest.txt",
    "replayManifest-",
    "_%Y-%m-%dT%H-%M-%S.dat",
    "%s\n",
)


def sections(data: bytes) -> tuple[int, list[dict[str, int | str]]]:
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    optional = pe + 24
    if struct.unpack_from("<H", data, optional)[0] != 0x10B:
        raise SystemExit("only PE32 (0x10b) images are supported")
    image_base = struct.unpack_from("<I", data, optional + 28)[0]
    table = optional + optional_size
    rows = []
    for index in range(count):
        at = table + index * 40
        name = data[at:at + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, rva, rsize, offset = struct.unpack_from("<IIII", data, at + 8)
        rows.append({"name": name, "rva": rva, "vsize": vsize,
                     "offset": offset, "raw_size": rsize})
    return image_base, rows


def va_of(rows: list[dict[str, int | str]], offset: int, image_base: int) -> int | None:
    for row in rows:
        if row["offset"] <= offset < row["offset"] + row["raw_size"]:
            return image_base + row["rva"] + (offset - row["offset"])
    return None


def occurrence_vs(data: bytes, rows, image_base: int, literal: str) -> list[dict[str, int]]:
    needle = literal.encode("ascii")
    found: list[dict[str, int]] = []
    start = 0
    while True:
        index = data.find(needle, start)
        if index < 0:
            break
        start = index + 1
        # Only complete strings: preceded by NUL/start and followed by NUL.
        # This drops prefix matches such as "%s/%s" inside "%s/%s.%d.vgr".
        if index and data[index - 1] != 0:
            continue
        end = index + len(needle)
        if end < len(data) and data[end] != 0:
            continue
        va = va_of(rows, index, image_base)
        if va is not None:
            found.append({"file_offset": index, "va": va})
    return found


def code_xrefs(data: bytes, rows, image_base: int, va: int) -> list[int]:
    text = next((row for row in rows if row["name"] == ".text"), None)
    if text is None:
        return []
    pattern = struct.pack("<I", va)
    hits: list[int] = []
    start = text["offset"]
    end = start + text["raw_size"]
    while True:
        index = data.find(pattern, start, end)
        if index < 0:
            return hits
        hits.append(image_base + text["rva"] + (index - start))
        start = index + 1


def parse_literal_spec(spec: str) -> tuple[str, int | None]:
    """Split ``VALUE`` or ``VALUE@0xVA`` into a literal and an optional VA."""
    if "@0x" not in spec:
        return spec, None
    literal, va_text = spec.rsplit("@0x", 1)
    return literal, int(va_text, 16)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--literal", action="append", dest="literals",
        help="extra literal; append '@0xVA' (e.g. \"w@0x1215ea8\") to "
             "restrict that literal to one VA so short strings stay bounded")
    args = parser.parse_args(argv)

    data = args.binary.read_bytes()
    image_base, rows = sections(data)
    specs = list(DEFAULT_LITERALS) + list(args.literals or [])
    evidence = []
    for spec in specs:
        literal, filter_va = parse_literal_spec(spec)
        for occurrence in occurrence_vs(data, rows, image_base, literal):
            if filter_va is not None and occurrence["va"] != filter_va:
                continue
            evidence.append({
                "literal": literal,
                "va": occurrence["va"],
                "file_offset": occurrence["file_offset"],
                "code_xrefs": code_xrefs(data, rows, image_base, occurrence["va"]),
            })
    report = {
        "schema": "vg.windows-client-xrefs.v1",
        "input": {
            "name": args.binary.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "scope": "absolute PE32 dword references inside .text; no execution",
        "image_base": image_base,
        "literals": evidence,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is None:
        sys.stdout.write(text + "\n")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
