"""Explicit truth and input preparation shared by research commands."""

from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from vg.core.replay_output import ReportInputs
from vg.core.stored_paths import stored_path_key
from vg.core.truth_input import TruthInputError, TruthMatch, load_truth_matches, select_truth_match


@dataclass(frozen=True, slots=True)
class PreparedTruth:
    matches: tuple[TruthMatch, ...]
    inputs: ReportInputs


def truth_reference_key(reference: str, document: str | Path) -> str:
    if PureWindowsPath(reference).drive or '\\' in reference:
        return stored_path_key(reference)
    path = Path(reference)
    return str((path if path.is_absolute() else Path(document).parent / path).resolve())


def load_research_truth(truth_path: str | Path) -> list[TruthMatch]:
    """Resolve local relative references without opening referenced replay files."""
    rows = []
    for match in load_truth_matches(truth_path):
        row = dict(match)
        row.setdefault('players', {})
        row.setdefault('match_info', {})
        reference = row.get('replay_file')
        if isinstance(reference, str) and not (PureWindowsPath(reference).drive or '\\' in reference):
            row['replay_file'] = truth_reference_key(reference, truth_path)
        rows.append(row)
    return rows


def prepare_truth_inputs(truth_path: str | Path, replay_files: Collection[Path] = (),
                         extra_files: Collection[Path] = ()) -> PreparedTruth:
    """Snapshot caller-selected inputs before loading their truth document."""
    inputs = ReportInputs(files=(Path(truth_path), *extra_files), replays=replay_files)
    matches = tuple(load_research_truth(truth_path))
    inputs.recheck()
    return PreparedTruth(matches, inputs)


def require_truth_match(matches: Collection[TruthMatch], truth_path: str | Path, replay_name: str) -> TruthMatch:
    return select_truth_match(tuple(matches), truth_path, replay_name=replay_name)


def truth_replay_files(matches: Collection[TruthMatch], truth_path: str | Path) -> tuple[Path, ...]:
    """Require references only for rows the caller has explicitly chosen to decode."""
    from vg.core.truth_input import resolve_truth_reference
    files = []
    for row in matches:
        reference = row.get('replay_file')
        if not isinstance(reference, str) or not reference:
            raise TruthInputError('truth_invalid', Path(truth_path), 'Selected match requires replay_file')
        files.append(resolve_truth_reference(reference, truth_path))
    return tuple(files)
