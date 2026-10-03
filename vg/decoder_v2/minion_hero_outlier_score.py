"""Score match-6 minion outlier patterns against same-hero peers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vg.core.replay_output import validate_report_outputs, write_report_output
from .report_inputs import prepare_truth_inputs, require_truth_match, truth_replay_files
from typing import Dict, List, Optional

from .minion_hero_compare import build_minion_hero_compare


def build_minion_hero_outlier_score(
    truth_path: str,
    target_replay_name: str,
    top_pattern_limit: int = 8,
) -> Dict[str, object]:
    """Score target pattern counts against same-hero peer baselines."""
    compare = build_minion_hero_compare(
        truth_path=truth_path,
        target_replay_name=target_replay_name,
        top_pattern_limit=top_pattern_limit,
    )

    rows = []
    for row in compare["rows"]:
        pattern_scores = []
        for pattern in compare["selected_patterns"]:
            target_count = row["target_pattern_counts"].get(pattern, 0)
            peer_values = [peer["pattern_counts"].get(pattern, 0) for peer in row["same_hero_peers"]]
            if peer_values:
                peer_mean = sum(peer_values) / len(peer_values)
                peer_max = max(peer_values)
                nonzero_peer_count = sum(1 for value in peer_values if value > 0)
                excess_vs_mean = target_count - peer_mean
                excess_vs_max = target_count - peer_max
            else:
                peer_mean = None
                peer_max = None
                nonzero_peer_count = 0
                excess_vs_mean = None
                excess_vs_max = None
            pattern_scores.append(
                {
                    "pattern": pattern,
                    "target_count": target_count,
                    "peer_mean": peer_mean,
                    "peer_max": peer_max,
                    "nonzero_peer_count": nonzero_peer_count,
                    "peer_count": len(peer_values),
                    "excess_vs_mean": excess_vs_mean,
                    "excess_vs_max": excess_vs_max,
                }
            )
        pattern_scores.sort(
            key=lambda item: (
                item["excess_vs_mean"] if item["excess_vs_mean"] is not None else float("-inf"),
                item["target_count"],
            ),
            reverse=True,
        )
        rows.append(
            {
                "player_name": row["player_name"],
                "hero_name": row["hero_name"],
                "residual_vs_0e": row["residual_vs_0e"],
                "same_hero_peer_count": row["same_hero_peer_count"],
                "pattern_scores": pattern_scores,
            }
        )

    return {
        "truth_path": str(Path(truth_path).resolve()),
        "target_replay_name": target_replay_name,
        "selected_patterns": compare["selected_patterns"],
        "rows": rows,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score target minion outlier patterns against same-hero peers.")
    parser.add_argument("--truth", default="vg/output/tournament_truth.json", help="Truth JSON path")
    parser.add_argument("--replay-name", required=True, help="Target replay_name from truth JSON")
    parser.add_argument("--top-pattern-limit", type=int, default=8, help="How many outlier patterns to score")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(argv)

    try:
        documents = prepare_truth_inputs(args.truth)
        validate_report_outputs(documents.inputs, [args.output] if args.output else [])
        selected = [row for row in documents.matches if "Incomplete" not in Path(row.get("replay_file", "")).parent.name]
        candidates = [row for row in selected if row.get("replay_name") == args.replay_name]
        if len(candidates) > 1:
            raise ValueError(f"{args.truth}: ambiguous replay name {args.replay_name!r}; scoped choices: {[row.get('replay_file') for row in candidates]}")
        require_truth_match(selected, args.truth, args.replay_name)
        replays = truth_replay_files(selected, args.truth)
        prepared = prepare_truth_inputs(args.truth, replays)
        documents.inputs.recheck()
        validate_report_outputs(prepared.inputs, [args.output] if args.output else [])
        report = build_minion_hero_outlier_score(
            truth_path=args.truth,
            target_replay_name=args.replay_name,
            top_pattern_limit=args.top_pattern_limit,
        )
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            write_report_output(prepared.inputs, output_path, payload)
            print(f"Minion hero outlier score saved to {output_path}")
        else:
            prepared.inputs.recheck()
            print(payload)
    except (OSError, ValueError, TypeError) as exc:
        print(f"minion_hero_outlier_score: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
