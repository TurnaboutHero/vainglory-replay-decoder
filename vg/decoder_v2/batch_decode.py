"""Batch decode replays conservatively with decoder_v2."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys
from typing import Dict, List, Optional

from vg.core.batch_result import InputResult, batch_report
from vg.core.replay_input import ReplayInputError, discover_replay_files, replay_input_id
from vg.core.replay_output import ReplayOutputError, ReportInputs, validate_report_outputs, write_report_output
from .decode_match import decode_match
from .player_state import decode_player_state


def find_replays(base_path: str) -> List[Path]:
    """Find all `.0.vgr` replay files under a directory tree."""
    return list(discover_replay_files(base_path))


@dataclass(frozen=True, slots=True)
class BatchInputs:
    replays: tuple[Path, ...]
    report_inputs: ReportInputs
    errors: dict[Path, ReplayOutputError]


def prepare_batch_inputs(base_path: str, *, files: tuple[Path, ...] = ()) -> BatchInputs:
    replays = tuple(find_replays(base_path))
    readable = []
    errors = {}
    for replay in replays:
        try:
            ReportInputs(replays=(replay,))
        except ReplayOutputError as error:
            if error.code != 'input_unreadable':
                raise
            errors[replay] = error
        else:
            readable.append(replay)
    return BatchInputs(replays, ReportInputs(files=files, replays=readable, reserved_replays=tuple(errors)), errors)


def decode_replay_batch(base_path: str, *, inputs: BatchInputs | None = None) -> Dict[str, object]:
    """Decode a replay tree using conservative v2 policy."""
    if inputs is None:
        inputs = prepare_batch_inputs(base_path)
    replays = inputs.replays
    matches = []
    results: list[InputResult] = []
    completeness_counter: Dict[str, int] = {}
    accepted_field_counter: Dict[str, int] = {}
    withheld_field_counter: Dict[str, int] = {}

    for replay in replays:
        input_id = replay_input_id(replay, base_path)
        try:
            if replay in inputs.errors:
                raise inputs.errors[replay]
            decoded = decode_match(str(replay))
            payload = decoded.to_dict() | {'input_id': input_id}
        except (OSError, ValueError) as error:
            results.append({'input_id': input_id, 'replay_file': str(replay),
                            'status': 'failed', 'error_code': getattr(error, 'code', 'decode_failed'),
                            'error': str(error)})
            continue
        matches.append(payload)
        results.append({'input_id': input_id, 'replay_file': str(replay),
                        'status': 'complete', 'error_code': None, 'error': None})

        completeness_status = payload["completeness_status"]
        completeness_counter[completeness_status] = completeness_counter.get(completeness_status, 0) + 1

        withheld = set(payload["withheld_fields"])
        for key, decision in payload["accepted_fields"].items():
            if (decision.get("accepted_for_index") is True
                    and decision.get("scope", "final") != "capture"
                    and payload.get("scope", "final") != "capture"
                    and key not in withheld):
                accepted_field_counter[key] = accepted_field_counter.get(key, 0) + 1
            else:
                withheld.add(key)
        for key in withheld:
            withheld_field_counter[key] = withheld_field_counter.get(key, 0) + 1

    return {
        **batch_report(results),
        "schema_version": "decoder_v2.batch.v2",
        "base_path": str(Path(base_path).resolve()),
        "total_replays": len(replays),
        "completeness_summary": completeness_counter,
        "accepted_field_summary": accepted_field_counter,
        "withheld_field_summary": withheld_field_counter,
        "matches": matches,
    }


def decode_state_batch(base_path: str, *, inputs: BatchInputs | None = None,
                       at_game_time: float | None = None) -> Dict[str, object]:
    """Decode every input through the single-replay player-state path at one common query."""
    if inputs is None:
        inputs = prepare_batch_inputs(base_path)
    states = []
    results: list[InputResult] = []
    support: Dict[str, int] = {}
    fields: Dict[str, Dict[str, int]] = {}
    for replay in inputs.replays:
        input_id = replay_input_id(replay, base_path)
        try:
            if replay in inputs.errors:
                raise inputs.errors[replay]
            state = decode_player_state(replay, at_game_time=at_game_time).to_dict()
        except (OSError, ValueError) as error:
            results.append({'input_id': input_id, 'replay_file': str(replay), 'status': 'failed',
                            'error_code': getattr(error, 'code', 'decode_failed'), 'error': str(error)})
            continue
        states.append({'input_id': input_id, **state})
        results.append({'input_id': input_id, 'replay_file': str(replay), 'status': 'complete', 'error_code': None, 'error': None})
        support[state['support_status']] = support.get(state['support_status'], 0) + 1
        for player in state['players']:
            for field, status in player['field_status'].items():
                counts = fields.setdefault(field, {})
                counts[status['status']] = counts.get(status['status'], 0) + 1
    return {
        **batch_report(results),
        'schema_version': 'decoder_v2.batch_state.v1',
        'base_path': str(Path(base_path).resolve()),
        'scope': 'recorded_end' if at_game_time is None else 'capture',
        'requested_game_time': at_game_time,
        'support_summary': support,
        'player_field_summary': fields,
        'states': states,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch decode replays conservatively with decoder_v2.")
    parser.add_argument("base_path", help="Replay root directory")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    parser.add_argument("--format", choices=("safe-json", "state-json"), default="safe-json",
                        help="safe-json keeps decoder_v2.batch.v2; state-json emits decoder_v2.player_state.v3 per input")
    parser.add_argument("--at-game-time", type=float, help="Query every input at this game-clock second (state-json only)")
    args = parser.parse_args(argv)
    if args.at_game_time is not None and (not math.isfinite(args.at_game_time) or args.at_game_time < 0):
        parser.error("--at-game-time must be finite and non-negative")
    if args.at_game_time is not None and args.format != "state-json":
        parser.error("--at-game-time requires --format state-json")

    try:
        output_path = Path(args.output) if args.output else None
        inputs = prepare_batch_inputs(args.base_path)
        if output_path is not None:
            validate_report_outputs(inputs.report_inputs, (output_path,))
        report = (decode_state_batch(args.base_path, inputs=inputs, at_game_time=args.at_game_time)
                  if args.format == "state-json" else decode_replay_batch(args.base_path, inputs=inputs))
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if output_path is not None:
            write_report_output(inputs.report_inputs, output_path, payload)
            print(f"decoder_v2 batch output saved to {output_path}")
        else:
            inputs.report_inputs.recheck()
            print(payload)
    except (OSError, ReplayInputError, ReplayOutputError) as error:
        print(f"batch-decode: {error}", file=sys.stderr)
        return 2
    return 1 if report.get('failed', 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
