"""Generate truth stubs for replay directories not yet covered by truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional

from .decode_match import decode_match
from .manifest import parse_replay_manifest, UUID_PAIR_PATTERN
from .truth_inventory import build_truth_inventory, inventory_inputs
from vg.core.replay_output import validate_report_outputs, write_report_output


def find_replay_files(directory: str) -> List[Path]:
    """Find `.0.vgr` replay files directly under a replay directory."""
    path = Path(directory)
    return sorted(
        [item for item in path.iterdir() if item.is_file() and item.name.endswith(".0.vgr")],
        key=lambda item: item.name,
    )


def build_truth_stub_for_replay(replay_file: str, manifest_path: Optional[str] = None) -> Dict[str, object]:
    """Build a prefilled truth stub for a replay."""
    safe = decode_match(replay_file).to_dict()
    manifest = parse_replay_manifest(manifest_path).to_dict() if manifest_path else None

    players = {}
    for player in safe["players"]:
        players[player["name"]] = {
            "team": player["team"],
            "hero_name": player["hero_name"],
            "kills": None,
            "deaths": None,
            "assists": None,
            "gold": None,
            "minion_kills": None,
            "notes": "Populate from trusted source (result image, manual review, or validated capture).",
        }

    return {
        "replay_name": safe["replay_name"],
        "replay_file": safe["replay_file"],
        "manifest": manifest,
        "prefill_source": "decoder_v2.safe-json",
        "match_info": {
            "game_mode": safe["game_mode"],
            "map_name": safe["map_name"],
            "team_size": safe["team_size"],
            "winner": None,
            "duration_seconds": None,
            "score_left": None,
            "score_right": None,
            "completeness_status": safe["completeness_status"],
            "completeness_reason": safe["completeness_reason"],
        },
        "players": players,
        "accepted_fields": safe["accepted_fields"],
        "withheld_fields": safe["withheld_fields"],
    }


def build_truth_stub_report(base_path: str, truth_path: str) -> Dict[str, object]:
    """Build truth stubs for replay directories not yet covered by truth."""
    inventory = build_truth_inventory(base_path, truth_path)
    stubs = []

    for row in inventory["missing"]:
        replay_file = Path(row["replay_file"])
        manifest_path, manifest_reason = associated_manifest(replay_file)
        stub = build_truth_stub_for_replay(str(replay_file), str(manifest_path) if manifest_path else None)
        stub['manifest_reason'] = manifest_reason
        stubs.append(stub)

    return {
        "schema_version": "decoder_v2.truth_stub_report.v1",
        "base_path": str(Path(base_path).resolve()),
        "truth_path": str(Path(truth_path).resolve()),
        "stub_count": len(stubs),
        "stubs": stubs,
    }


def associated_manifest(replay_file: Path) -> tuple[Path | None, str]:
    family = replay_file.name[:-len('.0.vgr')]
    identifiers = {family}
    pair = UUID_PAIR_PATTERN.fullmatch(family)
    if pair:
        identifiers.update((pair.group('match_uuid'), pair.group('session_uuid')))
    candidates = sorted(replay_file.parent.glob('replayManifest-*.txt'))
    exact = [path for path in candidates if path.name[len('replayManifest-'):-len('.txt')] in identifiers]
    if len(exact) == 1:
        return exact[0], 'exact_family_association'
    if len(exact) > 1 or len(candidates) > 1:
        return None, 'manifest_ambiguous'
    return None, 'manifest_unassociated' if candidates else 'manifest_missing'


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate truth stubs for unlabeled replay directories.")
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
    parser.add_argument(
        "-o", "--output",
        help="Optional output path",
    )
    args = parser.parse_args(argv)

    try:
        inputs = inventory_inputs(args.base, args.truth)
        if args.output:
            validate_report_outputs(inputs, (Path(args.output),))
        report = build_truth_stub_report(args.base, args.truth)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            write_report_output(inputs, Path(args.output), payload)
            print(f"Truth stubs saved to {args.output}")
        else:
            print(payload)
    except (OSError, ValueError, TypeError) as error:
        print(f'truth-stubs: {args.output or args.truth}: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
