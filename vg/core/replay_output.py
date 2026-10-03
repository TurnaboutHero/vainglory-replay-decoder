"""Protect numbered replay inputs when publishing a decoder result."""
from collections.abc import Collection, Mapping
from vg.core.batch_result import BatchReport
from dataclasses import dataclass, field
from fnmatch import fnmatch
import hashlib
import os
from pathlib import Path
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vg.core.report_recovery import ReportReceipt


class ReplayOutputError(ValueError):
    def __init__(self, path: Path, reason: str, code: str = 'output_alias'):
        self.path = path
        self.reason = reason
        self.code = code
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"{self.path}: {self.reason}"


@dataclass(frozen=True, slots=True)
class FileIdentity:
    path: Path
    resolved: Path
    device: int
    inode: int
    digest: str


def file_identity(path: Path) -> FileIdentity:
    with path.open('rb') as stream:
        stat = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return FileIdentity(path, path.resolve(), stat.st_dev, stat.st_ino, digest)


def _input_sources(files: Collection[Path], replays: Collection[Path]) -> tuple[Path, ...]:
    sources = list(files)
    for replay in replays:
        pattern = f"{replay.stem.rsplit('.', 1)[0]}.*.vgr"
        sources.append(replay)
        if replay.parent.exists():
            sources.extend(path for path in sorted(replay.parent.iterdir()) if fnmatch(path.name, pattern))
    return tuple(dict.fromkeys(sources))


@dataclass(frozen=True, slots=True)
class ReportInputs:
    """Snapshot consumed bytes; reserved unreadable inputs receive alias protection only."""

    files: Collection[Path] = ()
    replays: Collection[Path] = ()
    reserved_files: Collection[Path] = ()
    reserved_replays: Collection[Path] = ()
    identities: tuple[FileIdentity | None, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'files', tuple(Path(path) for path in self.files))
        object.__setattr__(self, 'replays', tuple(Path(path) for path in self.replays))
        object.__setattr__(self, 'reserved_files', tuple(Path(path) for path in self.reserved_files))
        object.__setattr__(self, 'reserved_replays', tuple(Path(path) for path in self.reserved_replays))
        try:
            object.__setattr__(self, 'identities', self._snapshot())
        except OSError as error:
            raise ReplayOutputError(Path(error.filename or '.'), str(error), 'input_unreadable') from error

    def sources(self) -> tuple[Path, ...]:
        return _input_sources((*self.files, *self.reserved_files), (*self.replays, *self.reserved_replays))

    def _snapshot(self) -> tuple[FileIdentity | None, ...]:
        return tuple(file_identity(path) if path.exists() else None
                     for path in _input_sources(self.files, self.replays))

    def recheck(self) -> None:
        try:
            current = self._snapshot()
        except OSError as error:
            raise ReplayOutputError(Path(error.filename or '.'), str(error), 'input_changed') from error
        if current != self.identities:
            raise ReplayOutputError(Path('.'), 'Consumed input identity changed after preflight', 'input_changed')


def validate_output_sources(sources: Collection[Path], output: Path) -> None:
    """Reject direct, symbolic, and hard-link aliases of consumed input files."""
    resolved = output.resolve()
    for source in sources:
        if resolved == source.resolve() or (output.exists() and source.exists() and output.samefile(source)):
            raise ReplayOutputError(output, "output path aliases an input file")


def validate_replay_output(replay: Path, output: Path) -> None:
    """Reject replay aliases and names consumed by lexical sibling discovery."""
    pattern = f"{replay.stem.rsplit('.', 1)[0]}.*.vgr"
    resolved = output.resolve()
    for candidate in (output, resolved):
        if candidate.parent.resolve() == replay.parent.resolve() and fnmatch(candidate.name, pattern):
            raise ReplayOutputError(output, "output names a sibling input .vgr section")
    validate_output_sources((replay, *replay.parent.glob(pattern)), output)


def validate_replay_outputs(replays: Collection[Path], output: Path) -> None:
    """Protect every discovered replay family in a batch, including future sections."""
    for replay in replays:
        validate_replay_output(replay, output)


def write_replay_output(replay: Path, output: Path, payload: str) -> None:
    """Publish a single-match report through the shared batch-safe writer."""
    write_replay_outputs((replay,), output, payload)


def write_replay_outputs(replays: Collection[Path], output: Path, payload: str) -> None:
    """Publish atomically so failed writes preserve existing results and inputs."""
    write_report_output(ReportInputs(replays=replays), output, payload)


def validate_report_outputs(inputs: ReportInputs, outputs: Collection[Path]) -> None:
    """Protect every explicit input and reject aliases among report destinations."""
    inputs.recheck()
    previous: list[Path] = []
    for output in outputs:
        output = Path(output)
        if output.is_symlink():
            raise ReplayOutputError(output, 'Output must not be a symbolic link')
        validate_output_sources(inputs.sources(), output)
        validate_replay_outputs((*inputs.replays, *inputs.reserved_replays), output)
        validate_output_sources(previous, output)
        previous.append(output)


def stage_payload(output: Path, payload: str | bytes, encoding: str = 'utf-8') -> Path:
    data = payload.encode(encoding) if isinstance(payload, str) else payload
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='wb', dir=output.parent,
            prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return temporary
    except (OSError, UnicodeError):
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def write_report_output(inputs: ReportInputs, output: Path, payload: str | bytes, *, encoding: str = 'utf-8') -> None:
    """Stage durably and recheck identities immediately before replacing one file."""
    output = Path(output)
    temporary: Path | None = None
    try:
        validate_report_outputs(inputs, (output,))
        temporary = stage_payload(output, payload, encoding)
        validate_report_outputs(inputs, (output,))
        os.replace(temporary, output)
    except (OSError, UnicodeError) as error:
        raise ReplayOutputError(output, str(error), 'publication_failed') from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def publish_report_set(inputs: ReportInputs, outputs: Mapping[Path, str | bytes], receipt: Path, *, batch: BatchReport | None = None) -> 'ReportReceipt':
    """Publish a recoverable generation, with the complete receipt written last."""
    from vg.core.report_transaction import publish_report_set as publish
    return publish(inputs, outputs, Path(receipt), batch=batch)


def recover_report_set(receipt: Path) -> 'ReportReceipt':
    """Restore a pending generation using only its verified owned backups."""
    from vg.core.report_transaction import recover_report_set as recover
    return recover(Path(receipt))
