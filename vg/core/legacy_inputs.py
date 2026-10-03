from pathlib import Path

from vg.core.replay_input import discover_replay_files, select_replay
from vg.core.replay_output import ReplayOutputError, ReportInputs


def truth_candidates(truth_path: str | None, auto_truth: bool) -> tuple[Path, ...]:
    if truth_path:
        return (Path(truth_path),)
    if not auto_truth:
        return ()
    return tuple(sorted({path for pattern in ('MATCH_DATA_*.md', 'MATCH_DATA_*.txt',
                                              'match_truth*.json', 'truth*.json')
                         for path in Path.cwd().glob(pattern) if path.is_file()}))


def prepare_legacy_inputs(path: str, truth_path: str | None = None, *,
                          auto_truth: bool = False) -> tuple[Path, ReportInputs]:
    replay = select_replay(path)
    return replay, ReportInputs(files=truth_candidates(truth_path, auto_truth), replays=(replay,))


def prepare_legacy_batch(path: str, truth_path: str | None, *,
                         auto_truth: bool) -> ReportInputs:
    readable, reserved = [], []
    for replay in discover_replay_files(path):
        try:
            ReportInputs(replays=(replay,))
        except ReplayOutputError as error:
            if error.code != 'input_unreadable':
                raise
            reserved.append(replay)
        else:
            readable.append(replay)
    return ReportInputs(files=truth_candidates(truth_path, auto_truth),
                        replays=readable, reserved_replays=reserved)
