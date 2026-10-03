"""Summarize HackedGlory-style XP/level evidence against local VGR signals."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from vg.core.replay_output import validate_report_outputs, write_report_output
from .report_inputs import prepare_truth_inputs, truth_replay_files

from .action02_subfamily_summary import build_action02_subfamily_summary
from .level_signal_probe import build_level_signal_batch


REWARD_LABELS = {
    "shared_reward_candidate",
    "solo_reward_candidate",
    "mixed_reward_candidate",
}


def _summarize_action02(report: Dict[str, object]) -> Dict[str, object]:
    rows = [row for row in report.get("rows", []) if isinstance(row, dict)]
    label_counts = Counter(str(row.get("subfamily_label")) for row in rows)
    label_event_counts = Counter()
    for row in rows:
        label_event_counts[str(row.get("subfamily_label"))] += int(row.get("event_count") or 0)

    reward_rows = [
        row
        for row in rows
        if str(row.get("subfamily_label")) in REWARD_LABELS
    ]
    reward_rows.sort(key=lambda row: int(row.get("event_count") or 0), reverse=True)
    return {
        "value_bucket_count": len(rows),
        "label_counts": dict(label_counts.most_common()),
        "label_event_counts": dict(label_event_counts.most_common()),
        "reward_candidate_bucket_count": len(reward_rows),
        "top_reward_candidates": reward_rows[:12],
    }


def _summarize_level_batch(report: Dict[str, object]) -> Dict[str, object]:
    summary = report.get("summary", {})
    matches = [match for match in report.get("matches", []) if isinstance(match, dict)]
    return {
        "matches_processed": report.get("matches_processed"),
        "matches_with_viable_level_candidates": summary.get("matches_with_viable_level_candidates"),
        "byte15_rejected_matches": summary.get("byte15_rejected_matches"),
        "heartbeat_records": summary.get("heartbeat_records"),
        "credit_action_03_players_with_records_by_match": [
            {
                "replay_name": match.get("replay_name"),
                "players_with_records": match.get("summary", {}).get("credit_action_03_players_with_records"),
            }
            for match in matches
        ],
    }


def _assessment(action02: Dict[str, object], level: Dict[str, object]) -> Dict[str, object]:
    reward_buckets = int(action02.get("reward_candidate_bucket_count") or 0)
    viable_level_matches = int(level.get("matches_with_viable_level_candidates") or 0)
    byte15_rejected = int(level.get("byte15_rejected_matches") or 0)
    matches_processed = int(level.get("matches_processed") or 0)
    return {
        "action02_status": "reward_pulse_context" if reward_buckets else "unresolved",
        "xp_total_export_status": "not_safe",
        "level_export_status": "not_safe",
        "blocking_fields": ["xp_total", "level"],
        "reasons": [
            (
                f"action 0x02 has {reward_buckets} reward-like value buckets, "
                "but these are event pulses/subfamilies rather than monotonic total XP counters"
            ),
            (
                f"level probe found viable level candidates in {viable_level_matches}/{matches_processed} matches"
            ),
            (
                f"[18 04 3E] byte15=level+12 is rejected in {byte15_rejected}/{matches_processed} matches"
                if matches_processed
                else "[18 04 3E] byte15=level+12 has no batch evidence"
            ),
            "No local field currently matches HackedGlory 1086-style monotonic XP/level scoreboard semantics.",
        ],
    }


def build_hackedglory_xp_level_validation(
    truth_path: str,
    *,
    limit: Optional[int] = None,
) -> Dict[str, object]:
    """Build a compact decision report for XP/level HackedGlory comparison."""
    action02_report = build_action02_subfamily_summary(truth_path)
    level_report = build_level_signal_batch(truth_path, limit=limit)
    action02_summary = _summarize_action02(action02_report)
    level_summary = _summarize_level_batch(level_report)
    return {
        "schema_version": "decoder_v2.hackedglory_xp_level_validation.v1",
        "truth_path": str(Path(truth_path).resolve()),
        "hackedglory_reference": (
            "HackedGlory reports XP/level through 1086-style monotonic scoreboard counters "
            "such as type 0x3e/0x42. Local .vgr action 0x02 is evaluated here only as a "
            "reward-pulse/context family, not as a total counter."
        ),
        "options": {"limit": limit},
        "assessment": _assessment(action02_summary, level_summary),
        "action02_reward_context": action02_summary,
        "level_signal_probe": level_summary,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize HackedGlory-inspired XP/level validation."
    )
    parser.add_argument("--truth", default="vg/output/tournament_truth.json", help="Truth JSON path")
    parser.add_argument("--limit", type=int, help="Optional level-probe batch limit")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        documents = prepare_truth_inputs(args.truth)
        validate_report_outputs(documents.inputs, [args.output] if args.output else [])
        selected = [row for row in documents.matches if "Incomplete" not in Path(row.get("replay_file", "")).parent.name]
        level_count = 0
        for row in documents.matches:
            reference = row.get("replay_file")
            if not reference or not Path(reference).exists():
                continue
            if row not in selected:
                selected.append(row)
            level_count += 1
            if args.limit is not None and level_count >= args.limit:
                break
        replays = truth_replay_files(selected, args.truth)
        prepared = prepare_truth_inputs(args.truth, replays)
        documents.inputs.recheck()
        validate_report_outputs(prepared.inputs, [args.output] if args.output else [])
        report = build_hackedglory_xp_level_validation(args.truth, limit=args.limit)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            write_report_output(prepared.inputs, output_path, payload)
            print(f"HackedGlory XP/level validation saved to {output_path}")
        else:
            prepared.inputs.recheck()
            print(payload)
    except (OSError, ValueError, TypeError) as exc:
        print(f"hackedglory_xp_level_validation: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
