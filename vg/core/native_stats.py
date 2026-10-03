"""Observed scoreboard state from native snapshots and stat updates.

An accepted result describes the requested recorded state, not match completion.
Clock interpolation uses the 046f anchor in each numbered frame. Resource 14
is exposed as minion_kills for existing callers; its native display label is
not independently established by this reader.
"""

from dataclasses import dataclass
import math
import struct
from typing import Collection, Sequence

from vg.core.vgr_records import VGRRecord, VGRRecordError, iter_records


@dataclass(frozen=True, slots=True)
class GameTime:
    seconds: float


@dataclass(frozen=True, slots=True)
class RecordTime:
    seconds: float


@dataclass(frozen=True, slots=True)
class NativePlayerStats:
    entity_id: int
    kills: int
    deaths: int
    assists: int
    minion_kills: int


@dataclass(frozen=True, slots=True)
class ClockAudit:
    valid: bool
    status: str
    reason: str
    first_game_time: float | None = None
    last_game_time: float | None = None


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


@dataclass(frozen=True, slots=True)
class _Frame:
    number: int
    records: tuple[VGRRecord, ...]
    anchor_record_time: float
    anchor_game_time: float

    def game_time(self, record_time: float) -> float:
        return self.anchor_game_time + record_time - self.anchor_record_time


def _scan_clock(frames: Sequence[tuple[int, bytes]]) -> tuple[ClockAudit, tuple[_Frame, ...]]:
    parsed = []
    previous_time = None
    for number, data in frames:
        if parsed and number != parsed[-1].number + 1:
            return ClockAudit(False, 'mixed_segments',
                              f'nonconsecutive frame numbers {parsed[-1].number} -> {number}'), ()
        try:
            records = tuple(iter_records(data))
        except VGRRecordError as exc:
            return ClockAudit(False, 'malformed_records', f'frame {number}: {exc}'), ()
        if not records:
            return ClockAudit(False, 'malformed_records', f'frame {number}: no records'), ()
        for record in records:
            if record.timestamp < 0 or (previous_time is not None and record.timestamp < previous_time):
                return ClockAudit(False, 'mixed_segments',
                                  f'frame {number} offset {record.offset}: disordered record time '
                                  f'{previous_time} -> {record.timestamp}'), ()
            previous_time = record.timestamp
        anchors = [r for r in records if r.opcode == 0x046f]
        if len(anchors) != 1 or len(anchors[0].payload) != 69:
            return ClockAudit(False, 'unsupported_clock',
                              f'frame {number}: expected one 046f anchor with 69-byte payload'), ()
        anchor = anchors[0]
        clock = struct.unpack_from('>f', anchor.payload, 64)[0]
        if not math.isfinite(clock) or clock < 0:
            return ClockAudit(False, 'unsupported_clock', f'frame {number}: invalid game clock {clock}'), ()
        current = _Frame(number, records, anchor.timestamp, clock)
        if parsed:
            previous = parsed[-1]
            game_delta = clock - previous.anchor_game_time
            record_delta = anchor.timestamp - previous.anchor_record_time
            if game_delta < -1 or game_delta - record_delta > 5:
                status = 'mixed_segments' if game_delta < -1 else 'unsupported_clock'
                return ClockAudit(False, status,
                                  f'frames {previous.number} -> {number}: game clock delta '
                                  f'{game_delta:.6f}, record delta {record_delta:.6f}'), ()
        parsed.append(current)
    if not parsed:
        return ClockAudit(False, 'malformed_records', 'no frames'), ()
    first = parsed[0].game_time(parsed[0].records[0].timestamp)
    last = parsed[-1].game_time(parsed[-1].records[-1].timestamp)
    return ClockAudit(True, 'accepted', 'continuous native clock anchors', first, last), tuple(parsed)


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
    Relevant semantic failures only affect state at or before the query. A later
    full snapshot replaces earlier values, exactly as native baseline assignment
    does. Missing baselines are never manufactured from zero.
    EOF includes every record; RecordTime filters only on record timestamps.
    First/last game times describe endpoints, not global interpolation extrema.
    """
    audit, parsed = _scan_clock(frames)
    requested = cutoff.seconds if isinstance(cutoff, GameTime) else None

    def invalid(status: str, reason: str) -> NativeStatsResult:
        return NativeStatsResult(False, status, reason, requested_game_time=requested,
                                 first_game_time=audit.first_game_time, last_game_time=audit.last_game_time)

    if not audit.valid:
        return invalid(audit.status, audit.reason)
    supplied = tuple(player_ids)
    if not supplied:
        return invalid('missing_baseline', 'no player identities supplied')
    if any(not isinstance(entity, int) or isinstance(entity, bool)
           or not 0 < entity <= 0xffffffff for entity in supplied):
        return invalid('invalid_query', 'player identities must be positive unsigned 32-bit integers')
    if len(set(supplied)) != len(supplied):
        return invalid('invalid_query', 'player identities must be unique')
    ids = sorted(supplied)
    if cutoff is not None and (not isinstance(cutoff, (GameTime, RecordTime))
                               or not math.isfinite(cutoff.seconds)):
        return invalid('invalid_query', 'cutoff must be a finite GameTime or RecordTime')
    if isinstance(cutoff, RecordTime):
        if not parsed[0].records[0].timestamp <= cutoff.seconds <= parsed[-1].records[-1].timestamp:
            return invalid('out_of_coverage', 'record-time cutoff is outside recorded coverage')
        selected = parsed[0]
        for frame in parsed:
            if frame.records[0].timestamp <= cutoff.seconds:
                selected = frame
        requested = selected.game_time(cutoff.seconds)
    target = audit.last_game_time if cutoff is None else requested
    if target is None or audit.first_game_time is None or audit.last_game_time is None:
        return invalid('unsupported_clock', 'no game-time coverage')
    if isinstance(cutoff, GameTime) and not audit.first_game_time <= target <= audit.last_game_time:
        return invalid('out_of_coverage', 'game-time cutoff is outside recorded coverage')

    states: dict[int, list[int]] = {}
    problems: dict[int, str] = {}
    persistent_layers: dict[int, str] = {}
    wanted = set(ids)
    for frame in parsed:
        for record in frame.records:
            if (isinstance(cutoff, RecordTime) and record.timestamp > cutoff.seconds) or (
                isinstance(cutoff, GameTime) and frame.game_time(record.timestamp) > target
            ):
                continue
            payload = record.payload
            if record.opcode == 0x03f3:
                ref_offset = 8
            elif record.opcode in (0x041c, 0x041d):
                ref_offset = 0
            else:
                continue
            location = f'frame {frame.number} offset {record.offset} opcode {record.opcode:04x}'
            if len(payload) < ref_offset + 4:
                for entity in ids:
                    problems[entity] = f'{location}: cannot identify actor in short payload'
                continue
            entity = struct.unpack_from('>I', payload, ref_offset)[0]
            if entity not in wanted:
                continue
            try:
                if record.opcode == 0x03f3:
                    if len(payload) not in (746, 750):
                        raise ValueError(f'unsupported snapshot length {len(payload)}')
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
                        # Snapshots replace only three arrays; they do not prove
                        # that the fourth layer or an unknown layer is reset.
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
                             players, requested, audit.first_game_time, audit.last_game_time, target)
