"""Audit truth quality by comparing OCR, current truth, and decoder_v2 output."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional

from .decode_match import decode_match
from .report_inputs import load_research_truth, truth_replay_files
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output
from vg.core.truth_input import TruthInputError


def _matched_rows(truth_path: str, ocr_path: str) -> List[tuple[Dict, Dict]]:
    truth, ocr = load_research_truth(truth_path), load_research_truth(ocr_path)
    pairs = []
    for row in truth:
        scoped = [other for other in ocr if row.get('replay_file')
                  and row.get('replay_file') == other.get('replay_file')]
        named = [other for other in ocr if row.get('replay_name')
                 and row.get('replay_name') == other.get('replay_name')
                 and (not row.get('replay_file') or not other.get('replay_file'))]
        candidates = scoped or named
        if len(candidates) > 1 or (named and sum(other.get('replay_name') == row.get('replay_name') for other in truth) > 1):
            raise TruthInputError('truth_ambiguous', Path(truth_path), 'Audit requires unique scoped truth/OCR matches')
        if candidates:
            if not isinstance(row.get('replay_name'), str):
                raise TruthInputError('truth_invalid', Path(truth_path), 'Matched row requires replay_name')
            truth_replay_files((row,), truth_path)
            pairs.append((row, candidates[0]))
    return sorted(pairs, key=lambda pair: (pair[0]['replay_name'], pair[0].get('replay_file', '')))


def _resolve_name(name: str, players: Dict[str, Dict]) -> Optional[str]:
    if name in players:
        return name
    lower_map = {key.lower(): key for key in players}
    if name.lower() in lower_map:
        return lower_map[name.lower()]
    prefix = name.split("_", 1)[0]
    candidates = [key for key in players if key.split("_", 1)[0] == prefix]
    if not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.80)
    return matches[0] if matches else None


def audit_truth(
    truth_path: str,
    ocr_truth_path: str,
) -> Dict[str, object]:
    matched_rows = _matched_rows(truth_path, ocr_truth_path)

    report_rows = []
    summary = {
        "score_mismatch_matches": 0,
        "duration_mismatch_matches": 0,
        "player_rows": 0,
        "mk_mismatches": 0,
        "kill_mismatches": 0,
        "death_mismatches": 0,
        "assist_mismatches": 0,
    }
    for truth_match, ocr_match in matched_rows:
        replay_name = truth_match['replay_name']
        safe = decode_match(truth_match["replay_file"]).to_dict()

        if (
            truth_match.get("match_info", {}).get("score_left") != ocr_match.get("match_info", {}).get("score_left")
            or truth_match.get("match_info", {}).get("score_right") != ocr_match.get("match_info", {}).get("score_right")
        ):
            summary["score_mismatch_matches"] += 1
        if (
            truth_match.get("match_info", {}).get("duration_seconds")
            != ocr_match.get("match_info", {}).get("duration_seconds")
        ):
            summary["duration_mismatch_matches"] += 1

        player_rows = []
        for player in safe["players"]:
            truth_name = _resolve_name(player["name"], truth_match.get("players", {}))
            ocr_name = _resolve_name(player["name"], ocr_match.get("players", {}))
            truth_player = truth_match.get("players", {}).get(truth_name) if truth_name else None
            ocr_player = ocr_match.get("players", {}).get(ocr_name) if ocr_name else None
            summary["player_rows"] += 1
            if (truth_player.get("minion_kills") if truth_player else None) != (ocr_player.get("minion_kills") if ocr_player else None):
                summary["mk_mismatches"] += 1
            if (truth_player.get("kills") if truth_player else None) != (ocr_player.get("kills") if ocr_player else None):
                summary["kill_mismatches"] += 1
            if (truth_player.get("deaths") if truth_player else None) != (ocr_player.get("deaths") if ocr_player else None):
                summary["death_mismatches"] += 1
            if (truth_player.get("assists") if truth_player else None) != (ocr_player.get("assists") if ocr_player else None):
                summary["assist_mismatches"] += 1

            player_rows.append(
                {
                    "decoder_name": player["name"],
                    "truth_name": truth_name,
                    "ocr_name": ocr_name,
                    "decoder_hero": player["hero_name"],
                    "truth_hero": truth_player.get("hero_name") if truth_player else None,
                    "ocr_hero": ocr_player.get("hero_name") if ocr_player else None,
                    "truth_minion_kills": truth_player.get("minion_kills") if truth_player else None,
                    "ocr_minion_kills": ocr_player.get("minion_kills") if ocr_player else None,
                    "truth_kills": truth_player.get("kills") if truth_player else None,
                    "ocr_kills": ocr_player.get("kills") if ocr_player else None,
                    "truth_deaths": truth_player.get("deaths") if truth_player else None,
                    "ocr_deaths": ocr_player.get("deaths") if ocr_player else None,
                    "truth_assists": truth_player.get("assists") if truth_player else None,
                    "ocr_assists": ocr_player.get("assists") if ocr_player else None,
                }
            )

        report_rows.append(
            {
                "replay_name": replay_name,
                "result_image": truth_match.get("result_image"),
                "truth_match_info": truth_match.get("match_info", {}),
                "ocr_match_info": ocr_match.get("match_info", {}),
                "safe_output_summary": {
                    "completeness_status": safe["completeness_status"],
                    "accepted_fields": list(safe["accepted_fields"].keys()),
                    "withheld_fields": list(safe["withheld_fields"].keys()),
                },
                "players": player_rows,
            }
        )

    return {
        "truth_path": str(Path(truth_path).resolve()),
        "ocr_truth_path": str(Path(ocr_truth_path).resolve()),
        "audited_matches": len(report_rows),
        "summary": summary,
        "matches": report_rows,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit truth quality against OCR output and decoder_v2 safe output.")
    parser.add_argument("--truth", default="vg/output/tournament_truth.json", help="Truth JSON path")
    parser.add_argument("--ocr", required=True, help="OCR-derived truth JSON path")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args(argv)

    try:
        documents = ReportInputs(files=(Path(args.truth), Path(args.ocr)))
        if args.output:
            validate_report_outputs(documents, (Path(args.output),))
        pairs = _matched_rows(args.truth, args.ocr)
        replays = truth_replay_files(tuple(row for row, _ in pairs), args.truth)
        inputs = ReportInputs(files=documents.files, replays=replays)
        documents.recheck()
        if args.output:
            validate_report_outputs(inputs, (Path(args.output),))
        report = audit_truth(args.truth, args.ocr)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            write_report_output(inputs, Path(args.output), payload)
            print(f"Truth audit saved to {args.output}")
        else:
            print(payload)
    except (OSError, ValueError, TypeError) as error:
        print(f'truth-audit: {args.output or args.truth}: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
