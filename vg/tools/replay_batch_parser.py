#!/usr/bin/env python3
"""
Batch Replay Parser - Parse all VGR replays in a directory.
Usage: python replay_batch_parser.py <replay_dir> [--output results.json]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import NotRequired, TypedDict

try:
    from vg.core.vgr_parser import VGRParser
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from vg.core.vgr_parser import VGRParser


from vg.core.batch_result import BatchReport, InputResult, batch_report
from vg.core.legacy_inputs import prepare_legacy_batch
from vg.core.replay_input import replay_input_id
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output


class ReplaySummary(TypedDict):
    file: str
    success: bool
    error: NotRequired[str]
    error_code: NotRequired[str]
    game_mode: NotRequired[str]
    map_name: NotRequired[str]
    map_mode: NotRequired[str]
    players: NotRequired[list[dict]]
    player_count: NotRequired[int]
    input_id: NotRequired[str]
    status: NotRequired[str]


class ParserBatchReport(BatchReport):
    total_replays: int
    successful: int
    unique_players: int
    game_modes: dict
    hero_picks: dict
    replays: list[ReplaySummary]


def parse_replay(vgr_path: Path) -> ReplaySummary:
    """Parse a single replay and return summary."""
    try:
        parser = VGRParser(str(vgr_path), auto_truth=False)
        parsed = parser.parse()
        match_info = parsed.get("match_info", {})
        players = []
        for team_label in ("left", "right"):
            for p in parsed["teams"].get(team_label, []):
                players.append({
                    "name": p.get("name", ""),
                    "hero_name": p.get("hero_name", "Unknown"),
                    "hero_id": p.get("hero_id"),
                    "team": team_label,
                    "entity_id": p.get("entity_id"),
                })
        return {
            "file": str(vgr_path),
            "game_mode": parsed.get("game_mode", "unknown"),
            "map_name": match_info.get("map_name", "unknown"),
            "map_mode": match_info.get("map_name", "unknown"),
            "players": players,
            "player_count": len(players),
            "success": True,
        }
    except (OSError, ValueError) as e:
        return {
            "file": str(vgr_path),
            "error": str(e),
            "error_code": getattr(e, "code", "decode_failed"),
            "success": False,
        }


def batch_parse(replay_dir: Path, *, inputs: ReportInputs | None = None) -> ParserBatchReport:
    """Parse all replays in directory."""
    if inputs is None:
        inputs = prepare_legacy_batch(str(replay_dir), None, auto_truth=False)
    vgr_files = sorted((*inputs.replays, *inputs.reserved_replays), key=lambda p: replay_input_id(p, replay_dir))
    print(f"Found {len(vgr_files)} replay files")

    results = []
    outcomes: list[InputResult] = []
    hero_counter = Counter()
    mode_counter = Counter()
    player_set = set()
    total_success = 0

    for i, vgr in enumerate(vgr_files):
        result = parse_replay(vgr)
        result['input_id'] = replay_input_id(vgr, replay_dir)
        result['status'] = 'complete' if result['success'] else 'failed'
        outcomes.append({'input_id': result['input_id'], 'replay_file': str(vgr),
                         'status': result['status'], 'error_code': result.get('error_code'),
                         'error': result.get('error')})
        results.append(result)
        if result["success"]:
            total_success += 1
            mode_counter[result["game_mode"]] += 1
            for p in result["players"]:
                hero_counter[p["hero_name"]] += 1
                player_set.add(p["name"])
        if (i + 1) % 10 == 0:
            print(f"  Parsed {i+1}/{len(vgr_files)}...")

    inputs.recheck()
    summary: ParserBatchReport = {
        **batch_report(outcomes),
        "total_replays": len(vgr_files),
        "successful": total_success,
        "failed": len(vgr_files) - total_success,
        "unique_players": len(player_set),
        "game_modes": dict(mode_counter.most_common()),
        "hero_picks": dict(hero_counter.most_common()),
        "replays": results,
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch parse VGR replay files")
    parser.add_argument("replay_dir", help="Directory containing replay files")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path")
    args = parser.parse_args(argv)
    output = Path(args.output) if args.output else Path(__file__).parent.parent / "output" / "batch_parse_results.json"
    try:
        inputs = prepare_legacy_batch(args.replay_dir, None, auto_truth=False)
        validate_report_outputs(inputs, (output,))
        summary = batch_parse(Path(args.replay_dir), inputs=inputs)
        payload = json.dumps(summary, indent=2, ensure_ascii=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        write_report_output(inputs, output, payload)
        print(f"Saved to: {output}")
        print(f"Batch status: {summary['status']} ({summary['successful']}/{summary['total_replays']})")
    except (OSError, ValueError) as error:
        print(f'replay-batch-parser: {error}', file=sys.stderr)
        return 2
    return 1 if summary['failed'] else 0


if __name__ == "__main__":
    raise SystemExit(main())
