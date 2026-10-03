"""Validate supplied truth documents without claiming their values are observed."""

from collections.abc import Mapping
import json
import math
import os
from pathlib import Path, PureWindowsPath
from typing import Final, assert_never

type JSONValue = None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]
type TruthMatch = dict[str, JSONValue]
NUMERIC_FIELDS: Final = frozenset({
    'kills', 'deaths', 'assists', 'gold', 'minion_kills', 'cs', 'level',
    'duration_seconds', 'score_left', 'score_right', 'xp', 'experience',
})


class TruthInputError(ValueError):
    def __init__(self, code: str, path: Path, reason: str):
        self.code = code
        self.path = path
        self.reason = reason
        super().__init__(str(self))

    def __str__(self) -> str:
        return f'{self.code}: {self.path}: {self.reason}'


def _mapping(value: JSONValue, path: Path, field: str) -> TruthMatch:
    if not isinstance(value, dict):
        raise TruthInputError('truth_invalid', path, f'{field} must be an object')
    return value


def _validate_numbers(row: Mapping[str, JSONValue], path: Path) -> None:
    for field in NUMERIC_FIELDS.intersection(row):
        value = row[field]
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or value < 0):
            raise TruthInputError('truth_invalid', path, f'{field} must be a finite nonnegative number or null')


def normalize_truth(data: JSONValue, path: Path | str, *, require_replay_file: bool = False) -> tuple[TruthMatch, ...]:
    """Preserve extras and scoped duplicates across single, keyed and list envelopes."""
    path = Path(path)
    document = _mapping(data, path, 'truth')
    rows: list[TruthMatch] = []
    if 'matches' not in document:
        rows.append(dict(document))
    else:
        matches = document['matches']
        match matches:
            case dict():
                for name, value in matches.items():
                    row = dict(_mapping(value, path, f'matches[{name}]'))
                    row.setdefault('replay_name', name)
                    rows.append(row)
            case list():
                rows.extend(dict(_mapping(value, path, 'match')) for value in matches)
            case None | bool() | int() | float() | str():
                raise TruthInputError('truth_invalid', path, 'matches must be an object or list')
            case unreachable:
                assert_never(unreachable)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if require_replay_file and 'replay_file' not in row:
            raise TruthInputError('truth_invalid', path, 'replay_file is required for this operation')
        for field in ('replay_name', 'replay_file'):
            if field in row and (not isinstance(row[field], str) or not row[field].strip()):
                raise TruthInputError('truth_invalid', path, f'{field} must be a nonempty string')
        _validate_numbers(row, path)
        if 'match_info' in row:
            _validate_numbers(_mapping(row['match_info'], path, 'match_info'), path)
        if 'players' in row:
            players = _mapping(row['players'], path, 'players')
            for name, player in players.items():
                _validate_numbers(_mapping(player, path, f'players[{name}]'), path)
        name, replay = row.get('replay_name'), row.get('replay_file')
        if isinstance(replay, str):
            identity = ('path', _reference_key(replay, path))
        else:
            identity = ('name', name if isinstance(name, str) else '')
        if identity in seen:
            raise TruthInputError('truth_ambiguous', path, 'Duplicate scoped match identity')
        seen.add(identity)
    return tuple(rows)


def load_truth_matches(path: Path | str, *, require_replay_file: bool = False) -> tuple[TruthMatch, ...]:
    """Read strict UTF-8 JSON; references need not exist for metadata inventories."""
    path = Path(path)
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeError as error:
        raise TruthInputError('truth_invalid', path, 'Truth must be UTF-8') from error
    except OSError as error:
        raise TruthInputError('truth_unreadable', path, str(error)) from error
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as error:
        raise TruthInputError('truth_invalid', path, str(error)) from error
    return normalize_truth(data, path, require_replay_file=require_replay_file)


def _reference_key(reference: str, document: Path) -> str:
    windows = PureWindowsPath(reference)
    if (windows.drive or '\\' in reference) and (os.name != 'nt' or windows.is_absolute()):
        return windows.as_posix().casefold()
    path = Path(reference)
    resolved = (path if path.is_absolute() else document.parent / path).resolve()
    return resolved.as_posix().casefold() if os.name == 'nt' else str(resolved)


def resolve_truth_reference(reference: str, document: Path | str) -> Path:
    """Resolve local disk references, refusing to reinterpret foreign drive paths."""
    document = Path(document)
    windows = PureWindowsPath(reference)
    if (windows.drive or '\\' in reference) and os.name != 'nt':
        raise TruthInputError('truth_unreadable', document, f'Foreign filesystem reference: {reference}')
    path = Path(reference)
    return path if path.is_absolute() else document.parent / path


def select_truth_match(matches: tuple[TruthMatch, ...], path: Path | str, *,
                       replay_name: str | None = None, replay_file: Path | str | None = None) -> TruthMatch:
    """Prefer scoped references; name-only selection is valid only when unique."""
    path = Path(path)
    candidates = list(matches)
    if replay_file is not None:
        key = _reference_key(str(replay_file), path)
        candidates = [row for row in candidates if isinstance(row.get('replay_file'), str)
                      and _reference_key(row['replay_file'], path) == key]
        if not candidates and replay_name is not None:
            candidates = [row for row in matches if 'replay_file' not in row and row.get('replay_name') == replay_name]
    elif replay_name is not None:
        candidates = [row for row in candidates if row.get('replay_name') == replay_name]
    if not candidates:
        raise TruthInputError('truth_no_match', path, 'No truth row matches the requested replay')
    if len(candidates) != 1:
        raise TruthInputError('truth_ambiguous', path, 'Select a unique scoped replay reference')
    return candidates[0]
