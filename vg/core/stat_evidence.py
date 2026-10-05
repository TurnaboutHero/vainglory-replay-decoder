"""Recording observations that cannot substitute for final-screen validation."""

from dataclasses import dataclass
import hashlib
import struct
from typing import Final, Sequence

from vg.core.native_stats import ClockAudit, inspect_native_clock
from vg.core.vgr_records import VGRRecordError, iter_records

FINAL_VALIDATION_STATUS: Final = "unverified"


@dataclass(frozen=True, slots=True)
class EndMatchObservation:
    frame_index: int
    record_offset: int
    record_time: float
    winning_team_raw: int
    end_reason: int
    request_status: str


@dataclass(frozen=True, slots=True)
class ReplayEvidence:
    replay_scope: str
    recording_valid: bool
    recording_reason: str
    native_clock: ClockAudit
    terminal_requests: tuple[EndMatchObservation, ...]
    final_validation_status: str = FINAL_VALIDATION_STATUS


def frame_scope(frames: Sequence[tuple[int, bytes]]) -> str:
    """Bind an identity to the contents and numbering of this replay series."""
    digest = hashlib.sha256(b"vgr-numbered-series-v1\x00")
    for number, data in frames:
        digest.update(struct.pack(">QQ", number, len(data)))
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def final_field_reason(field: str) -> str:
    """Explain why recording observations do not authorize a final field."""
    return (f"Final {field} withheld: source-bound final-screen validation is missing; "
            "recording coverage, native clock and queued end-match requests are separate observations.")


def _end_requests(number: int, records) -> list[EndMatchObservation]:
    found = []
    for record in records:
        if record.opcode == 0x03F1 and record.content_length == 8:
            end_reason = record.payload[4]
            status = ("validation_error" if end_reason in (5, 6, 7) else
                      "no_op" if end_reason == 8 else "queued_request")
            found.append(EndMatchObservation(number, record.offset, record.timestamp,
                                             struct.unpack_from(">I", record.payload)[0], end_reason, status))
    return found


def end_match_requests(frames: Sequence[tuple[int, bytes]]) -> tuple[EndMatchObservation, ...]:
    """Queued 03f1 requests in readable sections, without the clock audit."""
    found = []
    for number, data in frames:
        try:
            found.extend(_end_requests(number, iter_records(data)))
        except VGRRecordError:
            continue
    return tuple(found)


def inspect_replay_evidence(frames: Sequence[tuple[int, bytes]]) -> ReplayEvidence:
    """Keep structural, clock and terminal-request evidence independent."""
    valid = bool(frames) and frames[0][0] == 0
    reason = "Numbered recording begins at zero; framing and section sequence are valid."
    if not valid:
        reason = "Recording has no sections or does not begin at section zero."
    previous = None
    terminal = []
    for number, data in frames:
        if previous is not None and number != previous + 1:
            valid = False
            reason = f"Recording section gap: {previous} -> {number}."
        previous = number
        try:
            records = tuple(iter_records(data))
        except VGRRecordError as exc:
            valid = False
            reason = f"Section {number}: {exc}"
            continue
        if not records:
            valid = False
            reason = f"Section {number} contains no records."
        terminal.extend(_end_requests(number, records))
    return ReplayEvidence(frame_scope(frames), valid, reason,
                          inspect_native_clock(frames), tuple(terminal))
