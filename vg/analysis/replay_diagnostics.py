#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["typer", "rich"]
# ///
# How to run: install uv; from repository root:
# uv run --with typer --with rich python -m vg.analysis.replay_diagnostics --help
"""Bounded initialization and terminal observations; no gameplay conclusions."""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import struct
from typing import Final, TypedDict, override

from vg.analysis.event_timeline import _discover_sections
from vg.analysis.native_event_fields import DecodedFields, decode_fields
from vg.core.native_stats import inspect_native_clock
from vg.core.vgr_records import VGRRecord, iter_records

ANCHORS: Final = frozenset((0x03F1, 0x0452, 0x048D))
UPDATES: Final = frozenset((0x041C, 0x041D, 0x0430, 0x0431, 0x03F3))


class Observation(TypedDict):
    sequence: int
    section: int
    offset: int
    timestamp: float
    opcode: int
    content_length: int
    record_sha256: str
    fields: DecodedFields


@dataclass(frozen=True, slots=True)
class Section:
    number: int
    bytes: int
    sha256: str
    records: int


@dataclass(frozen=True, slots=True)
class Signature:
    section: int
    offset: int
    opcode: int
    content_length: int
    timestamp: float
    record_sha256: str
    definition_index: int | None
    skin_hash: int | None
    entity_be32: int | None


@dataclass(frozen=True, slots=True)
class Diagnostics:
    sections: tuple[Section, ...]
    record_count: int
    initial: tuple[Signature, ...]
    terminals: tuple[Observation, ...]
    trailing_same_time: tuple[Observation, ...]
    undecoded_layouts: tuple[tuple[int, int, str, int], ...]
    opcode_lengths: tuple[tuple[int, int, int], ...]
    definition_references: tuple[tuple[int, int, int], ...]
    clock_json: str


@dataclass(frozen=True, slots=True)
class InputError(ValueError):
    reason: str

    @override
    def __str__(self) -> str:
        return self.reason


def diagnose(frames: Sequence[tuple[int, bytes]], initial_limit: int = 128) -> Diagnostics:
    """Keep original order, all anchor-time trailing updates and strict framing.

    Unsupported is relative to decode_fields, not the native client dispatcher.
    Fingerprints cover complete records without emitting account-bearing payloads.
    """
    numbers = [number for number, _ in frames]
    if not frames or numbers != sorted(set(numbers)) or min(numbers) < 0:
        raise InputError('sections must be nonempty, unique and ordered')
    if not 1 <= initial_limit <= 4096:
        raise InputError('initial_limit must be between 1 and 4096')
    terminals: list[Observation] = []
    initial: list[Signature] = []
    sections: list[Section] = []
    lengths: Counter[tuple[int, int]] = Counter()
    unsupported: Counter[tuple[int, int, str]] = Counter()
    definitions: Counter[tuple[int, int]] = Counter()
    seq = 0
    for number, data in frames:
        count = 0
        for record in iter_records(data):
            fields = decode_fields(record)
            lengths[record.opcode, record.content_length] += 1
            status = fields.get('decoding_status', 'missing_status')
            if status != 'decoded':
                unsupported[record.opcode, record.content_length, status] += 1
            if record.opcode in (0x03F2, 0x03F3) and len(record.payload) >= 12:
                definition, skin, entity = struct.unpack_from('>III', record.payload)
                definitions[definition, skin] += 1
            else:
                definition = skin = entity = None
            if len(initial) < initial_limit or record.opcode in ANCHORS:
                digest = hashlib.sha256(data[record.offset:record.offset + 8 + record.content_length]).hexdigest()
                if len(initial) < initial_limit:
                    initial.append(Signature(number, record.offset, record.opcode,
                                             record.content_length, record.timestamp,
                                             digest, definition, skin, entity))
                if record.opcode in ANCHORS:
                    terminals.append(_observation(number, seq, record, digest))
            count += 1
            seq += 1
        sections.append(Section(number, len(data), hashlib.sha256(data).hexdigest(), count))
    earliest: dict[float, int] = {}
    for terminal in terminals:
        _ = earliest.setdefault(terminal['timestamp'], terminal['sequence'])
    trailing: list[Observation] = []
    seq = 0
    for number, data in frames:
        for record in iter_records(data):
            first = earliest.get(record.timestamp)
            if first is not None and seq > first and record.opcode in UPDATES:
                digest = hashlib.sha256(data[record.offset:record.offset + 8 + record.content_length]).hexdigest()
                trailing.append(_observation(number, seq, record, digest))
            seq += 1
    return Diagnostics(tuple(sections), seq, tuple(initial), tuple(terminals), tuple(trailing),
                       tuple((*key, count) for key, count in sorted(unsupported.items())),
                       tuple((*key, count) for key, count in sorted(lengths.items())),
                       tuple((*key, count) for key, count in sorted(definitions.items())),
                       json.dumps(asdict(inspect_native_clock(frames)), allow_nan=False))


def _observation(section: int, sequence: int, record: VGRRecord, digest: str) -> Observation:
    return {'sequence': sequence, 'section': section, 'offset': record.offset,
            'timestamp': record.timestamp, 'opcode': record.opcode,
            'content_length': record.content_length, 'record_sha256': digest,
            'fields': decode_fields(record)}


@dataclass(frozen=True, slots=True)
class Difference:
    index: int
    left: Signature | None
    right: Signature | None
    compared_prefix_limit: int


def first_difference(left: Diagnostics, right: Diagnostics, *, structure_only: bool = False) -> Difference | None:
    """Compare bounded ordered signatures; equality never proves full equality."""
    for index in range(max(len(left.initial), len(right.initial))):
        a = left.initial[index] if index < len(left.initial) else None
        b = right.initial[index] if index < len(right.initial) else None
        differs = a != b
        if structure_only and a is not None and b is not None:
            differs = (a.opcode, a.content_length) != (b.opcode, b.content_length)
        if differs:
            return Difference(index, a, b, max(len(left.initial), len(right.initial)))
    return None


def load_frames(path: Path) -> list[tuple[int, bytes]]:
    """Read numbered sections without changing input files."""
    return [(number, source.read_bytes()) for number, source in _discover_sections(path)]


@dataclass(frozen=True, slots=True)
class CLIReport:
    schema_version: int
    recording: Diagnostics
    comparison: Diagnostics | None
    first_difference: Difference | None
    first_structure_difference: Difference | None
    limitations: tuple[str, ...]


def main(path: Path, compare: Path | None = None, initial_limit: int = 128) -> None:
    """Emit anonymous observations; --compare compares a bounded initial prefix."""
    import typer

    try:
        report = diagnose(load_frames(path), initial_limit)
        other = diagnose(load_frames(compare), initial_limit) if compare is not None else None
        result = CLIReport(1, report, other,
                           first_difference(report, other) if other else None,
                           first_difference(report, other, structure_only=True) if other else None,
                           ('No winner, final stats, lifecycle or playback inference.',
                            'Undecoded layouts refer only to decode_fields coverage.',
                            'Same-time association is positional, not causal.'))
        print(json.dumps(asdict(result), allow_nan=False))
    except (OSError, ValueError) as error:
        typer.echo(f'replay-diagnostics: {error}', err=True)
        raise typer.Exit(2) from error


if __name__ == '__main__':
    import typer

    typer.run(main)
