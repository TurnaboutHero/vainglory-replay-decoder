"""Observed scoreboard state from native snapshots and stat updates.

An accepted result describes the requested recorded state, not match completion.
Clock interpolation uses the 046f anchor in each numbered frame. Resource 14
is exposed as minion_kills for existing callers and means the native scoreboard
CS value. Lane-minion versus jungle contribution is not inferred.
"""

from dataclasses import dataclass
import math
import struct
from typing import Collection, Sequence

from vg.core.native_query import (
    ClockAudit, GameTime, RecordTime, _scan_clock, select_native_query,
)


@dataclass(frozen=True, slots=True)
class NativePlayerStats:
    entity_id: int
    kills: int
    deaths: int
    assists: int
    minion_kills: int


@dataclass(frozen=True, slots=True)
class NativeStatsResult:
    valid: bool
    status: str
    reason: str
    players: tuple[NativePlayerStats, ...] = ()
    requested_game_time: float | None = None
    first_game_time: float | None = None
    last_game_time: float | None = None
    as_of_game_time: float | None = None
    applied_game_time: float | None = None
    record_boundary: tuple[int, int] | None = None


def inspect_native_clock(frames: Sequence[tuple[int, bytes]]) -> ClockAudit:
    """Inspect all frames, including data beyond a requested scoreboard capture."""
    return _scan_clock(frames)[0]


def _integer(value: float, *, signed: bool = False) -> int:
    if not math.isfinite(value) or not value.is_integer() or (not signed and value < 0):
        raise ValueError(f'unsupported count {value}')
    return int(value)


def read_native_stats(
    frames: Sequence[tuple[int, bytes]],
    player_ids: Collection[int],
    cutoff: GameTime | RecordTime | None = None,
) -> NativeStatsResult:
    """Read native assignments and updates; withhold incomplete/unknown state.

    Full-input framing and clock integrity are required even for early captures.
    Relevant semantic failures only affect state at or before the query. A spawn
    for an existing actor is a no-op. Actor destruction requires an independently
    proved cleanup boundary before another lifetime can be interpreted.
    Missing baselines are never manufactured from zero.
    EOF includes every record; RecordTime filters only on record timestamps.
    First/last game times describe endpoints, not global interpolation extrema.
    """
    query = select_native_query(frames, cutoff)
    audit = query.audit
    requested = query.requested_game_time

    def invalid(status: str, reason: str) -> NativeStatsResult:
        return NativeStatsResult(False, status, reason, requested_game_time=requested,
                                 first_game_time=audit.first_game_time, last_game_time=audit.last_game_time)

    if not query.valid:
        return invalid(query.status, query.reason)
    supplied = tuple(player_ids)
    if not supplied:
        return invalid('missing_baseline', 'no player identities supplied')
    if any(not isinstance(entity, int) or isinstance(entity, bool)
           or not 0 < entity <= 0xffffffff for entity in supplied):
        return invalid('invalid_query', 'player identities must be positive unsigned 32-bit integers')
    if len(set(supplied)) != len(supplied):
        return invalid('invalid_query', 'player identities must be unique')
    ids = sorted(supplied)
    states: dict[int, list[int]] = {}
    problems: dict[int, str] = {}
    persistent_layers: dict[int, str] = {}
    spawned: set[int] = set()
    wanted = set(ids)
    for section, record in query.records():
        payload = record.payload
        if record.opcode in (0x03f2, 0x03f3):
            ref_offset = 8
        elif record.opcode in (0x041c, 0x041d, 0x040b):
            ref_offset = 0
        else:
            continue
        location = f'frame {section} offset {record.offset} opcode {record.opcode:04x}'
        if len(payload) < ref_offset + 4:
            for entity in ids:
                problems[entity] = f'{location}: cannot identify actor in short payload'
            continue
        entity = struct.unpack_from('>I', payload, ref_offset)[0]
        if entity not in wanted:
            continue
        try:
            if record.opcode == 0x040b:
                persistent_layers[entity] = f'{location}: actor destruction requested; native cleanup boundary unobserved'
                continue
            if record.opcode == 0x03f2:
                if len(payload) not in (122, 126):
                    raise ValueError(f'unsupported spawn length {len(payload)}')
                spawned.add(entity)
                continue
            if record.opcode == 0x03f3:
                if len(payload) not in (746, 750):
                    raise ValueError(f'unsupported snapshot length {len(payload)}')
                if entity in spawned:
                    continue
                spawned.add(entity)
                if struct.unpack_from('>I', payload, 326)[0] != 0:
                    continue
                # Native receiver sets valid-mask bits 41/42 and copies all
                # resources. These fields are assignments, not increments.
                states[entity] = [_integer(struct.unpack_from('>f', payload, offset)[0])
                                  for offset in (298, 302, 306, 310)]
                problems.pop(entity, None)
                continue
            attribute = record.opcode == 0x041c
            index_offset = 12 if attribute else 8
            if len(payload) <= index_offset:
                raise ValueError('short stat payload lacks index')
            index = payload[index_offset]
            indices = (41, 42) if attribute else (11, 14)
            if index not in indices:
                continue
            if record.content_length != (24 if attribute else 16):
                raise ValueError(f'unsupported stat content length {record.content_length}')
            if attribute and payload[13] != 0:
                if payload[13] >= 3:
                    persistent_layers[entity] = f'{location}: unsupported attribute layer {payload[13]}'
                raise ValueError(f'unsupported attribute layer {payload[13]}')
            if entity not in states:
                continue
            value = _integer(struct.unpack_from('>f', payload, 8 if attribute else 4)[0], signed=True)
            mode = payload[14 if attribute else 9]
            slot = indices.index(index) + (0 if attribute else 2)
            updated = states[entity][slot] + value if mode == 0 else value
            if attribute and updated < 0:
                raise ValueError('negative attribute count requires unproved clamp bounds')
            states[entity][slot] = updated if attribute else max(updated, 0)
        except ValueError as exc:
            problems[entity] = f'{location}: {exc}'
    missing = [entity for entity in ids if entity not in states]
    if missing:
        if any(entity in problems for entity in missing):
            return invalid('unsupported_state', '; '.join(problems[entity] for entity in missing if entity in problems))
        return invalid('missing_baseline', f'no applicable native baseline for actors {missing}')
    problems.update(persistent_layers)
    if problems:
        return invalid('unsupported_state', '; '.join(problems[entity] for entity in sorted(problems)))
    players = tuple(NativePlayerStats(entity, *states[entity]) for entity in ids)
    return NativeStatsResult(True, 'accepted', 'native state observed; match completion not asserted',
                             players, requested, audit.first_game_time, audit.last_game_time,
                             query.as_of_game_time, query.applied_game_time, query.record_boundary)
