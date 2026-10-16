"""Single-file streaming publication with optimistic destination conflict checks."""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import tempfile
from typing import Callable, TextIO

from vg.core.replay_output import (
    FileIdentity, ReportInputs, ReplayOutputError, file_identity, validate_report_outputs,
)


@dataclass(frozen=True)
class OutputSnapshot:
    parent: Path
    parent_device: int
    parent_inode: int
    identity: FileIdentity | None
    modified_ns: int | None
    changed_ns: int | None


def capture_output(output: Path) -> OutputSnapshot:
    """Freeze absence or regular-file identity before producing any rows."""
    parent = output.parent.resolve(strict=True)
    parent_stat = parent.stat()
    info = None
    try:
        info = output.lstat()
    except FileNotFoundError:
        pass
    if info is not None and not stat.S_ISREG(info.st_mode):
        raise ReplayOutputError(output, 'Output must be a regular file, not a link or directory', 'publication_failed')
    return OutputSnapshot(parent, parent_stat.st_dev, parent_stat.st_ino,
                          file_identity(output) if info is not None else None,
                          info.st_mtime_ns if info is not None else None,
                          info.st_ctime_ns if info is not None else None)


def publish_timeline(output: Path, expected: OutputSnapshot,
                     write: Callable[[TextIO], None], inputs: ReportInputs) -> None:
    """Stage completely, fsync, recheck sources/destination, then publish.

    Like the report-set publisher, existing-target replacement uses an
    optimistic check followed by rename, not a portable compare-and-swap.
    An initially absent destination uses exclusive hard-link creation instead.
    """
    def check_destination():
        try:
            current = capture_output(output)
        except (OSError, ReplayOutputError) as error:
            raise ReplayOutputError(output, 'Destination or parent changed during publication', 'publication_conflict') from error
        if current != expected:
            raise ReplayOutputError(output, 'Destination or parent changed during publication', 'publication_conflict')

    temporary = None
    temporary_identity = None
    staged_stat = None
    published = False
    try:
        check_destination()
        validate_report_outputs(inputs, (output,))
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                dir=expected.parent, prefix=f'.{output.name}.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            info = os.fstat(stream.fileno())
            temporary_identity = (info.st_dev, info.st_ino)
            write(stream)
            stream.flush()
            os.fsync(stream.fileno())
            staged_stat = os.fstat(stream.fileno())
        # Input hashing may be lengthy. Check destination and stage ownership
        # only after it finishes, immediately before the publication syscall.
        validate_report_outputs(inputs, (output,))
        check_destination()
        try:
            current_stage = temporary.lstat()
        except OSError as error:
            raise ReplayOutputError(output, 'Staging file changed during publication',
                                    'publication_conflict') from error
        if (not stat.S_ISREG(current_stage.st_mode)
                or (current_stage.st_dev, current_stage.st_ino) != temporary_identity
                or (current_stage.st_size, current_stage.st_mtime_ns, current_stage.st_ctime_ns)
                != (staged_stat.st_size, staged_stat.st_mtime_ns, staged_stat.st_ctime_ns)):
            raise ReplayOutputError(output, 'Staging file changed during publication',
                                    'publication_conflict')
        if expected.identity is None:
            try:
                os.link(temporary, output)
            except FileExistsError as error:
                raise ReplayOutputError(output, 'Destination appeared during publication', 'publication_conflict') from error
        else:
            os.replace(temporary, output)
        published = True
    finally:
        if temporary is not None:
            # A moved/replaced parent invalidates this pathname. Never remove a
            # foreign file through it; our stage may remain in the moved folder.
            try:
                parent_info = expected.parent.stat()
                info = temporary.lstat()
            except FileNotFoundError:
                pass
            else:
                if ((parent_info.st_dev, parent_info.st_ino) ==
                        (expected.parent_device, expected.parent_inode)
                        and (info.st_dev, info.st_ino) == temporary_identity
                        and (published or staged_stat is None
                             or (info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                             == (staged_stat.st_size, staged_stat.st_mtime_ns, staged_stat.st_ctime_ns))):
                    temporary.unlink()
