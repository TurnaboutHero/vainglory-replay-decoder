import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from vg.core import replay_archive as archive
from vg.core.vgr_loader import VGRLoader
from vg.tools import vgrplay_inject as inject


def family(root, name, count, prefix):
    root.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (root / f'{name}.{index}.vgr').write_bytes(prefix + str(index).encode())


def hashes(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.vgr')}


class TestProductLoader(unittest.TestCase):
    def test_loader_happy_copy_sync_preserves_read_only_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            destination = Path(directory) / 'copy'
            source.write_bytes(b'generated durable archive copy')
            source.chmod(stat.S_IREAD)
            try:
                archive._copy(source, destination)
                self.assertEqual(destination.read_bytes(), source.read_bytes())
                self.assertFalse(destination.stat().st_mode & stat.S_IWUSR)
                with patch.object(archive.os, 'fsync', side_effect=OSError('sync failed')):
                    with self.assertRaisesRegex(OSError, 'sync failed'):
                        destination.chmod(stat.S_IWRITE | stat.S_IREAD)
                        archive._copy(source, destination)
                self.assertFalse(destination.stat().st_mode & stat.S_IWUSR)
            finally:
                source.chmod(stat.S_IWRITE | stat.S_IREAD)
                if destination.exists():
                    destination.chmod(stat.S_IWRITE | stat.S_IREAD)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source, self.target = self.root / 'source', self.root / 'target'
        family(self.source, 'saved', 3, b'source')
        family(self.target, 'slot', 4, b'original')
        self.old_source = hashes(self.source)
        self.old_target = hashes(self.target)
        self.report = self.root / 'report.json'
        self.report.write_text('old-report')

    def run_fake(self, cmd, **kwargs):
        for path in self.target.glob('slot.*.vgr'):
            path.unlink()
        for path in self.source.glob('saved.*.vgr'):
            shutil.copy2(path, self.target / path.name.replace('saved.', 'slot.'))
        return subprocess.CompletedProcess(cmd, 0, 'ok', '')

    def assert_restored(self):
        self.assertEqual(hashes(self.target), self.old_target)
        self.assertEqual(hashes(self.source), self.old_source)
        self.assertEqual(self.report.read_text(), 'old-report')

    def test_loader_happy_load_and_duplicate_names(self):
        family(self.target, 'other', 1, b'untouched')
        other = (self.target / 'other.0.vgr').read_bytes()
        result = VGRLoader(str(self.target)).load_replay(str(self.source), target_name='slot')
        self.assertTrue(result['success'], result)
        self.assertEqual(result['frames_copied'], 3)
        expected = {name.replace('saved.', 'slot.'): value for name, value in self.old_source.items()}
        self.assertEqual({k: v for k, v in hashes(self.target).items() if k.startswith('slot.')}, expected)
        self.assertEqual((self.target / 'other.0.vgr').read_bytes(), other)
        self.assertEqual(hashes(Path(result['recovery']) / 'originals'), self.old_target)
        self.assertEqual(hashes(self.source), self.old_source)
        family(self.root / 'more' / 'a', 'same', 1, b'a')
        family(self.root / 'more' / 'b', 'same', 1, b'b')
        self.assertEqual(len(VGRLoader().list_saved_replays(str(self.root / 'more'))), 2)
        print(json.dumps({'source': self.old_source, 'target': expected, 'recoverable': self.old_target}))

    def test_loader_happy_fake_vgrplay_cli(self):
        args = ['vgrplay', '--source-dir', str(self.source), '--replay-name', 'saved', '--temp-dir', str(self.target),
                '--target-name', 'slot', '-o', str(self.report)]
        with patch.object(sys, 'argv', args), patch.object(inject.subprocess, 'run', side_effect=self.run_fake), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(inject.main(), 0)
        result = json.loads(self.report.read_text())
        self.assertTrue(result['verification']['ok'])
        self.assertEqual(result['verification']['verified_frame_count'], 3)
        self.assertEqual(hashes(Path(result['recovery']) / 'originals'), self.old_target)
        self.assertEqual(hashes(self.source), self.old_source)

    def test_loader_happy_real_cli_fake_executable(self):
        script = self.root / 'fake.py'
        script.write_text('import pathlib, shutil, sys\na=sys.argv\ns=pathlib.Path(a[a.index("-source")+1])\n'
                          't=pathlib.Path(a[a.index("-overwrite")+1])\nn=a[a.index("-sname")+1]\no=a[a.index("-oname")+1]\n'
                          'for p in t.glob(o+".*.vgr"): p.unlink()\n'
                          'for p in s.glob(n+".*.vgr"): shutil.copy2(p,t/(o+p.name[len(n):]))\n')
        executable = self.root / ('fake.cmd' if os.name == 'nt' else 'fake')
        if os.name == 'nt':
            executable.write_text(f'@"{sys.executable}" -B "{script}" %*\n')
        else:
            executable.write_text(f'#!/bin/sh\nexec "{sys.executable}" -B "{script}" "$@"\n')
            executable.chmod(0o700)
        completed = subprocess.run([sys.executable, '-B', '-m', 'vg.tools.vgrplay_inject',
            '--source-dir', str(self.source), '--replay-name', 'saved', '--temp-dir', str(self.target),
            '--target-name', 'slot', '--vgrplay', str(executable), '-o', str(self.report)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(json.loads(self.report.read_text())['verification']['ok'])
        self.assertEqual(hashes(self.source), self.old_source)

    def test_loader_failure_gap_self_ambiguity_links_busy(self):
        (self.source / 'saved.1.vgr').unlink()
        result = VGRLoader(str(self.target)).load_replay(str(self.source))
        self.assertEqual(result['error_code'], 'replay_gap')
        family(self.source, 'saved', 3, b'source')
        self.assertFalse(VGRLoader(str(self.source)).load_replay(str(self.source))['success'])
        family(self.target, 'other', 1, b'other')
        self.assertEqual(VGRLoader(str(self.target)).load_replay(str(self.source))['error_code'], 'replay_ambiguous')
        (self.target / 'other.0.vgr').unlink()
        lock = archive.lock_path(self.target / 'slot.0.vgr')
        lock.write_text('uncertain owner')
        self.assertEqual(VGRLoader(str(self.target)).load_replay(str(self.source))['error_code'], 'slot_busy')
        lock.unlink()
        (self.target / 'slot.0.vgr').unlink()
        os.link(self.source / 'saved.0.vgr', self.target / 'slot.0.vgr')
        self.assertEqual(VGRLoader(str(self.target)).load_replay(str(self.source))['error_code'], 'archive_overlap')

    def test_loader_failure_mutating_source_and_target(self):
        original = archive._copy
        for selected, code in ((self.source, 'source_changed'), (self.target, 'target_changed')):
            with self.subTest(code=code):
                family(self.source, 'saved', 3, b'source')
                family(self.target, 'slot', 4, b'original')
                touched = False
                def changing(src, dst):
                    nonlocal touched
                    original(src, dst)
                    if not touched:
                        touched = True
                        name = 'saved' if selected == self.source else 'slot'
                        (selected / f'{name}.0.vgr').write_bytes(b'external-change')
                with patch.object(archive, '_copy', side_effect=changing):
                    result = VGRLoader(str(self.target)).load_replay(str(self.source))
                self.assertFalse(result['success'])
                self.assertEqual(result['error_code'], code)
                untouched = self.target if selected == self.source else self.source
                self.assertEqual(hashes(untouched), self.old_target if untouched == self.target else self.old_source)

    def test_loader_failure_partial_replace_and_failed_rollback(self):
        real_replace = os.replace
        for rollback_fails in (False, True):
            with self.subTest(rollback_fails=rollback_fails):
                def failing(src, dst):
                    if Path(src).parent.name == 'stage' and Path(dst).name == 'slot.1.vgr':
                        raise OSError('promotion failure')
                    if rollback_fails and Path(src).name.startswith('restore-'):
                        raise OSError('rollback failure')
                    return real_replace(src, dst)
                with patch.object(archive.os, 'replace', side_effect=failing):
                    result = VGRLoader(str(self.target)).load_replay(str(self.source))
                self.assertFalse(result['success'])
                if rollback_fails:
                    self.assertEqual(result['error_code'], 'recovery_required')
                    recovery = Path(result['recovery'])
                    self.assertEqual(hashes(recovery / 'originals'), self.old_target)
                    self.assertTrue((recovery / 'journal.json').exists())
                    self.assertTrue(archive.lock_path(self.target / 'slot.0.vgr').exists())
                else:
                    self.assert_restored()

    def test_loader_failure_subprocess_and_report_publication(self):
        for failure in ('timeout', 'nonzero', 'mismatch', 'stage', 'replace', 'serialize'):
            with self.subTest(failure=failure):
                def process(cmd, **kwargs):
                    result = self.run_fake(cmd)
                    if failure == 'timeout':
                        raise subprocess.TimeoutExpired(cmd, 1)
                    if failure == 'nonzero':
                        return subprocess.CompletedProcess(cmd, 7, '', 'failed')
                    if failure == 'mismatch':
                        (self.target / 'slot.1.vgr').write_bytes(b'bad')
                    return result
                real_replace = os.replace
                def replace(src, dst):
                    if failure == 'replace' and Path(dst) == self.report:
                        raise OSError('report replace failed')
                    return real_replace(src, dst)
                real_write = inject.write_report_output
                def publish(inputs, output, payload):
                    if failure == 'stage':
                        raise OSError('report staging failed')
                    return real_write(inputs, output, payload)
                real_dumps = json.dumps
                def serialize(payload, *args, **kwargs):
                    if failure == 'serialize' and 'verification' in payload:
                        raise TypeError()
                    return real_dumps(payload, *args, **kwargs)
                with patch.object(inject.subprocess, 'run', side_effect=process), patch.object(inject, 'write_report_output', side_effect=publish), patch.object(os, 'replace', side_effect=replace), patch.object(json, 'dumps', side_effect=serialize):
                    with self.assertRaises((ValueError, OSError)):
                        inject.inject_replay_with_vgrplay(str(self.source), 'saved', str(self.target), output=str(self.report))
                self.assert_restored()
                self.assertFalse(archive.lock_path(self.target / 'slot.0.vgr').exists())

    def test_loader_failure_report_aliases_before_and_after_process(self):
        for root, name in ((self.source, 'saved'), (self.target, 'slot')):
            for kind in ('direct', 'future', 'symlink', 'hardlink'):
                with self.subTest(root=root.name, kind=kind):
                    alias = root / f'{name}.0.vgr'
                    if kind == 'future':
                        alias = root / f'{name}.99.vgr'
                    if kind in ('symlink', 'hardlink'):
                        alias = self.root / f'{root.name}-{kind}.json'
                        if kind == 'symlink':
                            alias.symlink_to(root / f'{name}.0.vgr')
                        else:
                            os.link(root / f'{name}.0.vgr', alias)
                    with patch.object(inject.subprocess, 'run') as process:
                        with self.assertRaises(ValueError):
                            inject.inject_replay_with_vgrplay(str(self.source), 'saved', str(self.target), output=str(alias))
                        process.assert_not_called()
                    if kind in ('symlink', 'hardlink'):
                        alias.unlink()
                    self.assert_restored()
        late = self.root / 'late.json'
        def process(cmd, **kwargs):
            result = self.run_fake(cmd)
            late.symlink_to(self.source / 'saved.0.vgr')
            return result
        with patch.object(inject.subprocess, 'run', side_effect=process):
            with self.assertRaises(ValueError):
                inject.inject_replay_with_vgrplay(str(self.source), 'saved', str(self.target), output=str(late))
        self.assert_restored()
        for selected in (self.source / 'saved.0.vgr', self.target / 'slot.0.vgr'):
            for kind in ('symlink', 'hardlink'):
                with self.subTest(late_existing=selected.name, kind=kind):
                    def late_existing(cmd, **kwargs):
                        result = self.run_fake(cmd)
                        self.report.unlink()
                        if kind == 'symlink':
                            self.report.symlink_to(selected)
                        else:
                            os.link(selected, self.report)
                        return result
                    with patch.object(inject.subprocess, 'run', side_effect=late_existing):
                        with self.assertRaises(ValueError):
                            inject.inject_replay_with_vgrplay(str(self.source), 'saved', str(self.target), output=str(self.report))
                    self.assert_restored()
                    self.assertFalse(self.report.is_symlink())

    def test_loader_failure_interrupt_overlap_and_ambiguous_source(self):
        with self.assertRaises(archive.ArchiveError):
            VGRLoader(str(self.source)).backup_active_replay(str(self.source))
        self.assertEqual(hashes(self.source), self.old_source)
        family(self.root / 'duplicates' / 'one', 'saved', 1, b'one')
        family(self.root / 'duplicates' / 'two', 'saved', 1, b'two')
        self.assertEqual(VGRLoader(str(self.target)).load_replay(str(self.root / 'duplicates'), 'saved')['error_code'], 'replay_ambiguous')
        real_replace = os.replace
        def interrupt(src, dst):
            if Path(src).parent.name == 'stage' and Path(dst).name == 'slot.1.vgr':
                raise KeyboardInterrupt
            return real_replace(src, dst)
        with patch.object(os, 'replace', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            VGRLoader(str(self.target)).load_replay(str(self.source))
        self.assert_restored()

    def test_loader_failure_restart_prepared_and_promoting(self):
        for state in ('prepared', 'promoting', 'report_published'):
            with self.subTest(state=state):
                program = ('from pathlib import Path; import os; from vg.core.replay_archive import replacement; '
                           f'ctx=replacement(Path({str(self.source / "saved.0.vgr")!r}), Path({str(self.target / "slot.0.vgr")!r})); '
                           'tx=ctx.__enter__(); '
                           + ('tx.promote(); ' if state != 'prepared' else '')
                           + (f'tx.prepare_report(Path({str(self.report)!r}), "new-report"); Path({str(self.report)!r}).write_text("new-report"); ' if state == 'report_published' else '')
                           + 'print(tx.operation, flush=True); os._exit(0)')
                child = subprocess.run([sys.executable, '-B', '-c', program], capture_output=True, text=True, check=True)
                operation = Path(child.stdout.strip())
                self.assertEqual(json.loads((operation / 'journal.json').read_text())['state'], 'promoting' if state == 'report_published' else state)
                archive.recover(operation)
                self.assert_restored()
                self.assertFalse(archive.lock_path(self.target / 'slot.0.vgr').exists())
