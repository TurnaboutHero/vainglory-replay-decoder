import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from vg.core.replay_input import ReplayInputError, discover_replay_files, replay_sections
from vg.core.replay_output import (
    ReportInputs, ReplayOutputError, publish_report_set, recover_report_set,
    validate_output_sources, write_report_output,
)
from vg.core.truth_input import TruthInputError, normalize_truth
from vg.core.report_recovery import ReportReceipt


CRASH_PROGRAM = '''
import os, sys
from pathlib import Path
from unittest.mock import patch
from vg.core.replay_output import ReportInputs, publish_report_set
root = Path(sys.argv[1])
real_replace = os.replace
def replace(source, target):
    if Path(target) == root / 'two.json':
        os._exit(73)
    real_replace(source, target)
with patch('os.replace', side_effect=replace):
    publish_report_set(ReportInputs(files=(root / 'input.bin',)),
                       {root / 'one.json': 'new one', root / 'two.json': 'new two'},
                       root / 'receipt.json')
'''


class ProductIORecovery(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input.bin'
        self.source.write_bytes(b'original input')
        self.one, self.two, self.receipt = (self.root / name for name in ('one.json', 'two.json', 'receipt.json'))
        self.one.write_bytes(b'old one')
        self.two.write_bytes(b'old two')
        self.inputs = ReportInputs(files=(self.source,))

    def crash(self) -> ReportReceipt:
        result = subprocess.run([sys.executable, '-B', '-c', CRASH_PROGRAM, str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertEqual(self.one.read_bytes(), b'new one')
        self.assertEqual(self.two.read_bytes(), b'old two')
        pending = json.loads(self.receipt.read_text())
        self.assertEqual(pending['status'], 'pending')
        return pending

    def test_restart_restores_prior_receipt_and_outputs(self) -> None:
        publish_report_set(self.inputs, {self.one: b'old one', self.two: b'old two'}, self.receipt)
        prior_receipt = self.receipt.read_bytes()
        self.crash()
        invocation = [sys.executable, '-B', '-c',
                      'import sys; from pathlib import Path; from vg.core.replay_output import recover_report_set; '
                      'print(recover_report_set(Path(sys.argv[1]))["status"])', str(self.receipt)]
        recovered = subprocess.run(invocation, capture_output=True, text=True)
        self.assertEqual((recovered.returncode, recovered.stdout.strip()), (0, 'rolled_back'), recovered.stderr)
        self.assertEqual((self.one.read_bytes(), self.two.read_bytes()), (b'old one', b'old two'))
        self.assertEqual(self.receipt.read_bytes(), prior_receipt)
        self.assertEqual(self.source.read_bytes(), b'original input')
        self.assertEqual(list(self.root.glob('.*.tmp')), [])

    def test_recovery_refuses_unowned_changes_and_keeps_backups(self) -> None:
        pending = self.crash()
        self.one.write_bytes(b'written by another owner')
        with self.assertRaises(ReplayOutputError) as error:
            recover_report_set(self.receipt)
        self.assertEqual(error.exception.code, 'recovery_required')
        self.assertEqual(self.one.read_bytes(), b'written by another owner')
        self.assertTrue(all(Path(entry['backup']).exists() for entry in pending['entries']))
        self.assertEqual(json.loads(self.receipt.read_text())['status'], 'pending')

    def test_recovery_rejects_corrupt_backup_or_receipt(self) -> None:
        pending = self.crash()
        backup = Path(pending['entries'][0]['backup'])
        backup.write_bytes(b'damaged')
        with self.assertRaises(ReplayOutputError) as error:
            recover_report_set(self.receipt)
        self.assertEqual(error.exception.code, 'recovery_required')
        self.assertEqual(self.one.read_bytes(), b'new one')
        pending['entries'][0]['backup'] = str(self.source)
        self.receipt.write_text(json.dumps(pending))
        with self.assertRaises(ReplayOutputError):
            recover_report_set(self.receipt)
        self.assertEqual(self.source.read_bytes(), b'original input')

    def test_recovery_refuses_source_hardlink_and_output_symlink(self) -> None:
        self.crash()
        self.one.unlink()
        os.link(self.source, self.one)
        with self.assertRaises(ReplayOutputError):
            recover_report_set(self.receipt)
        self.one.unlink()
        self.one.symlink_to(self.source)
        with self.assertRaises(ReplayOutputError):
            recover_report_set(self.receipt)
        self.assertEqual(self.source.read_bytes(), b'original input')

    def test_staging_and_backup_fsync_failure_preserve_old_generation(self) -> None:
        real_fsync = os.fsync
        for fail_at in (1, 2, 3, 4, 5):
            calls = 0

            def fsync(fd) -> None:
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise OSError('injected fsync failure')
                real_fsync(fd)

            with self.subTest(fail_at=fail_at), patch('os.fsync', side_effect=fsync):
                with self.assertRaises(ReplayOutputError) as error:
                    publish_report_set(self.inputs, {self.one: 'new one', self.two: 'new two'}, self.receipt)
                self.assertEqual(error.exception.code, 'publication_failed')
            self.assertEqual((self.one.read_bytes(), self.two.read_bytes()), (b'old one', b'old two'))
            self.assertFalse(self.receipt.exists())
            self.assertEqual(list(self.root.glob('.*.backup')), [])
            self.assertEqual(list(self.root.glob('.*.tmp')), [])

    def test_original_source_inode_disappearance_and_reserved_paths(self) -> None:
        replacement = self.root / 'replacement.bin'
        replacement.write_bytes(self.source.read_bytes())
        os.replace(replacement, self.source)
        with self.assertRaises(ReplayOutputError) as error:
            write_report_output(self.inputs, self.one, 'new')
        self.assertEqual(error.exception.code, 'input_changed')
        inputs = ReportInputs(files=(self.source,))
        self.source.unlink()
        with self.assertRaises(ReplayOutputError) as error:
            write_report_output(inputs, self.one, 'new')
        self.assertEqual(error.exception.code, 'input_changed')
        reserved = self.root / 'database.db-wal'
        with self.assertRaises(ReplayOutputError):
            validate_output_sources((reserved,), reserved)
        self.assertEqual(self.one.read_bytes(), b'old one')

    def test_aliases_are_rejected_before_absolute_key_normalization(self) -> None:
        relative = Path(os.path.relpath(self.one, Path.cwd()))
        self.assertNotEqual(relative, self.one)
        with self.assertRaises(ReplayOutputError) as error:
            publish_report_set(self.inputs, {relative: 'first', self.one: 'second'}, self.receipt)
        self.assertEqual(error.exception.code, 'output_alias')
        self.assertEqual(self.one.read_bytes(), b'old one')

    def test_discovery_io_errors_and_unreadable_sections_are_typed(self) -> None:
        with patch('vg.core.replay_input.os.walk', side_effect=PermissionError('denied')):
            with self.assertRaises(ReplayInputError) as error:
                discover_replay_files(self.root)
        self.assertEqual(error.exception.code, 'input_unreadable')
        frame0 = self.root / 'match.0.vgr'
        frame0.write_bytes(b'opaque archive section')
        with patch('pathlib.Path.read_bytes', side_effect=PermissionError('denied')):
            with self.assertRaises(ReplayInputError) as error:
                replay_sections(frame0)
        self.assertEqual(error.exception.code, 'input_unreadable')
        self.assertEqual(replay_sections(frame0), ((0, frame0),))

    def test_truth_operation_can_require_disk_reference(self) -> None:
        with self.assertRaises(TruthInputError) as error:
            normalize_truth({'replay_name': 'match'}, self.root / 'truth.json', require_replay_file=True)
        self.assertEqual(error.exception.code, 'truth_invalid')
