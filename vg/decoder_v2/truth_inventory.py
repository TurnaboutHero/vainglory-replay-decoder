"""Truth coverage per replay family, with retained directory summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional

from vg.core.replay_input import discover_replay_files
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output
from vg.core.stored_paths import stored_parent
from .report_inputs import load_research_truth, truth_reference_key


def load_truth_directories(truth_path: str) -> Dict[str, Dict[str, object]]:
    result = {}
    for match in load_research_truth(truth_path):
        reference = match.get('replay_file')
        if isinstance(reference, str):
            parent = stored_parent(reference)
            result[parent] = {'replay_name': match.get('replay_name'),
                              'is_incomplete_fixture': 'Incomplete' in parent}
    return result


def inventory_metadata(replay: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in replay.parent.iterdir() if path.is_file()
                        and not path.name.startswith('._') and (
                            path.name.startswith('replayManifest-') or
                            (path.name.lower().startswith('result') and path.suffix.lower() in {'.png', '.jpg', '.jpeg'}))))


def scan_replay_directories(base_path: str) -> List[Dict[str, object]]:
    rows = []
    replays = discover_replay_files(base_path)
    for replay in replays:
        metadata = inventory_metadata(replay)
        rows.append({
            'directory': str(replay.parent.resolve()), 'replay_file': str(replay.resolve()),
            'replay_name': replay.name[:-len('.0.vgr')],
            'replay_file_count': sum(other.parent == replay.parent for other in replays),
            'has_result_image': any(path.suffix.lower() in {'.png', '.jpg', '.jpeg'} for path in metadata),
            'has_manifest': any(path.name.startswith('replayManifest-') for path in metadata),
        })
    return rows


def inventory_inputs(base_path: str, truth_path: str) -> ReportInputs:
    replays = discover_replay_files(base_path)
    metadata = tuple(dict.fromkeys(path for replay in replays for path in inventory_metadata(replay)))
    inputs = ReportInputs(files=(Path(truth_path), *metadata), replays=replays)
    load_research_truth(truth_path)
    inputs.recheck()
    return inputs


def build_truth_inventory(base_path: str, truth_path: str) -> Dict[str, object]:
    rows = scan_replay_directories(base_path)
    matches = load_research_truth(truth_path)
    references = {truth_reference_key(match['replay_file'], truth_path): match for match in matches
                  if isinstance(match.get('replay_file'), str)}
    covered, missing = [], []
    for row in rows:
        truth_entry = references.get(truth_reference_key(row['replay_file'], truth_path))
        merged = {**row, 'covered_by_truth': truth_entry is not None}
        if truth_entry is not None:
            merged['is_incomplete_fixture'] = 'Incomplete' in row['directory']
            covered.append(merged)
        else:
            missing.append(merged)
    directories = {row['directory'] for row in rows}
    missing_dirs = {row['directory'] for row in missing}
    covered_dirs = directories - missing_dirs
    return {
        'schema_version': 'decoder_v2.truth_inventory.v2',
        'base_path': str(Path(base_path).resolve()), 'truth_path': str(Path(truth_path).resolve()),
        'total_families': len(rows), 'covered_families': len(covered), 'missing_families': len(missing),
        'total_replay_directories': len(directories), 'covered_directories': len(covered_dirs),
        'missing_directories': len(missing_dirs),
        'coverage_pct': len(covered) / len(rows) * 100 if rows else 0.0,
        'directories_with_result_images': len({row['directory'] for row in rows if row['has_result_image']}),
        'directories_with_manifest': len({row['directory'] for row in rows if row['has_manifest']}),
        'covered': covered, 'missing': missing,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Inventory local truth coverage across replay families.')
    parser.add_argument('--base', default=r'D:\Desktop\My Folder\Game\VG\vg replay', help='Base replay directory')
    parser.add_argument('--truth', default='vg/output/tournament_truth.json', help='Truth JSON path')
    parser.add_argument('-o', '--output', help='Optional output JSON path')
    args = parser.parse_args(argv)
    try:
        inputs = inventory_inputs(args.base, args.truth)
        if args.output:
            validate_report_outputs(inputs, (Path(args.output),))
        report = build_truth_inventory(args.base, args.truth)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            write_report_output(inputs, Path(args.output), payload)
            print(f'Truth inventory saved to {args.output}')
        else:
            print(payload)
    except (OSError, ValueError, TypeError) as error:
        print(f'truth-inventory: {args.output or args.truth}: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
