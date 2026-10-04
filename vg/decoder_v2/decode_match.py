"""Conservative match export for decoder_v2."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from vg.core.vgr_parser import VGRParser
from vg.core.replay_input import ReplayInputError, replay_sections, select_replay
from vg.core.vgr_records import VGRRecordError
from vg.core.stat_evidence import final_field_reason, inspect_replay_evidence
from vg.core.unified_decoder import _le_to_be
from .completeness import load_frames
from vg.core.replay_output import (
    ReplayOutputError, ReportInputs, validate_replay_output,
    validate_report_outputs, write_report_output,
)

from .gold import decode_gold_from_replay
from .kda import decode_kda_from_replay
from .minions import collect_minion_candidates
from .models import (AcceptedPlayerFields, DecoderV2MatchOutput, FieldDecision,
                     )
from .winner import decode_winner_from_replay
from .player_state import decode_player_state


def decode_match(replay_file: str, *, at_game_time: Optional[float] = None) -> DecoderV2MatchOutput:
    """Export scoped native captures; final fields require independent validation."""
    replay_file = str(select_replay(replay_file))
    parsed = VGRParser(replay_file, auto_truth=False).parse()
    match_info = parsed["match_info"]
    evidence = inspect_replay_evidence(load_frames(replay_file))
    capture = at_game_time is not None
    kda_result = decode_kda_from_replay(replay_file, at_game_time=at_game_time)
    assessment = kda_result.assessment
    duration_estimate = kda_result.duration_estimate
    if not capture:
        winner_result = decode_winner_from_replay(replay_file)
        assessment = winner_result.assessment
        duration_estimate = winner_result.duration_estimate

    roster = [player for side in ("left", "right") for player in parsed["teams"][side]]
    ids = [player.get("entity_id") for player in roster]
    valid_ids = all(isinstance(eid, int) and not isinstance(eid, bool) and 0 < eid <= 0xFFFF
                    for eid in ids)
    identity_ok = bool(ids) and valid_ids and len(set(ids)) == len(ids)
    identity_reason = None if identity_ok else "Player IDs are missing, invalid or duplicated in this recording."
    capture_ids = [row.entity_id_be for row in kda_result.players]
    capture_ok = (
        capture and identity_ok and evidence.recording_valid and evidence.native_clock.valid
        and kda_result.accepted and kda_result.scope == "capture"
        and kda_result.at_game_time == at_game_time
        and kda_result.replay_scope == evidence.replay_scope
        and len(capture_ids) == len(ids) and len(set(capture_ids)) == len(capture_ids)
        and set(capture_ids) == {_le_to_be(eid) for eid in ids}
        and all(row.replay_scope == evidence.replay_scope for row in kda_result.players)
    )
    capture_reason = None
    if capture and not capture_ok:
        if not evidence.recording_valid:
            capture_reason = evidence.recording_reason
        elif not evidence.native_clock.valid:
            capture_reason = evidence.native_clock.reason
        elif not identity_ok:
            capture_reason = identity_reason
        elif not kda_result.accepted:
            capture_reason = kda_result.reason
        else:
            capture_reason = 'Capture scope, requested time or player roster does not match this recording.'
    kda_by_id = {row.entity_id_be: row for row in kda_result.players} if capture_ok else {}
    players: List[AcceptedPlayerFields] = []
    for player in roster:
        eid = player.get("entity_id")
        eid_be = _le_to_be(eid) if isinstance(eid, int) and not isinstance(eid, bool) and 0 < eid <= 0xFFFF else None
        native = kda_by_id.get(eid_be)
        players.append(AcceptedPlayerFields(
            name=player["name"], team=player.get("team", "unknown"),
            entity_id=eid, hero_name=player.get("hero_name", "Unknown"),
            kills=native.kills if native else None,
            deaths=native.deaths if native else None,
            assists=native.assists if native else None,
            gold=None, gold_status=None if capture else "withheld_final_validation_missing",
            entity_id_be=eid_be, replay_scope=evidence.replay_scope,
            identity_status="recording_scoped" if identity_ok else "invalid",
            identity_reason=identity_reason,
        ))

    accepted_fields: Dict[str, FieldDecision] = {}
    withheld_fields: Dict[str, FieldDecision] = {}
    metadata = {
        "hero": identity_ok and all(p.hero_name != "Unknown" for p in players),
        "team_grouping": identity_ok and all(p.team in ("left", "right") for p in players),
        "entity_id": identity_ok,
    }
    for field, valid in metadata.items():
        target = accepted_fields if valid else withheld_fields
        target[field] = FieldDecision(
            value="accepted" if valid else None, claim_status="confirmed" if valid else "unknown",
            accepted_for_index=valid, claim_id=f"player_block.{field}",
            reason=None if valid else (identity_reason or "Player metadata is unknown."),
            evidence_status="recorded_player_block" if valid else "unverified", scope="identity",
        )
    for field in ("winner", "gold"):
        withheld_fields[field] = FieldDecision(
            value=None, claim_status="unknown", accepted_for_index=False,
            claim_id=f"{field}.complete_match", reason=final_field_reason(field),
        )
    for field in ("kills", "deaths", "assists"):
        target = accepted_fields if capture_ok else withheld_fields
        target[field] = FieldDecision(
            value="accepted" if capture_ok else None,
            claim_status="strong" if capture_ok else "unknown", accepted_for_index=False,
            claim_id=f"{field}.capture" if capture else f"{field}.complete_match",
            reason=None if capture_ok else (capture_reason if capture else final_field_reason(field)),
            evidence_status="native_capture_observed" if capture_ok else "unverified",
            scope="capture" if capture else "final",
        )
    withheld_fields["minion_kills"] = FieldDecision(
        None, "partial", False, "minion_kills.complete_match",
        "Withheld: field is still partial in decoder_v2.",
    )
    withheld_fields["duration_seconds"] = FieldDecision(
        None if capture else duration_estimate.estimate_seconds, "partial", False,
        "duration.approximate",
        ('Withheld: a capture does not establish final duration.' if capture else
         f'Withheld: duration is still approximate in decoder_v2 (source: {duration_estimate.source}).'),
    )
    return DecoderV2MatchOutput(
        schema_version="decoder_v2.capture.v2" if capture else "decoder_v2.match.v2",
        replay_name=parsed["replay_name"], replay_file=parsed["replay_file"],
        game_mode=match_info["mode"], map_name=match_info["map_name"],
        team_size=match_info["team_size"], completeness_status=assessment.status.value,
        completeness_reason=assessment.reason, accepted_fields=accepted_fields,
        withheld_fields=withheld_fields, players=tuple(players),
        scope="capture" if capture else "final", at_game_time=at_game_time,
        as_of_game_time=kda_result.as_of_game_time if capture_ok else None,
        replay_scope=evidence.replay_scope, evidence=evidence,
    )


def decode_match_debug(replay_file: str, *, at_game_time: Optional[float] = None) -> Dict[str, object]:
    """Decode a replay with research/debug details included."""
    replay_file = str(select_replay(replay_file))
    if at_game_time is not None:
        safe_output = decode_match(replay_file, at_game_time=at_game_time)
        kda_result = decode_kda_from_replay(replay_file, at_game_time=at_game_time)
        return {
            "schema_version": "decoder_v2.debug_capture.v2",
            "safe_output": safe_output.to_dict(),
            "completeness": kda_result.assessment.to_dict(),
            "duration": None,
            "winner_debug": None,
            "kda_debug": kda_result.to_dict(),
            "gold_debug": None,
            "minion_candidates": [],
        }
    safe_output = decode_match(replay_file)
    winner_result = decode_winner_from_replay(replay_file)
    kda_result = decode_kda_from_replay(replay_file)
    gold_result = decode_gold_from_replay(replay_file, assessment=winner_result.assessment)
    minion_candidates = collect_minion_candidates(replay_file)

    return {
        "schema_version": "decoder_v2.debug_match.v2",
        "safe_output": safe_output.to_dict(),
        "completeness": winner_result.assessment.to_dict(),
        "duration": winner_result.duration_estimate.to_dict(),
        "winner_debug": winner_result.to_dict(),
        "kda_debug": kda_result.to_dict(),
        "gold_debug": gold_result.to_dict(),
        "minion_candidates": [item.to_dict() for item in minion_candidates],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Decode native recorded player state, or request explicit final-safe/debug output.")
    parser.add_argument("replay_file", help="Path to .0.vgr replay file")
    parser.add_argument(
        "--format",
        choices=("state-json", "safe-json", "debug-json"),
        default="state-json",
        help="state-json (default) reports native recorded state; safe-json retains conservative final decisions",
    )
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    parser.add_argument("--at-game-time", type=float, help="Capture all supported fields at game-clock seconds; does not assert match completion.")
    args = parser.parse_args(argv)
    if args.at_game_time is not None and (not math.isfinite(args.at_game_time) or args.at_game_time < 0):
        parser.error("--at-game-time must be finite and non-negative")
    try:
        output = Path(args.output) if args.output else None
        if output is not None and not Path(args.replay_file).is_dir():
            validate_replay_output(Path(args.replay_file), output)
        replay = select_replay(args.replay_file)
        sections = replay_sections(replay)
        inputs = ReportInputs(files=tuple(path for _, path in sections), replays=(replay,))
        if output is not None:
            for candidate in (output, output.resolve()):
                if (candidate.parent.resolve() == replay.parent.resolve()
                        and candidate.name.startswith(replay.name[:-6] + '.')
                        and candidate.name.endswith('.vgr')):
                    raise ReplayOutputError(output, 'output names a sibling input .vgr section')
            validate_report_outputs(inputs, (output,))
        if args.format == "debug-json":
            payload_obj = decode_match_debug(str(replay), at_game_time=args.at_game_time)
        elif args.format == "state-json":
            payload_obj = decode_player_state(str(replay), at_game_time=args.at_game_time).to_dict()
        else:
            payload_obj = decode_match(str(replay), at_game_time=args.at_game_time).to_dict()
        if replay_sections(replay) != sections:
            raise ReplayOutputError(replay, 'Replay section set changed after preflight', 'input_changed')
        payload = json.dumps(payload_obj, indent=2, ensure_ascii=False)
        if output is not None:
            write_report_output(inputs, output, payload)
            print(f"decoder_v2 output saved to {output}")
        else:
            inputs.recheck()
            print(payload)
    except (ReplayInputError, ReplayOutputError, VGRRecordError, OSError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
