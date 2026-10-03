"""Deterministic replay selection, independent of native evidence acceptance."""

import os
from pathlib import Path
import re

from vg.core.vgr_records import VGRRecordError, iter_records


class ReplayInputError(ValueError):
    def __init__(self, code: str, path: Path, reason: str):
        self.code = code
        self.path = path
        self.reason = reason
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"{self.code}: {self.path}: {self.reason}"


def _visible(path: Path) -> bool:
    return not any(part == '__MACOSX' or part.startswith('._') for part in path.parts)


def discover_replay_files(root: Path | str) -> tuple[Path, ...]:
    """Enumerate frame-zero paths without parsing their bytes or hiding IO errors."""
    root = Path(root)
    if not root.exists():
        raise ReplayInputError('input_missing', root, 'Replay root does not exist')
    if not root.is_dir():
        raise ReplayInputError('input_not_directory', root, 'Replay root must be a directory')
    result = []

    def onerror(error: OSError) -> None:
        raise ReplayInputError('input_unreadable', Path(error.filename or root), str(error)) from error

    try:
        for directory, folders, files in os.walk(root, onerror=onerror):
            folders[:] = sorted(name for name in folders if _visible(Path(name)))
            for name in files:
                path = Path(directory) / name
                if name.endswith('.0.vgr') and _visible(path):
                    result.append(path)
    except OSError as error:
        onerror(error)
    return tuple(sorted(result, key=lambda path: path.relative_to(root).as_posix()))


def _check_frame0(path: Path) -> None:
    if not path.exists():
        raise ReplayInputError('input_missing', path, 'Replay file does not exist')
    if not path.is_file() or not path.name.endswith('.0.vgr') or not _visible(path):
        raise ReplayInputError('replay_malformed', path, 'Select an explicit .0.vgr file')


def _read_section(path: Path) -> bytes:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ReplayInputError('input_unreadable', path, str(error)) from error
    if not data:
        raise ReplayInputError('replay_empty', path, 'Replay section is empty')
    return data


def _recognizable(data: bytes) -> bool:
    # Metadata fixtures are intentionally not fully framed native recordings.
    for marker in (b'\xda\x03\xee', b'\xe0\x03\xee'):
        offset = data.find(marker)
        while offset >= 0:
            name = data[offset + 3:offset + 33].split(b'\x00', 1)[0]
            if (offset + 0xD6 <= len(data) and len(name) >= 3
                    and all(32 <= byte <= 126 for byte in name)):
                return True
            offset = data.find(marker, offset + 1)
    try:
        return bool(tuple(iter_records(data)))
    except VGRRecordError:
        return False


def select_replay(path: Path | str) -> Path:
    """Select one real family; never infer a frame-zero filename from a sibling."""
    path = Path(path)
    if path.is_dir():
        candidates = discover_replay_files(path)
        if not candidates:
            raise ReplayInputError('replay_empty', path, 'Directory contains no replay families')
        if len(candidates) != 1:
            raise ReplayInputError('replay_ambiguous', path, 'Select one explicit .0.vgr file')
        path = candidates[0]
    _check_frame0(path)
    if not _recognizable(_read_section(path)):
        raise ReplayInputError('replay_malformed', path, 'No recognizable player metadata or framed records')
    return path


def replay_sections(frame0: Path | str, *, require_contiguous: bool = False) -> tuple[tuple[int, Path], ...]:
    """Read-check numeric siblings; retain gaps for analysis unless explicitly forbidden."""
    frame0 = Path(frame0)
    _check_frame0(frame0)
    family = frame0.name[:-len('.0.vgr')]
    pattern = re.compile(re.escape(family) + r'\.([0-9]+)\.vgr\Z')
    sections: dict[int, Path] = {}
    try:
        for path in frame0.parent.iterdir():
            matched = pattern.fullmatch(path.name)
            if matched is None or not _visible(path):
                continue
            number = int(matched.group(1))
            if number in sections:
                raise ReplayInputError('replay_ambiguous', path, 'Duplicate numeric section suffix')
            _read_section(path)
            sections[number] = path
    except OSError as error:
        raise ReplayInputError('input_unreadable', frame0.parent, str(error)) from error
    ordered = tuple(sorted(sections.items()))
    if require_contiguous and tuple(sections_number for sections_number, _ in ordered) != tuple(range(len(ordered))):
        raise ReplayInputError('replay_gap', frame0, 'Loading requires contiguous sections starting at zero')
    return ordered


def replay_input_id(frame0: Path | str, root: Path | str) -> str:
    """Return scoped path identity without substituting it for replay content identity."""
    path, base = Path(frame0).absolute(), Path(root).absolute()
    try:
        return path.relative_to(base).as_posix()
    except ValueError as error:
        raise ReplayInputError('input_outside_root', path, f'Replay is outside {base}') from error
