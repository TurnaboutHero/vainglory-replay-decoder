"""Build a focused truth-capture pack from the labeling queue and prefixed truth stubs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Optional

from .truth_labeling_queue import build_truth_labeling_queue
from .truth_stubs import build_truth_stub_report
from .truth_inventory import inventory_inputs
from vg.core.replay_output import validate_report_outputs, write_report_output


def _capture_track(queue_row: Dict[str, object]) -> str:
    completeness = str(queue_row["completeness_status"])
    game_mode = str(queue_row["game_mode"])
    team_size = int(queue_row["team_size"])

    if completeness != "complete_confirmed":
        return "resolve_completeness_first"
    if team_size == 5 and game_mode == "GameMode_5v5_Ranked":
        return "validate_5v5_ranked_minion_and_kda_policy"
    if team_size == 5:
        return "expand_complete_5v5_generalization"
    if team_size == 3:
        return "expand_3v3_generalization"
    return "general_truth_capture"


def _capture_reason(queue_row: Dict[str, object]) -> str:
    decisions = queue_row.get('accepted_decisions', {})
    withheld = queue_row.get('withheld_fields', {})
    final_fields = ('winner', 'kills', 'deaths', 'assists')
    accepted = [field for field in final_fields if isinstance(decisions.get(field), dict)
                and decisions[field].get('accepted_for_index') is True
                and decisions[field].get('scope', 'final') == 'final' and field not in withheld]
    pending = [field for field in final_fields if field not in accepted]
    reasons = [str(withheld[field].get('reason')) for field in pending
               if isinstance(withheld.get(field), dict) and withheld[field].get('reason')]
    return (f"Final fields requiring source-bound truth: {', '.join(pending) or 'none'}. "
            f"Accepted final decisions: {', '.join(accepted) or 'none'}. " + ' '.join(dict.fromkeys(reasons)))


def _capture_requirements(queue_row: Dict[str, object]) -> List[str]:
    requirements = [
        "final winner",
        "final team score",
        "per-player K/D/A",
        "per-player gold or bounty field if visible",
        "per-player minion kills or bounty field if visible",
    ]
    if str(queue_row["completeness_status"]) != "complete_confirmed":
        requirements.append("full-length replay completeness confirmation")
    return requirements


def build_truth_capture_pack(base_path: str, truth_path: str, limit: int = 20) -> Dict[str, object]:
    queue = build_truth_labeling_queue(base_path, truth_path)
    stubs = build_truth_stub_report(base_path, truth_path)
    stub_by_replay_file = {
        str(stub["replay_file"]): stub
        for stub in stubs["stubs"]
    }

    items = []
    for queue_row in queue["rows"][:limit]:
        replay_file = str(queue_row["replay_file"])
        stub = stub_by_replay_file.get(replay_file)
        if not stub:
            continue
        items.append(
            {
                "score": queue_row["score"],
                "capture_track": _capture_track(queue_row),
                "capture_reason": _capture_reason(queue_row),
                "capture_requirements": _capture_requirements(queue_row),
                "queue_entry": queue_row,
                "truth_stub": stub,
            }
        )

    return {
        "schema_version": "decoder_v2.truth_capture_pack.v1",
        "base_path": str(Path(base_path).resolve()),
        "truth_path": str(Path(truth_path).resolve()),
        "requested_limit": limit,
        "generated_items": len(items),
        "items": items,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a focused truth-capture pack from the top labeling queue items.")
    parser.add_argument(
        "--base",
        default=r"D:\Desktop\My Folder\Game\VG\vg replay",
        help="Base replay directory",
    )
    parser.add_argument(
        "--truth",
        default="vg/output/tournament_truth.json",
        help="Truth JSON path",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of top queue items to include")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        inputs = inventory_inputs(args.base, args.truth)
        if args.output:
            validate_report_outputs(inputs, (Path(args.output),))
        report = build_truth_capture_pack(args.base, args.truth, limit=args.limit)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            write_report_output(inputs, Path(args.output), payload)
            print(f"Truth capture pack saved to {args.output}")
        else:
            print(payload)
    except (OSError, ValueError, TypeError) as error:
        print(f'truth-capture-pack: {args.output or args.truth}: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
