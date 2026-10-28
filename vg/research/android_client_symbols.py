"""Extract Nuo/Kindred symbol evidence from a stripped Android libGame.so.

The input binary is never bundled or modified. Only printable strings that
already exist in the ELF are read, mangled C++ names are demangled with the
host ``c++filt`` (Xcode command line tools), and the result is emitted as JSON.
This is static name evidence, not decoding of payloads or runtime behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

MANGLED = re.compile(r"_Z[A-Za-z0-9_]+")
# A printable run is split on every character a mangled name cannot contain,
# so one name is matched per piece instead of greedily consuming a whole run.
NAME_PIECE = re.compile(r"[A-Za-z0-9_]+")
ACTION = re.compile(r"Nuo::Kindred::(Action[A-Za-z0-9_]+)::")
REPO_ACTION = re.compile(r"\bAction[A-Z][A-Za-z0-9]+\b")
LINE_FORMAT = re.compile(
    r"^%[0-9.]*f:(Pkt[A-Za-z0-9_]+|LocalInput_[A-Za-z0-9_]+):(.*)$")
FIELD_TYPES = {"%d": "int32", "%u": "uint32", "%f": "float", "%.5f": "float", "%s": "string"}
DEFAULT_REFERENCE = Path("vg/docs/event_semantics_2026-10-04.json")


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("--minimum must be >= 1")
    return number


def candidate_names(data: bytes, minimum: int) -> set[str]:
    pattern = rb"[\x20-\x7e]{" + str(minimum).encode("ascii") + rb",}"
    names: set[str] = set()
    for run in re.finditer(pattern, data):
        text = run.group().decode("ascii")
        for piece in NAME_PIECE.findall(text):
            if MANGLED.fullmatch(piece):
                names.add(piece)
    return names


def demangle(names: list[str]) -> tuple[dict[str, str], list[str]]:
    warnings: list[str] = []
    if not names:
        return {}, warnings
    try:
        done = subprocess.run(
            ["c++filt"], input="\n".join(names), text=True,
            capture_output=True,
        )
    except OSError as error:
        return {name: name for name in names}, [f"c++filt unavailable: {error}"]
    lines = done.stdout.splitlines()
    if done.returncode != 0 or len(lines) != len(names):
        warnings.append(
            "c++filt output did not align with input; raw names retained")
        return {name: name for name in names}, warnings
    decoded = dict(zip(names, lines))
    unchanged = sum(1 for raw, plain in decoded.items() if raw == plain)
    if unchanged:
        warnings.append(f"{unchanged} names were not valid manglings and stay raw")
    return decoded, warnings


def action_rows(actions: dict[str, list[str]]) -> list[dict[str, object]]:
    rows = []
    for cls in sorted(actions):
        members = sorted(set(actions[cls]))
        constructors = [
            member for member in members
            if member.split("(")[0].endswith(f"{cls}::{cls}")
        ]
        rows.append({
            "class": cls,
            "constructors": constructors,
            "methods": [member for member in members if member not in constructors],
        })
    return rows


def line_formats(runs: list[str]) -> tuple[dict[str, dict[str, object]], list[str]]:
    rows: dict[str, dict[str, object]] = {}
    warnings: list[str] = []
    extras: dict[str, list[dict[str, object]]] = {}
    for run in runs:
        match = LINE_FORMAT.match(run.strip())
        if not match:
            continue
        name, arguments = match.groups()
        fields: list[str] = []
        unknown: list[str] = []
        empty = 0
        for part in arguments.split(","):
            token = part.strip()
            if not token:
                empty += 1
                continue
            if token in FIELD_TYPES:
                fields.append(FIELD_TYPES[token])
            else:
                fields.append(f"unknown:{token}")
                unknown.append(token)
        trailing = arguments.rstrip().endswith(",")
        recognized = sum(1 for field in fields if not field.startswith("unknown:"))
        row: dict[str, object] = {
            "format": run.strip(),
            "fields": fields,
            "field_count": recognized,
            "token_count": len(fields),
            "total_token_count": len(fields) + empty,
            "trailing_comma": trailing,
            "empty_tokens": empty,
            "count_scope": "literal-only",
        }
        if unknown:
            row["unknown_tokens"] = sorted(set(unknown))
            warnings.append(
                f"{name}: unknown conversion tokens {sorted(set(unknown))}")
        if trailing:
            warnings.append(
                f"{name}: literal ends with a comma; {recognized} conversions "
                "are a literal-only lower bound")
        if name in rows:
            warnings.append(
                f"{name}: duplicate line format; the top-level format is variant 1 "
                "and later variants are under 'variants'")
            extras.setdefault(name, []).append(row)
        else:
            rows[name] = row
    for name, variants in extras.items():
        rows[name]["variants"] = variants
        rows[name]["variant_count"] = 1 + len(variants)
    return rows, warnings


def cross_client(client_classes: set[str], reference: Path) -> dict[str, object] | None:
    if not reference.is_file():
        return None
    text = reference.read_text(encoding="utf-8")
    repo = set(REPO_ACTION.findall(text))
    return {
        "reference": {
            "path": str(reference),
            "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
            "action_names": len(repo),
        },
        "both": sorted(client_classes & repo),
        "client_only": sorted(client_classes - repo),
        "repo_only": sorted(repo - client_classes),
        "counts": {
            "client": len(client_classes),
            "repo": len(repo),
            "both": len(client_classes & repo),
            "client_only": len(client_classes - repo),
            "repo_only": len(repo - client_classes),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--minimum", type=positive_int, default=5)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE,
                        help="repo action-name catalog for the cross-client section")
    args = parser.parse_args(argv)

    data = args.binary.read_bytes()
    jobs = re.finditer(rb"[\x20-\x7e]{" + str(args.minimum).encode("ascii") + rb",}", data)
    runs = [job.group().decode("ascii") for job in jobs]
    names = sorted({piece for run in runs for piece in NAME_PIECE.findall(run)
                    if MANGLED.fullmatch(piece)})
    decoded, warnings = demangle(names)

    actions: dict[str, list[str]] = {}
    replay: list[str] = []
    for plain in decoded.values():
        match = ACTION.match(plain)
        if match:
            actions.setdefault(match.group(1), []).append(plain)
        if "Replay" in plain or "replay" in plain:
            replay.append(plain)

    rows = action_rows(actions)
    formats, format_warnings = line_formats(runs)
    warnings.extend(format_warnings)
    cross = cross_client({row["class"] for row in rows}, args.reference)
    if cross is None:
        warnings.append(f"reference catalog not found: {args.reference}")

    report = {
        "schema": "vg.android-client-symbols.v1",
        "input": {
            "name": args.binary.name,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "scope": "printable strings and demangled names only; no code execution or payload decoding",
        "counts": {
            "mangled_names": len(names),
            "demangled_changed": sum(1 for raw, plain in decoded.items() if raw != plain),
            "demangle_unchanged": sum(1 for raw, plain in decoded.items() if raw == plain),
        },
        "warnings": warnings,
        "action_classes": rows,
        "action_class_count": len(rows),
        "replay_line_formats": formats,
        "replay_line_format_count": len(formats),
        "replay_symbols": sorted(set(replay)),
        "replay_string_literals": sorted({
            run.strip() for run in runs
            if "Replay" in run and not run.startswith("_Z") and len(run) <= 200
        }),
        "cross_client": cross,
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
