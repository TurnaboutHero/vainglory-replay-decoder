"""Replay completeness and signal extraction for decoder_v2."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import List, Sequence, Tuple

from vg.core.kda_detector import KDADetector
from vg.core.stat_evidence import inspect_replay_evidence
from vg.core.unified_decoder import _le_to_be
from vg.core.vgr_parser import VGRParser
from vg.core.vgr_records import VGRRecordError, iter_records

from .models import CompletenessAssessment, CompletenessStatus, ReplaySignalSummary


def load_frames(replay_file: str) -> List[Tuple[int, bytes]]:
    """Load replay frames as `(frame_index, bytes)` tuples."""
    replay_path = Path(replay_file)
    frame_dir = replay_path.parent
    replay_name = replay_path.stem.rsplit(".", 1)[0]
    return [
        (int(frame.stem.split(".")[-1]), frame.read_bytes())
        for frame in sorted(frame_dir.glob(f"{replay_name}.*.vgr"), key=lambda p: int(p.stem.split(".")[-1]))
    ]


def _scan_record_tails(
    frames: Sequence[Tuple[int, bytes]],
) -> tuple[float | None, float | None, float | None]:
    """Read legacy candidate tails from owning records, never neighboring bytes.

    A malformed frame invalidates all candidate tails, including earlier ones.
    Candidate labels/ranges remain heuristics, not native terminal semantics.
    """
    death_times: list[float] = []
    item_times: list[float] = []
    crystal_times: list[float] = []
    try:
        for _, data in frames:
            for record in iter_records(data):
                if record.opcode == 0x0431 and record.content_length == 8:
                    reference = struct.unpack_from(">I", record.payload)[0]
                    if reference > 0xFFFF or record.payload[4:] != b"\x00\x00":
                        continue
                    if 0 < record.timestamp < 5000:
                        death_times.append(record.timestamp)
                    if 2000 <= reference <= 2005 and 60 < record.timestamp < 2400:
                        crystal_times.append(record.timestamp)
                if record.opcode == 0x043D and record.content_length == 16:
                    reference = struct.unpack_from(">I", record.payload)[0]
                    if reference <= 0xFFFF and 0 < record.timestamp < 5000:
                        item_times.append(record.timestamp)
    except VGRRecordError:
        # inspect_native_clock reports the framing failure to the public gate.
        return None, None, None
    return (max(death_times, default=None), max(item_times, default=None),
            max(crystal_times, default=None))


def extract_replay_signals(replay_file: str) -> ReplaySignalSummary:
    """Extract timing/completeness signals from a replay."""
    parser = VGRParser(replay_file, auto_truth=False)
    parsed = parser.parse()
    frames = load_frames(replay_file)

    valid_eids = {
        _le_to_be(player["entity_id"])
        for team in ("left", "right")
        for player in parsed["teams"][team]
        if player.get("entity_id")
    }

    evidence = inspect_replay_evidence(frames)
    clock = evidence.native_clock
    detector = KDADetector(valid_eids)
    if clock.status != "malformed_records":
        for frame_idx, data in frames:
            try:
                detector.process_frame(frame_idx, data)
            except VGRRecordError:
                detector = KDADetector(valid_eids)
                break

    max_kill_ts = max((event.timestamp for event in detector.kill_events if event.timestamp is not None), default=None)
    max_player_death_ts = max((event.timestamp for event in detector.death_events), default=None)
    max_death_header_ts, max_item_ts, crystal_ts = _scan_record_tails(frames)

    return ReplaySignalSummary(
        replay_name=parsed["replay_name"],
        replay_file=parsed["replay_file"],
        frame_count=len(frames),
        max_frame_index=frames[-1][0] if frames else 0,
        crystal_ts=crystal_ts,
        max_kill_ts=max_kill_ts,
        max_player_death_ts=max_player_death_ts,
        max_death_header_ts=max_death_header_ts,
        max_item_ts=max_item_ts,
        native_clock_valid=clock.valid,
        native_clock_status=clock.status,
        native_clock_reason=clock.reason,
        first_game_time=clock.first_game_time,
        last_game_time=clock.last_game_time,
        replay_scope=evidence.replay_scope,
        recording_valid=evidence.recording_valid,
        recording_reason=evidence.recording_reason,
        terminal_requests=evidence.terminal_requests,
    )


def assess_completeness(signals: ReplaySignalSummary) -> CompletenessAssessment:
    """Apply a conservative completeness heuristic."""
    if signals.native_clock_valid is False:
        return CompletenessAssessment(
            status=CompletenessStatus.COMPLETENESS_UNKNOWN,
            reason=f"Native clock integrity failed ({signals.native_clock_status}): {signals.native_clock_reason}",
            signals=signals,
        )

    crystal_ts = signals.crystal_ts
    max_death_ts = signals.max_player_death_ts
    max_death_header_ts = signals.max_death_header_ts
    max_item_ts = signals.max_item_ts

    if signals.frame_count < 20:
        return CompletenessAssessment(
            status=CompletenessStatus.INCOMPLETE_CONFIRMED,
            reason="Tiny replay snippet lacks enough signal to represent a full match.",
            signals=signals,
        )

    if (
        crystal_ts is not None
        and max_death_ts is not None
        and abs(crystal_ts - max_death_ts) <= 30
    ):
        return CompletenessAssessment(
            status=CompletenessStatus.COMPLETENESS_UNKNOWN,
            reason="Terminal crystal candidate agrees with the player-death tail; this heuristic does not confirm completion.",
            signals=signals,
        )

    if (
        crystal_ts is not None
        and max_death_header_ts is not None
        and max_item_ts is not None
        and signals.frame_count >= 180
        and crystal_ts >= 1800
        and abs(max_death_header_ts - crystal_ts) <= 30
        and abs(max_item_ts - crystal_ts) <= 60
        and (max_death_ts is None or (crystal_ts - max_death_ts) >= 100)
    ):
        return CompletenessAssessment(
            status=CompletenessStatus.COMPLETENESS_UNKNOWN,
            reason="Late crystal candidate and activity tails agree; these heuristics do not confirm completion.",
            signals=signals,
        )

    if (
        crystal_ts is None
        and max_death_ts is not None
        and max_death_header_ts is not None
        and max_death_ts < 600
        and (max_death_header_ts - max_death_ts) > 300
        and signals.frame_count < 90
    ):
        return CompletenessAssessment(
            status=CompletenessStatus.INCOMPLETE_CONFIRMED,
            reason="No crystal death, short frame count, and large gap between player-death tail and generic death-header tail.",
            signals=signals,
        )

    return CompletenessAssessment(
        status=CompletenessStatus.COMPLETENESS_UNKNOWN,
        reason="No corroborated terminal crystal evidence; aligned activity tails do not confirm match completion.",
        signals=signals,
    )
