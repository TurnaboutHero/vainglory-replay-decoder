from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import socket
from typing import Iterator

from vg.core.replay_archive import ArchiveError, Entry, ReportState, _copy, _json, _verify, digest, inventory, lock_path
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output


def _restore(target: Path, originals: Path, entries: tuple[Entry, ...], expected: tuple[Entry, ...]) -> None:
    _verify(originals, entries)
    names = {entry.name for entry in entries}
    for entry in entries:
        staged = originals.parent / f'restore-{entry.name}'
        _copy(originals / entry.name, staged)
        os.replace(staged, target.parent / entry.name)
    for entry in expected:
        if entry.name not in names:
            (target.parent / entry.name).unlink(missing_ok=True)
    if inventory(target).entries != entries:
        raise ArchiveError('recovery_required', target, 'Restored inventory does not match originals')


def _restore_report(operation: Path, report: ReportState) -> None:
    output = Path(report['path'])
    if report['existed']:
        backup = operation / 'prior-report'
        if digest(backup) != report['prior']:
            raise ArchiveError('recovery_required', backup, 'Report backup hash mismatch')
        if output.is_symlink() or not output.exists() or digest(output) != report['prior']:
            staged = operation / 'restore-report'
            _copy(backup, staged)
            os.replace(staged, output)
    else:
        output.unlink(missing_ok=True)


def _owner_dead(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() == 87
        try:
            code = wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value != 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def recover(operation: Path) -> Path:
    """Explicit rollback only with a dead local owner and validated journal paths."""
    try:
        data = json.loads((operation / 'journal.json').read_text(encoding='utf-8'))
        target = Path(data['target'])
        if (operation.is_symlink() or (operation / 'originals').is_symlink()
                or (operation / 'journal.json').is_symlink() or lock_path(target).is_symlink()
                or not target.is_absolute() or not target.name.endswith('.0.vgr')
                or not operation.name.startswith('.vgr-recovery-')
                or operation.resolve() != Path(data['operation']).resolve() or operation.parent.resolve() != target.parent.resolve()):
            raise ArchiveError('recovery_required', operation, 'Journal path ownership mismatch')
        if data['state'] not in ('prepared', 'promoting', 'committed', 'rolled_back', 'recovery_required'):
            raise ArchiveError('recovery_required', operation, 'Unknown journal state')
        if data['host'] != socket.gethostname():
            raise ArchiveError('recovery_required', operation, 'Cannot establish dead owner on this host')
        if not _owner_dead(int(data['pid'])):
            raise ArchiveError('slot_busy', operation, 'Owner process still exists')
        owner = json.loads(lock_path(target).read_text(encoding='utf-8'))
        if owner['operation'] != str(operation) or owner['pid'] != data['pid'] or owner['host'] != data['host']:
            raise ArchiveError('recovery_required', operation, 'Lock ownership differs from journal')
        entries = tuple(Entry(**row) for row in data['originals'])
        expected = tuple(Entry(**row) for row in data['expected'])
        for rows in (entries, expected):
            for number, entry in enumerate(rows):
                matched = re.fullmatch(re.escape(target.name[:-6]) + r'\.([0-9]+)\.vgr', entry.name)
                if matched is None or int(matched[1]) != number:
                    raise ArchiveError('recovery_required', operation, 'Unsafe journal section path')
        allowed = {e.name: {e.sha256} for e in entries}
        for entry in expected:
            allowed.setdefault(entry.name, set()).add(entry.sha256)
        for path in target.parent.glob(f'{target.name[:-6]}.*.vgr'):
            if path.is_symlink() or digest(path) not in allowed.get(path.name, set()):
                raise ArchiveError('recovery_required', path, 'Unknown conflicting target bytes')
        report = data.get('report', {})
        if report:
            output = Path(report['path'])
            inputs = ReportInputs(files=tuple((operation / 'originals').iterdir()) + (operation / 'journal.json',),
                                  replays=(Path(data['source']), target))
            validate_report_outputs(inputs, (output,))
            if output.exists() and digest(output) not in (report['prior'], report['published']):
                raise ArchiveError('recovery_required', output, 'Report changed outside transaction')
            if report['existed']:
                backup = operation / 'prior-report'
                if digest(backup) != report['prior']:
                    raise ArchiveError('recovery_required', backup, 'Report backup hash mismatch')
                write_report_output(inputs, output, backup.read_bytes())
            else:
                output.unlink(missing_ok=True)
        _restore(target, operation / 'originals', entries, expected)
        data['state'] = 'rolled_back'
        _json(operation / 'journal.json', json.dumps(data, indent=2))
        (operation / 'recovery-required').unlink(missing_ok=True)
        lock_path(target).unlink(missing_ok=True)
        return target
    except ArchiveError:
        raise
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ArchiveError('recovery_required', operation, str(error), operation) from error


@contextmanager
def exclusive_lock(path: Path, operation: Path, *, recover_dead: bool = False) -> Iterator[None]:
    owner = json.dumps({'pid': os.getpid(), 'host': socket.gethostname(), 'operation': str(operation)})
    if recover_dead and path.exists() and not path.is_symlink():
        reaper = path.with_name(path.name + '.reaper')
        try:
            with reaper.open('x', encoding='utf-8') as stream:
                stream.write(owner)
            try:
                previous = json.loads(path.read_text(encoding='utf-8'))
                recorded = Path(previous['operation'])
                if (previous['host'] == socket.gethostname() and recorded.parent.resolve() == path.parent.resolve()
                        and _owner_dead(previous['pid'])):
                    path.unlink()
            finally:
                reaper.unlink()
        except (OSError, ValueError, TypeError, KeyError):
            raise ArchiveError('slot_busy', path, 'Cannot verify dead snapshot owner') from None
    try:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(owner)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        raise ArchiveError('slot_busy', path, 'Existing lock requires explicit verified recovery') from error
    try:
        yield
    finally:
        # A failed rollback deliberately retains ownership and the recovery pointer.
        if not (operation / 'recovery-required').exists():
            path.unlink(missing_ok=True)
