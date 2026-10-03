"""Generate nullable replay statistics with one explicit outcome per input."""

import argparse
import json
from pathlib import Path
import sys

from vg.analysis.batch_statistics import StatisticsReport, generate_report, print_report
from vg.core.batch_result import BatchReport, InputResult, PartialBatchError, batch_report
from vg.core.legacy_inputs import prepare_legacy_batch
from vg.core.replay_input import discover_replay_files, replay_input_id
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output
from vg.core.unified_decoder import DecodedMatch, UnifiedDecoder


class AnalysisReport(BatchReport, StatisticsReport):
    pass


def find_replays(directory: Path) -> list[Path]:
    return list(discover_replay_files(directory))


def _decode_all(replay_dir: str, truth_path: str | None,
                inputs: ReportInputs) -> tuple[BatchReport, list[DecodedMatch]]:
    matches = []
    results: list[InputResult] = []
    replays = sorted((*inputs.replays, *inputs.reserved_replays), key=lambda p: replay_input_id(p, replay_dir))
    for replay in replays:
        result: InputResult = {'input_id': replay_input_id(replay, replay_dir), 'replay_file': str(replay),
                               'status': 'complete', 'error_code': None, 'error': None}
        try:
            decoder = UnifiedDecoder(str(replay))
            matches.append(decoder.decode_with_truth(truth_path) if truth_path else decoder.decode())
        except (OSError, ValueError) as error:
            result.update(status='failed', error_code=getattr(error, 'code', 'decode_failed'), error=str(error))
        results.append(result)
    inputs.recheck()
    return batch_report(results), matches


def decode_all_report(replay_dir: str, truth_path: str | None = None, *,
                      inputs: ReportInputs | None = None) -> AnalysisReport:
    """Return summary statistics and every input outcome, including failures."""
    if inputs is None:
        inputs = prepare_legacy_batch(replay_dir, truth_path, auto_truth=False)
    report, matches = _decode_all(replay_dir, truth_path, inputs)
    return {**generate_report(matches), **report}


def decode_all(replay_dir: str, truth_path: str | None = None) -> list[DecodedMatch]:
    inputs = prepare_legacy_batch(replay_dir, truth_path, auto_truth=False)
    report, matches = _decode_all(replay_dir, truth_path, inputs)
    if report['failed']:
        raise PartialBatchError(report)
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Batch VGR replay analysis report')
    parser.add_argument('replay_dir', nargs='?', default=r'D:\Desktop\My Folder\Game\VG\vg replay')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('--truth', help='Explicit truth data for comparison')
    args = parser.parse_args(argv)
    try:
        inputs = prepare_legacy_batch(args.replay_dir, args.truth, auto_truth=False)
        output = Path(args.output) if args.output else None
        if output is not None:
            validate_report_outputs(inputs, (output,))
        report = decode_all_report(args.replay_dir, args.truth, inputs=inputs)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            write_report_output(inputs, output, payload)
            print(f'JSON report saved to: {output}')
        print_report(report)
        print(f"Batch status: {report['status']} ({report['succeeded']}/{report['discovered']}, failed={report['failed']})")
    except (OSError, ValueError) as error:
        print(f'batch-report: {error}', file=sys.stderr)
        return 2
    return 1 if report['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
