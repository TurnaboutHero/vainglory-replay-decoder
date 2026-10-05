"""Verified filesystem snapshots and recoverable, cooperating replay-slot writes.

The slot must be quiescent; sequential replacements are not atomic to a game.
"""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import struct
from typing import Iterator, TypedDict
import uuid

from vg.core.replay_input import ReplayInputError, discover_replay_files, replay_sections
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output


class ArchiveError(ReplayInputError):
    """Archive failure with an optional durable recovery location."""

    def __init__(self, code: str, path: Path, reason: str, recovery: Path | None = None):
        self.recovery = recovery
        super().__init__(code, path, reason)


@dataclass(frozen=True, slots=True)
class Entry:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class Inventory:
    frame0: Path
    entries: tuple[Entry, ...]
    scope: str


class Snapshot(TypedDict):
    path: str
    scope: str
    source_scope: str
    sections: list[dict[str, str | int]]


class ReportState(TypedDict):
    path: str
    existed: bool
    prior: str
    published: str


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def select_family(path: Path, name: str | None = None, *, recursive: bool = True) -> Path:
    """Select raw archive bytes without making semantic validity claims."""
    if path.is_file():
        replay_sections(path, require_contiguous=True)
        return path.absolute()
    candidates = discover_replay_files(path)
    candidates = tuple(p for p in candidates if not any(part.startswith(('.snapshot-', '.vgr-recovery-')) for part in p.relative_to(path).parts) and (recursive or p.parent == path)
                       and (name is None or p.name == f'{name}.0.vgr'))
    if len(candidates) != 1:
        code = 'replay_ambiguous' if candidates else 'input_missing'
        raise ArchiveError(code, path, 'Select exactly one replay family with an explicit name/path')
    return candidates[0].absolute()


def inventory(frame0: Path, *, manifest: bool = False) -> Inventory:
    sections = replay_sections(frame0, require_contiguous=True)
    scope = hashlib.sha256(b'vgr-numbered-series-v1\x00')
    entries = []
    for number, path in sections:
        data = path.read_bytes()
        scope.update(struct.pack('>QQ', number, len(data)))
        scope.update(data)
        entries.append(Entry(path.name, len(data), hashlib.sha256(data).hexdigest()))
    if manifest:
        selected = _associated_manifest(frame0)
        if selected is not None:
            entries.append(Entry(selected.name, selected.stat().st_size, digest(selected)))
    return Inventory(frame0, tuple(entries), 'sha256:' + scope.hexdigest())


def _associated_manifest(frame0: Path) -> Path | None:
    family = frame0.name[:-6]
    identifiers = {family}
    if len(family) == 73 and family[36] == '-':
        parts = (family[:36], family[37:])
        try:
            canonical = tuple(str(uuid.UUID(part)) for part in parts)
        except ValueError:
            canonical = ()
        if canonical == tuple(part.lower() for part in parts):
            identifiers.update(parts)
    candidates = [frame0.parent / f'replayManifest-{name}.txt' for name in identifiers]
    associated = [path for path in candidates if path.is_file()]
    if len(associated) > 1:
        raise ArchiveError('manifest_ambiguous', frame0, 'Multiple exact family/UUID manifests match')
    return associated[0] if associated else None


def _check_unchanged(before: Inventory, code: str, *, manifest: bool = False) -> None:
    try:
        after = inventory(before.frame0, manifest=manifest)
    except (OSError, ReplayInputError) as error:
        raise ArchiveError(code, before.frame0, str(error)) from error
    if before != after:
        raise ArchiveError(code, before.frame0, 'Section inventory or full contents changed')


def _copy(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
    mode = destination.stat().st_mode
    destination.chmod(mode | stat.S_IWUSR)
    try:
        with destination.open('r+b') as stream:
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        destination.chmod(mode)


def _verify(directory: Path, entries: tuple[Entry, ...]) -> None:
    for entry in entries:
        path = directory / entry.name
        if path.is_symlink() or path.stat().st_size != entry.size or digest(path) != entry.sha256:
            raise ArchiveError('verification_failed', path, 'Copied bytes do not match inventory')


def _json(path: Path, payload: str) -> None:
    write_report_output(ReportInputs(), path, payload)


def lock_path(frame0: Path) -> Path:
    return frame0.parent / f'.{frame0.name[:-6]}.archive.lock'


@contextmanager
def exclusive_lock(path: Path, operation: Path, *, recover_dead: bool = False) -> Iterator[None]:
    from vg.core.archive_recovery import exclusive_lock as acquire
    with acquire(path, operation, recover_dead=recover_dead):
        yield


def _safe_paths(source: Inventory, target: Inventory) -> None:
    paths = [source.frame0.parent / entry.name for entry in source.entries]
    targets = [target.frame0.parent / entry.name for entry in target.entries]
    if source.frame0.parent.resolve() == target.frame0.parent.resolve():
        raise ArchiveError('archive_overlap', target.frame0, 'Source and target directories overlap')
    for path in (*paths, *targets):
        if path.is_symlink() or path.stat().st_nlink > 1:
            raise ArchiveError('archive_overlap', path, 'Linked replay sections or parents are unsafe')
    for path in paths:
        if any(path.samefile(other) for other in targets):
            raise ArchiveError('archive_overlap', path, 'Source and target refer to the same file')


class Replacement:
    """Mutable transaction owns staging, rollback and commit state until exit."""

    def __init__(self, source: Path, target: Path):
        self.source = inventory(source)
        self.target = inventory(target)
        _safe_paths(self.source, self.target)
        self.name = target.name[:-6]
        self.operation = target.parent / f'.vgr-recovery-{uuid.uuid4().hex}'
        self.stage = self.operation / 'stage'
        self.originals = self.operation / 'originals'
        self.journal = self.operation / 'journal.json'
        self.committed = False
        self.promoting = False
        self.report: ReportState | None = None
        self.expected = tuple(Entry(f'{self.name}.{index}.vgr', e.size, e.sha256)
                              for index, e in enumerate(self.source.entries))

    def record(self, state: str) -> None:
        _json(self.journal, json.dumps({'state': state, 'operation': str(self.operation),
              'target': str(self.target.frame0), 'pid': os.getpid(), 'host': socket.gethostname(),
              'source': str(self.source.frame0), 'report': self.report,
              'originals': [asdict(e) for e in self.target.entries],
              'expected': [asdict(e) for e in self.expected]}, indent=2))

    def prepare(self) -> None:
        self.stage.mkdir(parents=True)
        self.originals.mkdir()
        for entry, expected in zip(self.source.entries, self.expected):
            _copy(self.source.frame0.parent / entry.name, self.stage / expected.name)
        for entry in self.target.entries:
            _copy(self.target.frame0.parent / entry.name, self.originals / entry.name)
        _check_unchanged(self.source, 'source_changed')
        _check_unchanged(self.target, 'target_changed')
        _verify(self.stage, self.expected)
        _verify(self.originals, self.target.entries)
        self.record('prepared')

    def begin(self) -> None:
        _check_unchanged(self.source, 'source_changed')
        _check_unchanged(self.target, 'target_changed')
        self.record('promoting')
        self.promoting = True

    def promote(self) -> None:
        self.begin()
        for entry in self.expected:
            os.replace(self.stage / entry.name, self.target.frame0.parent / entry.name)
        wanted = {e.name for e in self.expected}
        for entry in self.target.entries:
            if entry.name not in wanted:
                (self.target.frame0.parent / entry.name).unlink()
        self.verify()

    def verify(self) -> None:
        _check_unchanged(self.source, 'source_changed')
        actual = inventory(self.target.frame0)
        if actual.entries != self.expected:
            raise ArchiveError('verification_failed', self.target.frame0, 'Target inventory differs', self.operation)

    def rollback(self) -> None:
        from vg.core.archive_recovery import _restore, _restore_report
        try:
            _restore(self.target.frame0, self.originals, self.target.entries, self.expected)
            if self.report:
                _restore_report(self.operation, self.report)
            self.record('rolled_back')
        except (OSError, ValueError) as error:
            (self.operation / 'recovery-required').touch()
            raise ArchiveError('recovery_required', self.target.frame0, str(error), self.operation) from error

    def commit(self) -> None:
        self.verify()
        self.record('committed')
        self.committed = True

    def prepare_report(self, output: Path, payload: str | None = None) -> None:
        if not self.report:
            exists = output.exists()
            if exists:
                _copy(output, self.operation / 'prior-report')
            self.report = {'path': str(output.absolute()), 'existed': exists,
                           'prior': digest(output) if exists else '', 'published': ''}
        if payload is not None:
            self.report['published'] = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        self.record('promoting' if self.promoting else 'prepared')


@contextmanager
def replacement(source: Path, target: Path) -> Iterator[Replacement]:
    transaction = Replacement(source, target)
    with exclusive_lock(lock_path(target), transaction.operation):
        transaction.prepare()
        try:
            yield transaction
        finally:
            if transaction.promoting and not transaction.committed:
                transaction.rollback()


def recover(operation: Path) -> Path:
    from vg.core.archive_recovery import recover as recover_operation
    return recover_operation(operation)


def _snapshot_receipt(destination: Path, before: Inventory) -> Snapshot:
    sections = [asdict(e) for e in before.entries]
    scope = hashlib.sha256(json.dumps(sections, sort_keys=True).encode()).hexdigest()
    return {'path': str(destination), 'scope': scope, 'source_scope': before.scope, 'sections': sections}


def verify_snapshot(destination: Path, before: Inventory) -> None:
    """An existing snapshot counts only when its bytes and its whole receipt match the source inventory."""
    if destination.is_symlink() or {p.name for p in destination.iterdir()} != {e.name for e in before.entries} | {'snapshot.json'}:
        raise ArchiveError('recovery_required', destination, 'Existing snapshot inventory differs')
    try:
        _verify(destination, before.entries)
    except ArchiveError as error:
        raise ArchiveError('recovery_required', error.path, error.reason) from error
    receipt = destination / 'snapshot.json'
    try:
        recorded = json.loads(receipt.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError) as error:
        raise ArchiveError('recovery_required', receipt, f'Snapshot receipt is unreadable: {error}') from error
    # The stored path is how the snapshot was first named; another spelling or a moved directory is the same data.
    expected = {k: v for k, v in _snapshot_receipt(destination, before).items() if k != 'path'}
    if (not isinstance(recorded, dict) or not isinstance(recorded.get('path'), str)
            or {k: v for k, v in recorded.items() if k != 'path'} != expected):
        raise ArchiveError('recovery_required', receipt, 'Snapshot receipt differs from its verified sections')


def snapshot(frame0: Path, destination: Path, *, expected: Inventory | None = None) -> Snapshot:
    """Publish a verified immutable directory; failed attempts never acknowledge it."""
    before = expected or inventory(frame0, manifest=True)
    _check_unchanged(before, 'source_changed', manifest=True)
    if destination.is_symlink() or destination.resolve() == frame0.parent.resolve() or destination.resolve() in frame0.resolve().parents:
        raise ArchiveError('archive_overlap', destination, 'Backup overlaps replay source')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / f'.snapshot-{uuid.uuid4().hex}'
    with exclusive_lock(destination.parent / '.snapshot.lock', stage, recover_dead=True):
        stage.mkdir()
        try:
            for entry in before.entries:
                _copy(frame0.parent / entry.name, stage / entry.name)
            _verify(stage, before.entries)
            _check_unchanged(before, 'source_changed', manifest=True)
            result = _snapshot_receipt(destination, before)
            _json(stage / 'snapshot.json', json.dumps(result, indent=2))
            if destination.exists():
                verify_snapshot(destination, before)
            else:
                os.replace(stage, destination)
            return result
        finally:
            shutil.rmtree(stage, ignore_errors=True)
