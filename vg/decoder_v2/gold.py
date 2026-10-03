"""Strict resource observations and partial gold estimates for decoder_v2."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Optional, assert_never

from vg.core.stat_evidence import final_field_reason, frame_scope
from vg.core.unified_decoder import _le_to_be
from vg.core.vgr_parser import VGRParser
from vg.core.vgr_records import VGRRecordError, iter_records

from .completeness import assess_completeness, extract_replay_signals, load_frames
from .credit_events import credit_event_from_record
from .models import CompletenessAssessment, CompletenessStatus, GoldExtractionResult, GoldPlayerSummary


def _status_for_assessment(assessment: CompletenessAssessment) -> str:
    match assessment.status:
        case CompletenessStatus.INCOMPLETE_CONFIRMED:
            return "partial_incomplete_replay"
        case CompletenessStatus.COMPLETE_CONFIRMED | CompletenessStatus.COMPLETENESS_UNKNOWN:
            return "partial_final_validation_missing"
        case unreachable:
            assert_never(unreachable)


def decode_gold_from_replay(
    replay_file: str,
    assessment: Optional[CompletenessAssessment] = None,
) -> GoldExtractionResult:
    """Keep the legacy income formula partial; recording coverage cannot validate final gold."""
    if assessment is None:
        assessment = assess_completeness(extract_replay_signals(replay_file))

    frames = load_frames(replay_file)
    replay_scope = frame_scope(frames)
    reason = final_field_reason('gold')
    if assessment.signals.replay_scope is not None and assessment.signals.replay_scope != replay_scope:
        return GoldExtractionResult(False, reason, assessment, replay_scope=replay_scope,
                                    record_issues=("Recording differs from supplied assessment.",))
    parsed = VGRParser(replay_file, auto_truth=False).parse()
    roster = [(team, player) for team in ("left", "right")
              for player in parsed.get("teams", {}).get(team, [])]
    ids = [player.get("entity_id") for _, player in roster]
    if not ids or any(not isinstance(eid, int) or isinstance(eid, bool) or not 0 < eid <= 0xFFFF for eid in ids):
        return GoldExtractionResult(False, reason, assessment, replay_scope=replay_scope,
                                    record_issues=("Missing or invalid player entity ID.",))
    if len(ids) != len(set(ids)):
        return GoldExtractionResult(False, reason, assessment, replay_scope=replay_scope,
                                    record_issues=("Duplicate player entity IDs.",))
    valid_ids = {_le_to_be(eid) for eid in ids}

    income: Dict[int, float] = defaultdict(float)
    last_set: Dict[int, float] = {}
    set_counts: Counter[int] = Counter()
    spent: Dict[int, float] = defaultdict(float)
    counts: Counter[int] = Counter()
    invalid_ids: set[int] = set()
    issues: list[str] = []
    malformed = False

    for frame_idx, data in frames:
        try:
            for record in iter_records(data):
                if record.opcode != 0x041D:
                    continue
                try:
                    event = credit_event_from_record(record, frame_idx)
                except VGRRecordError as exc:
                    issues.append(str(exc))
                    malformed = True
                    continue
                if event.entity_id_be not in valid_ids or event.action != 0x06:
                    continue
                if event.value is None or event.operation not in (0, 1):
                    invalid_ids.add(event.entity_id_be)
                    issues.append(f"frame {frame_idx} offset {record.offset}: unsupported gold value/operation.")
                    continue
                counts[event.entity_id_be] += 1
                if event.operation == 1:
                    last_set[event.entity_id_be] = event.value
                    set_counts[event.entity_id_be] += 1
                elif event.value > 0:
                    income[event.entity_id_be] += event.value
                elif event.value < 0:
                    spent[event.entity_id_be] += abs(event.value)
        except VGRRecordError as exc:
            issues.append(f"frame {frame_idx}: {exc}")
            malformed = True

    gold_status = _status_for_assessment(assessment)
    players = []
    for team_label, player in roster:
        eid = _le_to_be(player["entity_id"])
        supported = not malformed and eid not in invalid_ids and counts[eid] > 0
        players.append(GoldPlayerSummary(
            player_name=str(player.get("name")), team=str(player.get("team") or team_label),
            hero_name=str(player.get("hero_name") or "Unknown"),
            gold=600 + round(income[eid]) if supported else None,
            gold_status=gold_status if supported else "partial_unsupported_credit_records",
            action_06_income=round(income[eid], 4),
            action_06_sellback_refund=None,
            action_06_spent=round(spent[eid], 4),
            entity_id_be=eid, replay_scope=replay_scope, record_count=counts[eid],
            action_06_last_set_value=last_set.get(eid),
            action_06_set_count=set_counts[eid],
        ))

    return GoldExtractionResult(
        accepted=False,
        reason=reason,
        assessment=assessment,
        players=tuple(players),
        replay_scope=replay_scope,
        record_issues=tuple(issues),
    )
