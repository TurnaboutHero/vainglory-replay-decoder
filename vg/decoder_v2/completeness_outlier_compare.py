"""Compare one completeness outlier against accepted long-tail cohorts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .completeness_audit import build_completeness_audit
from .batch_decode import find_replays
from vg.core.replay_input import ReplayInputError
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output


def _derived_metrics(row: Dict[str, object]) -> Dict[str, Optional[float]]:
    crystal_ts = row.get("crystal_ts")
    max_death_ts = row.get("max_player_death_ts")
    max_header_ts = row.get("max_death_header_ts")
    max_item_ts = row.get("max_item_ts")
    return {
        "crystal_to_player_death": (max_death_ts - crystal_ts) if crystal_ts is not None and max_death_ts is not None else None,
        "crystal_to_header": (max_header_ts - crystal_ts) if crystal_ts is not None and max_header_ts is not None else None,
        "header_to_item": (max_item_ts - max_header_ts) if max_item_ts is not None and max_header_ts is not None else None,
        "player_death_to_header": (max_header_ts - max_death_ts) if max_death_ts is not None and max_header_ts is not None else None,
        "player_death_to_item": (max_item_ts - max_death_ts) if max_death_ts is not None and max_item_ts is not None else None,
    }


def _summarize_reference(rows: List[Dict[str, object]]) -> Dict[str, Dict[str, Optional[float]]]:
    metrics: Dict[str, List[float]] = {}
    for row in rows:
        for key, value in _derived_metrics(row).items():
            if value is None:
                continue
            metrics.setdefault(key, []).append(float(value))
    summary = {}
    for key, values in metrics.items():
        summary[key] = {
            "count": len(values),
            "min": min(values),
            "mean": sum(values) / len(values),
            "max": max(values),
        }
    return summary


def build_completeness_outlier_compare(base_path: str, target_replay_name: str) -> Dict[str, object]:
    """Compare one target replay against accepted long-tail complete cohorts."""
    audit = build_completeness_audit(base_path)
    rows = audit["rows"]
    candidates = [row for row in rows if row["replay_name"] == target_replay_name]
    if len(candidates) != 1:
        raise ReplayInputError('replay_ambiguous' if candidates else 'input_missing', Path(base_path),
                               f'Expected one target {target_replay_name!r}; choices: {[row["replay_file"] for row in candidates]}')
    target = candidates[0]

    accepted_stale_tail = [
        row for row in rows
        if row["status"] == "complete_confirmed"
        and "crystal_player_death_gap_gt_60s" in row["review_flags"]
        and "generic_player_death_gap_gt_60s" in row["review_flags"]
    ]
    accepted_without_crystal = [
        row for row in rows
        if row["status"] == "complete_confirmed"
        and "complete_without_crystal" in row["review_flags"]
    ]

    return {
        "base_path": str(Path(base_path).resolve()),
        "target_replay_name": target_replay_name,
        "target": {
            "replay_name": target["replay_name"],
            "replay_file": target["replay_file"],
            "status": target["status"],
            "reason": target["reason"],
            "review_flags": target["review_flags"],
            "review_bucket": target.get("review_bucket"),
            "frame_count": target["frame_count"],
            "metrics": _derived_metrics(target),
        },
        "accepted_stale_tail_reference_count": len(accepted_stale_tail),
        "accepted_stale_tail_metric_summary": _summarize_reference(accepted_stale_tail),
        "accepted_without_crystal_reference_count": len(accepted_without_crystal),
        "accepted_without_crystal_metric_summary": _summarize_reference(accepted_without_crystal),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare one completeness outlier against accepted long-tail cohorts.")
    parser.add_argument(
        "--base",
        default=r"D:\Desktop\My Folder\Game\VG\vg replay",
        help="Base replay directory",
    )
    parser.add_argument("--replay-name", required=True, help="Target replay_name")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(argv)

    try:
        replays = find_replays(args.base)
        inputs = ReportInputs(replays=replays)
        validate_report_outputs(inputs, [args.output] if args.output else [])
        candidates = [replay for replay in replays if replay.name == f'{args.replay_name}.0.vgr']
        if len(candidates) != 1:
            raise ReplayInputError('replay_ambiguous' if candidates else 'input_missing', Path(args.base),
                                   f'Expected one target {args.replay_name!r}; choices: {candidates}')
        report = build_completeness_outlier_compare(args.base, args.replay_name)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            write_report_output(inputs, Path(args.output), payload)
            print(f"Completeness outlier compare saved to {args.output}")
        else:
            inputs.recheck()
            print(payload)
    except (OSError, ValueError, TypeError) as error:
        print(f'completeness-outlier: {args.base}: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
