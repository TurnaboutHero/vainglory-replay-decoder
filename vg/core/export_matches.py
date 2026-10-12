"""Export decoded replay families as recoverable JSON and CSV report sets."""

import argparse
import json
from pathlib import Path
import sys
from typing import TypedDict

from vg.core.batch_result import BatchReport, InputResult, PartialBatchError, batch_report
from vg.core.export_rows import (
    CsvRow, _complete_sum, match_to_csv_rows, match_to_summary_row, serialize_csv,
)
from vg.core.replay_input import discover_replay_files, replay_input_id, select_replay
from vg.core.replay_output import (
    ReplayOutputError, ReportInputs, publish_report_set, validate_report_outputs,
    write_report_output,
)
from vg.core.unified_decoder import DecodedMatch, UnifiedDecoder
from vg.core.analysis_eligibility import partition_definitive_analysis


class ExportReport(BatchReport):
    total_matches: int
    matches: list[dict]
    publication_status: str
    receipt: str
    definitive_analysis: dict


def export_match_json(match: DecodedMatch, output_path: Path) -> None:
    inputs = ReportInputs(replays=(Path(match.replay_path),),
                          files=(Path(match.truth_source),) if match.truth_source else ())
    write_report_output(inputs, output_path, match.to_json(indent=2))


def export_csv(rows: list[CsvRow], output_path: Path) -> None:
    write_report_output(ReportInputs(), output_path, serialize_csv(rows, ('match_idx', 'input_id') if not rows else ()))


def find_replays(directory: Path) -> list[Path]:
    return list(discover_replay_files(directory))


def decode_single(replay_path: str, truth_path: str | None = None) -> DecodedMatch:
    decoder = UnifiedDecoder(str(select_replay(replay_path)))
    return decoder.decode_with_truth(truth_path) if truth_path else decoder.decode()


def _batch_inputs(replays: list[Path], truth_path: str | None) -> tuple[ReportInputs, dict[Path, ReplayOutputError]]:
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
    files = (Path(truth_path),) if truth_path else ()
    return ReportInputs(files=files, replays=readable, reserved_replays=tuple(errors)), errors


def _decode_batch(directory: str, truth_path: str | None, output_dir: str | None,
                  csv_only: bool) -> tuple[ExportReport, list[DecodedMatch]]:
    replays = find_replays(Path(directory))
    inputs, errors = _batch_inputs(replays, truth_path)
    out = Path(output_dir) if output_dir else Path(directory)
    receipt = out / 'export_receipt.json'
    json_paths = [] if csv_only else [out / 'all_matches.json', *(out / f'match_{i}.json' for i in range(1, len(replays) + 1))]
    validate_report_outputs(inputs, (*json_paths, out / 'all_matches.csv', out / 'match_summary.csv', receipt))
    results: list[InputResult] = []
    matches = []
    payloads = []
    rows = []
    summaries = []
    outputs = {}
    for ordinal, replay in enumerate(replays, 1):
        input_id = replay_input_id(replay, directory)
        result = {'input_id': input_id, 'replay_file': str(replay), 'match_idx': ordinal,
                  'status': 'complete', 'error_code': None, 'error': None}
        try:
            if replay in errors:
                raise errors[replay]
            select_replay(replay)
            match = decode_single(str(replay), truth_path)
        except (OSError, ValueError) as error:
            result.update(status='failed', error_code=getattr(error, 'code', 'decode_failed'), error=str(error))
            results.append(result)
            continue
        results.append(result)
        matches.append(match)
        payload = match.to_dict() | {'input_id': input_id, 'match_idx': ordinal}
        payloads.append(payload)
        if not csv_only:
            outputs[out / f'match_{ordinal}.json'] = json.dumps(payload, indent=2, ensure_ascii=False)
        rows.extend(match_to_csv_rows(match, ordinal, input_id))
        summaries.append(match_to_summary_row(match, ordinal, input_id))
    report: ExportReport = {**batch_report(results), 'total_matches': len(matches), 'matches': payloads,
                            'definitive_analysis': partition_definitive_analysis(payloads),
                            'publication_status': 'complete', 'receipt': str(receipt.absolute())}
    if not csv_only:
        outputs[out / 'all_matches.json'] = json.dumps(report, indent=2, ensure_ascii=False)
    empty_match = DecodedMatch('', '', '', '', 0)
    outputs[out / 'all_matches.csv'] = serialize_csv(rows, ('match_idx', 'input_id', 'replay_name', 'player_name', 'kills', 'duration_s', 'duration_status'))
    outputs[out / 'match_summary.csv'] = serialize_csv(summaries, match_to_summary_row(empty_match))
    out.mkdir(parents=True, exist_ok=True)
    publish_report_set(inputs, outputs, receipt, batch=batch_report(results))
    return report, matches


def decode_batch_report(directory: str, truth_path: str | None = None,
                        output_dir: str | None = None, csv_only: bool = False) -> ExportReport:
    """Return every input outcome only after publishing the current generation."""
    return _decode_batch(directory, truth_path, output_dir, csv_only)[0]


def decode_batch(directory: str, truth_path: str | None = None,
                 output_dir: str | None = None, csv_only: bool = False) -> list[DecodedMatch]:
    """Preserve list compatibility without hiding failed inputs."""
    report, matches = _decode_batch(directory, truth_path, output_dir, csv_only)
    if report['failed']:
        raise PartialBatchError(report)
    return matches


def resolve_single_output_paths(replay_path: Path, output: str | None = None,
                                csv_only: bool = False) -> tuple[Path | None, Path]:
    out = Path(output) if output else replay_path.parent
    if out.is_dir():
        out = out / f'{replay_path.stem}_decoded'
        return (None if csv_only else out.with_suffix('.json'), out.with_suffix('.csv'))
    if csv_only:
        return None, out if out.suffix else out.with_suffix('.csv')
    if out.suffix and out.suffix.lower() not in ('.json', '.csv'):
        raise ReplayOutputError(out, 'Use .json, .csv, a suffixless name, or an existing directory', 'output_ambiguous')
    return out.with_suffix('.json'), out.with_suffix('.csv')


def export_single(replay_path: Path, match: DecodedMatch, output: str | None = None,
                  csv_only: bool = False, *, truth_path: str | None = None,
                  inputs: ReportInputs | None = None) -> tuple[Path | None, Path]:
    replay_path = select_replay(replay_path)
    if inputs is None:
        files = tuple(Path(source) for source in (truth_path, match.truth_source) if source)
        inputs = ReportInputs(replays=(replay_path,), files=files)
    json_path, csv_path = resolve_single_output_paths(replay_path, output, csv_only)
    receipt = csv_path.with_name(csv_path.name + '.receipt.json')
    outputs = {csv_path: serialize_csv(match_to_csv_rows(match, input_id=replay_path.name), ('match_idx', 'input_id', 'player_name'))}
    if json_path is not None:
        outputs[json_path] = json.dumps(match.to_dict() | {'input_id': replay_path.name, 'match_idx': 0}, indent=2, ensure_ascii=False)
    result: InputResult = {'input_id': replay_path.name, 'replay_file': str(replay_path),
                           'status': 'complete', 'error_code': None, 'error': None}
    publish_report_set(inputs, outputs, receipt, batch=batch_report([result]))
    return json_path, csv_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Export decoded VGR replays to JSON/CSV')
    parser.add_argument('path', help='Replay .0.vgr file or batch directory')
    parser.add_argument('--batch', action='store_true')
    parser.add_argument('--truth')
    parser.add_argument('-o', '--output')
    parser.add_argument('--csv-only', action='store_true')
    args = parser.parse_args(argv)
    path = Path(args.path)
    try:
        if args.batch or path.is_dir():
            report = decode_batch_report(str(path), args.truth, args.output, args.csv_only)
            print(json.dumps({key: value for key, value in report.items() if key != 'matches'}))
            return 1 if report['failed'] else 0
        replay = select_replay(path)
        inputs = ReportInputs(replays=(replay,), files=(Path(args.truth),) if args.truth else ())
        json_path, csv_path = resolve_single_output_paths(replay, args.output, args.csv_only)
        destinations = (csv_path, csv_path.with_name(csv_path.name + '.receipt.json'))
        validate_report_outputs(inputs, destinations + ((json_path,) if json_path else ()))
        match = decode_single(str(replay), args.truth)
        export_single(replay, match, args.output, args.csv_only, truth_path=args.truth, inputs=inputs)
        print(f'Exported: {csv_path}')
    except (OSError, ValueError, TypeError) as error:
        print(f'export-matches: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
