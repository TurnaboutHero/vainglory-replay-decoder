"""Shared audited record selection for native state readers.

The legacy as-of query time and actual applied-record time are distinct.
EOF traverses every record, including events projected past a paused endpoint.
"""

from dataclasses import dataclass
import math
import struct
from typing import Iterator, Sequence

from vg.core.vgr_records import VGRRecord, VGRRecordError, iter_records


@dataclass(frozen=True, slots=True)
class GameTime:
    seconds: float


@dataclass(frozen=True, slots=True)
class RecordTime:
    seconds: float


@dataclass(frozen=True, slots=True)
class ClockAudit:
    valid: bool
    status: str
    reason: str
    first_game_time: float | None = None
    last_game_time: float | None = None
    game_time_mapping_valid: bool = True


@dataclass(frozen=True, slots=True)
class _Frame:
    number: int
    records: tuple[VGRRecord, ...]
    anchor_record_time: float
    anchor_game_time: float

    def game_time(self, record_time: float) -> float:
        return self.anchor_game_time + record_time - self.anchor_record_time


def _scan_clock(frames: Sequence[tuple[int, bytes]], *, allow_forward_jumps: bool = False) -> tuple[ClockAudit, tuple[_Frame, ...]]:
    parsed = []
    previous_time = None
    mapping_failure = None
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
            detail = (f'frames {previous.number} -> {number}: game clock delta '
                      f'{game_delta:.6f}, record delta {record_delta:.6f}')
            if game_delta < -1:
                return ClockAudit(False, 'mixed_segments', detail), ()
            if game_delta - record_delta > 5:
                if not allow_forward_jumps:
                    return ClockAudit(False, 'unsupported_clock', detail), ()
                mapping_failure = mapping_failure or detail
        parsed.append(current)
    if not parsed:
        return ClockAudit(False, 'malformed_records', 'no frames'), ()
    if mapping_failure:
        return ClockAudit(True, 'record_order_only',
                          f'native record order is valid; game-time mapping unavailable: {mapping_failure}',
                          game_time_mapping_valid=False), tuple(parsed)
    first = parsed[0].game_time(parsed[0].records[0].timestamp)
    last = parsed[-1].game_time(parsed[-1].records[-1].timestamp)
    return ClockAudit(True, 'accepted', 'continuous native clock anchors', first, last), tuple(parsed)


@dataclass(frozen=True, slots=True)
class NativeQuery:
    valid: bool
    status: str
    reason: str
    audit: ClockAudit
    frames: tuple[_Frame, ...]
    cutoff: GameTime | RecordTime | None
    requested_game_time: float | None = None
    as_of_game_time: float | None = None
    applied_game_time: float | None = None
    record_boundary: tuple[int, int] | None = None

    def includes(self, frame: _Frame, record: VGRRecord) -> bool:
        """Keep record-order traversal and the existing per-frame time mapping."""
        if isinstance(self.cutoff, RecordTime):
            return record.timestamp <= self.cutoff.seconds
        if isinstance(self.cutoff, GameTime):
            return frame.game_time(record.timestamp) <= self.cutoff.seconds
        return True

    def records(self) -> Iterator[tuple[int, VGRRecord]]:
        """Yield only validated selected records without allocating another copy."""
        if self.valid:
            for frame in self.frames:
                for record in frame.records:
                    if self.includes(frame, record):
                        yield frame.number, record


def select_native_query(
    frames: Sequence[tuple[int, bytes]],
    cutoff: GameTime | RecordTime | None = None,
) -> NativeQuery:
    """Audit full input, then select an inclusive native time boundary."""
    audit, parsed = _scan_clock(frames, allow_forward_jumps=not isinstance(cutoff, GameTime))
    requested = cutoff.seconds if isinstance(cutoff, GameTime) else None

    def invalid(status: str, reason: str) -> NativeQuery:
        return NativeQuery(False, status, reason, audit, (), cutoff,
                           requested_game_time=requested)

    if not audit.valid:
        return invalid(audit.status, audit.reason)
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
        requested = selected.game_time(cutoff.seconds) if audit.game_time_mapping_valid else None
    target = audit.last_game_time if cutoff is None else requested
    if audit.game_time_mapping_valid and (target is None or audit.first_game_time is None or audit.last_game_time is None):
        return invalid('unsupported_clock', 'no game-time coverage')
    if isinstance(cutoff, GameTime) and not audit.first_game_time <= target <= audit.last_game_time:
        return invalid('out_of_coverage', 'game-time cutoff is outside recorded coverage')
    reason = 'audited native record selection' if audit.game_time_mapping_valid else audit.reason
    query = NativeQuery(True, 'accepted', reason,
                        audit, parsed, cutoff, requested, target)
    if isinstance(cutoff, GameTime):
        excluded = False
        for frame in parsed:
            for record in frame.records:
                included = query.includes(frame, record)
                if included and excluded:
                    return invalid('ambiguous_game_time',
                                   'game-time cutoff selects later records after excluding an earlier record')
                excluded = excluded or not included
    for frame in reversed(parsed):
        for record in reversed(frame.records):
            if query.includes(frame, record):
                return NativeQuery(True, 'accepted', query.reason, audit, parsed, cutoff,
                                   requested, target, frame.game_time(record.timestamp) if audit.game_time_mapping_valid else None,
                                   (frame.number, record.offset))
    return invalid('out_of_coverage', 'query includes no recorded boundary')
