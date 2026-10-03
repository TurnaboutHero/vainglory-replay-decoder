"""Compare self/teammate/opponent linkage for action patterns against same-hero peers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vg.core.replay_output import validate_report_outputs, write_report_output
from .report_inputs import load_research_truth, prepare_truth_inputs, require_truth_match, truth_replay_files
from typing import Dict, List, Optional

from .minion_action_self_vs_team import build_minion_action_self_vs_team_per_player
from .minion_hero_compare import build_minion_hero_compare


def build_minion_action_relation_compare(
    truth_path: str,
    target_replay_name: str,
    action_hex: str = "0x02",
    top_pattern_limit: int = 12,
) -> Dict[str, object]:
    """Compare self/teammate/opponent linkage against same-hero peers."""
    compare = build_minion_hero_compare(
        truth_path=truth_path,
        target_replay_name=target_replay_name,
        top_pattern_limit=top_pattern_limit,
    )
    matches = load_research_truth(truth_path)
    complete_matches = [match for match in matches if "Incomplete" not in Path(match["replay_file"]).parent.name]
    target_match = next(match for match in complete_matches if match["replay_name"] == target_replay_name)
    replay_by_name = {match["replay_name"]: match["replay_file"] for match in complete_matches}
    selected_patterns = compare["selected_patterns"]
    target_relations = build_minion_action_self_vs_team_per_player(
        replay_file=target_match["replay_file"],
        selected_patterns=selected_patterns,
    )
    target_series = str(Path(target_match["replay_file"]).parent.parent.resolve())

    rows = []
    for player_row in compare["rows"]:
        relation_by_pattern = {row["pattern"]: row for row in target_relations.get(player_row["player_name"], [])}
        peer_relation_rows = []
        for peer in player_row["same_hero_peers"]:
            peer_replay_file = replay_by_name[peer["replay_name"]]
            peer_report = build_minion_action_self_vs_team_per_player(
                replay_file=peer_replay_file,
                selected_patterns=selected_patterns,
            )
            peer_row_map = {row["pattern"]: row for row in peer_report.get(peer["player_name"], [])}
            peer_series = str(Path(peer["fixture_directory"]).parent.resolve())
            peer_relation_rows.append(
                {
                    "series": peer_series,
                    "replay_name": peer["replay_name"],
                    "rows": peer_row_map,
                }
            )

        pattern_rows = []
        for pattern in selected_patterns:
            target_row = relation_by_pattern.get(pattern, {})
            same_series_peers = [peer for peer in peer_relation_rows if peer["series"] == target_series]
            other_series_peers = [peer for peer in peer_relation_rows if peer["series"] != target_series]

            def _mean(peers: List[Dict[str, object]], key: str) -> Optional[float]:
                values = [peer["rows"].get(pattern, {}).get(key) for peer in peers if pattern in peer["rows"]]
                values = [value for value in values if value is not None]
                return (sum(values) / len(values)) if values else None

            pattern_rows.append(
                {
                    "pattern": pattern,
                    "target_self_presence_rate": target_row.get("self_presence_rate"),
                    "target_teammate_presence_rate": target_row.get("teammate_presence_rate"),
                    "target_opponent_presence_rate": target_row.get("opponent_presence_rate"),
                    "same_series_self_presence_mean": _mean(same_series_peers, "self_presence_rate"),
                    "same_series_teammate_presence_mean": _mean(same_series_peers, "teammate_presence_rate"),
                    "same_series_opponent_presence_mean": _mean(same_series_peers, "opponent_presence_rate"),
                    "other_series_self_presence_mean": _mean(other_series_peers, "self_presence_rate"),
                    "other_series_teammate_presence_mean": _mean(other_series_peers, "teammate_presence_rate"),
                    "other_series_opponent_presence_mean": _mean(other_series_peers, "opponent_presence_rate"),
                }
            )

        rows.append(
            {
                "player_name": player_row["player_name"],
                "hero_name": player_row["hero_name"],
                "residual_vs_0e": player_row["residual_vs_0e"],
                "pattern_rows": pattern_rows,
            }
        )

    return {
        "truth_path": str(Path(truth_path).resolve()),
        "target_replay_name": target_replay_name,
        "rows": rows,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare self/teammate/opponent linkage for action patterns against same-hero peers.")
    parser.add_argument("--truth", default="vg/output/tournament_truth.json", help="Truth JSON path")
    parser.add_argument("--replay-name", required=True, help="Target replay_name from truth JSON")
    parser.add_argument("--action", default="0x02", help="Credit action family to inspect")
    parser.add_argument("--top-pattern-limit", type=int, default=12, help="How many patterns to inspect")
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
        for row in selected:
            peers = [candidate for candidate in selected if candidate.get("replay_name") == row.get("replay_name")]
            if len(peers) > 1:
                raise ValueError(f"{args.truth}: ambiguous peer name; scoped choices: {[peer.get('replay_file') for peer in peers]}")
        replays = truth_replay_files(selected, args.truth)
        prepared = prepare_truth_inputs(args.truth, replays)
        documents.inputs.recheck()
        validate_report_outputs(prepared.inputs, [args.output] if args.output else [])
        report = build_minion_action_relation_compare(
            truth_path=args.truth,
            target_replay_name=args.replay_name,
            action_hex=args.action,
            top_pattern_limit=args.top_pattern_limit,
        )
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            write_report_output(prepared.inputs, output_path, payload)
            print(f"Minion action relation compare saved to {output_path}")
        else:
            prepared.inputs.recheck()
            print(payload)
    except (OSError, ValueError, TypeError) as exc:
        print(f"minion_action_relation_compare: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
