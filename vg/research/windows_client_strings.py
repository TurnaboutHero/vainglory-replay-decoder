"""Extract replay-related strings and MSVC RTTI class names from a PE client.

The input executable is never bundled or modified. Only printable runs already
present in the file are read, in both 8-bit ASCII and UTF-16LE, and no
execution, unpacking or decryption is done. RTTI names are decoded only for the
simple ``.?AVClass@Scope@Nuo@@`` form; other forms keep ``decoded: null``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

PRINTABLE_ASCII = re.compile(rb"[\x20-\x7e]{5,}")
PRINTABLE_UTF16 = re.compile(rb"(?:[\x20-\x7e]\x00){5,}")
RTTI = re.compile(r"^\.\?A[VU]\S+$")
SIMPLE_RTTI = re.compile(r"^\.\?A[VU][A-Za-z0-9_]+(?:@[A-Za-z0-9_]+)+@@$")
VGR_LITERAL = re.compile(
    r"^%s/%s(?:\.%d\.vgr)?$|^replayManifest-?$|^replayManifest\.txt$"
    r"|^_%Y-%m-%dT%H-%M-%S\.dat$")
TEXT_FORMAT = re.compile(r"^%[0-9.]*[a-z]:")


def decode_rtti(raw: str) -> str | None:
    """Decode only the simple ``.?AVClass@Scope@Nuo@@`` form, else return None."""
    if not SIMPLE_RTTI.fullmatch(raw):
        return None
    body = raw[4:].rstrip("@")
    parts = [part for part in body.split("@") if part]
    return "::".join(reversed(parts))


def _utf16_runs(data: bytes) -> list[tuple[int, str, str]]:
    """Find UTF-16LE runs that start at byte 0 or after a string NUL.

    A match that starts inside an ASCII run is rejected and the scan resumes
    one byte later, so the real UTF-16 start immediately after the NUL is not
    skipped and overlapping variants are not emitted.
    """
    runs: list[tuple[int, str, str]] = []
    position = 0
    while position < len(data):
        match = PRINTABLE_UTF16.search(data, position)
        if match is None:
            break
        start = match.start()
        if start and data[start - 1] != 0:
            position = start + 1
            continue
        runs.append((start, match.group().decode("utf-16-le"), "utf-16-le"))
        position = match.end()
    return runs


def readable_runs(data: bytes) -> list[tuple[int, str, str]]:
    """Return (file offset, text, encoding) for ASCII and UTF-16LE runs."""
    runs = [(match.start(), match.group().decode("ascii"), "ascii")
            for match in PRINTABLE_ASCII.finditer(data)]
    runs.extend(_utf16_runs(data))
    return sorted(runs)


def entry(offset: int, value: str, encoding: str) -> dict[str, object]:
    return {"offset": offset, "value": value, "encoding": encoding}


def classify(runs: list[tuple[int, str, str]], limit: int = 200) -> dict[str, object]:
    vgr = [entry(offset, value, encoding) for offset, value, encoding in runs
           if VGR_LITERAL.fullmatch(value.strip()) and len(value.strip()) <= limit]
    pkt = [entry(offset, value, encoding) for offset, value, encoding in runs
           if "Pkt" in value and len(value.strip()) <= limit]
    formats = [entry(offset, value, encoding) for offset, value, encoding in runs
               if TEXT_FORMAT.match(value.strip()) and len(value.strip()) <= limit]
    replay = sorted({value.strip() for _, value, _ in runs
                     if "replay" in value.lower() and len(value.strip()) <= limit})
    rtti = []
    for offset, value, encoding in runs:
        raw = value.strip()
        if RTTI.fullmatch(raw):
            rtti.append({"raw": raw, "offset": offset, "encoding": encoding,
                         "decoded": decode_rtti(raw)})
    return {
        "replay_strings": replay,
        "vgr_and_manifest_strings": vgr,
        "pkt_strings": pkt,
        "text_format_strings": formats,
        "rtti_classes": rtti,
        "counts": {
            "printable_runs": len(runs),
            "replay_strings": len(replay),
            "vgr_and_manifest_strings": len(vgr),
            "pkt_strings": len(pkt),
            "text_format_strings": len(formats),
            "rtti_classes": len(rtti),
            "rtti_decoded": sum(1 for row in rtti if row["decoded"] is not None),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args(argv)

    data = args.binary.read_bytes()
    report = {
        "schema": "vg.windows-client-strings.v1",
        "input": {
            "name": args.binary.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "scope": ("printable ASCII and UTF-16LE strings only; no execution, "
                  "unpacking or decryption"),
        **classify(readable_runs(data), args.limit),
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
