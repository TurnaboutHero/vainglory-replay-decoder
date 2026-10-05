import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from vg.core import replay_archive as archive
from vg.core import vgr_watcher as watcher_module
from vg.core.vgr_watcher import VGRWatcher
from vg.core.vgr_loader import VGRLoader


def hashes(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}


class TestProductWatcher(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.backup = self.root / 'backup'
        (self.source / 'a.0.vgr').write_bytes(b'a' * 2048)
        (self.source / 'b.0.vgr').write_bytes(b'b')
        self.watcher = VGRWatcher(str(self.backup), str(self.source))

    def snapshots(self):
        return sorted(p.parent for p in self.backup.rglob('snapshot.json'))

    def test_watcher_happy_growing_full_bytes_manifest_restart(self):
        (self.source / 'replayManifest-a.txt').write_text('manifest-one')
        self.assertTrue(self.watcher.scan_once())
        self.assertEqual(len(self.snapshots()), 2)
        originals = {str(p): hashes(p) for p in self.snapshots()}
        (self.source / 'a.1.vgr').write_bytes(b'appended')
        (self.source / 'a.0.vgr').write_bytes(b'a' * 1500 + b'changed-tail')
        self.assertTrue(self.watcher.scan_once())
        self.assertEqual(len(self.snapshots()), 3)
        latest = next(row for row in self.watcher.last_scan_report if row['status'] == 'success')
        saved = Path(latest['path'])
        for name in ('a.0.vgr', 'a.1.vgr', 'replayManifest-a.txt'):
            self.assertEqual((saved / name).read_bytes(), (self.source / name).read_bytes())
        (self.source / 'replayManifest-a.txt').write_text('manifest-two')
        self.assertTrue(self.watcher.scan_once())
        self.assertEqual(len(self.snapshots()), 4)
        restarted = VGRWatcher(str(self.backup), str(self.source))
        self.assertFalse(restarted.scan_once())
        self.assertTrue(all(row['status'] == 'unchanged' for row in restarted.last_scan_report))
        self.assertEqual({path: hashes(Path(path)) for path in originals}, originals)
        print(json.dumps({'original_snapshots': originals, 'latest': restarted.last_scan_report}))

    def test_watcher_happy_continuous_uses_same_engine_and_distinct_source(self):
        calls = 0
        def controlled_sleep(interval):
            nonlocal calls
            calls += 1
            if calls == 1:
                (self.source / 'a.1.vgr').write_bytes(b'new-section')
            else:
                raise KeyboardInterrupt
        with patch.object(watcher_module.time, 'sleep', side_effect=controlled_sleep), contextlib.redirect_stdout(io.StringIO()):
            self.watcher.watch()
        self.assertEqual(len(self.snapshots()), 3)
        other = self.root / 'other-source'
        other.mkdir()
        (other / 'b.0.vgr').write_bytes(b'b')
        self.assertTrue(VGRWatcher(str(self.backup), str(other)).scan_once())
        self.assertEqual(len(self.snapshots()), 4)

    def test_watcher_happy_exact_uuid_manifest_changes(self):
        match_uuid = '11111111-2222-3333-4444-555555555555'
        family = match_uuid + '-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        (self.source / 'a.0.vgr').rename(self.source / f'{family}.0.vgr')
        (self.source / 'b.0.vgr').unlink()
        exact = self.source / f'replayManifest-{match_uuid}.txt'
        wrong = self.source / 'replayManifest-11111111.txt'
        exact.write_text('exact-one')
        wrong.write_text('unrelated-prefix')
        self.assertTrue(self.watcher.scan_once(), self.watcher.last_scan_report)
        saved = self.snapshots()[0]
        self.assertEqual((saved / exact.name).read_text(), 'exact-one')
        self.assertFalse((saved / wrong.name).exists())
        exact.write_text('exact-two')
        self.assertTrue(self.watcher.scan_once())
        self.assertEqual(len(self.snapshots()), 2)
        self.assertEqual((saved / exact.name).read_text(), 'exact-one')
        wrong.write_text('still-unrelated')
        self.assertFalse(self.watcher.scan_once())
        backup = VGRLoader(str(self.source)).backup_active_replay(str(self.root / 'manual'))
        self.assertEqual((backup / exact.name).read_text(), 'exact-two')

    def test_watcher_failure_ambiguous_exact_manifests(self):
        match_uuid = '11111111-2222-3333-4444-555555555555'
        family = match_uuid + '-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        (self.source / 'a.0.vgr').rename(self.source / f'{family}.0.vgr')
        (self.source / 'b.0.vgr').unlink()
        (self.source / f'replayManifest-{match_uuid}.txt').write_text('match')
        (self.source / f'replayManifest-{family}.txt').write_text('family')
        self.assertFalse(self.watcher.scan_once())
        self.assertEqual(self.watcher.last_scan_report[0]['error_code'], 'manifest_ambiguous')
        self.assertEqual(self.snapshots(), [])

    def test_watcher_failure_copy_and_source_mutation_retry_preserve_old(self):
        self.assertTrue(self.watcher.scan_once())
        originals = {str(p): hashes(p) for p in self.snapshots()}
        receipts = {str(p): p.read_bytes() for p in (self.backup / '.watcher').glob('*.json')}
        (self.source / 'a.1.vgr').write_bytes(b'appended')
        real_copy = archive._copy
        def fail_copy(src, dst):
            if src.name.startswith('a.'):
                raise OSError('copy failed')
            real_copy(src, dst)
        with patch.object(archive, '_copy', side_effect=fail_copy):
            self.assertFalse(self.watcher.scan_once())
        self.assertTrue(any(row['status'] == 'error' for row in self.watcher.last_scan_report))
        self.assertEqual({path: Path(path).read_bytes() for path in receipts}, receipts)
        attempts = 0
        def mutate(src, dst):
            nonlocal attempts
            real_copy(src, dst)
            if src.name == 'a.0.vgr':
                attempts += 1
                src.write_bytes(src.read_bytes() + b'changed')
        with patch.object(archive, '_copy', side_effect=mutate):
            self.assertFalse(self.watcher.scan_once())
        self.assertEqual(attempts, 2)
        self.assertTrue(any(row['status'] == 'pending' and row['error_code'] == 'source_changed' for row in self.watcher.last_scan_report))
        self.assertEqual({path: Path(path).read_bytes() for path in receipts}, receipts)
        self.assertEqual({path: hashes(Path(path)) for path in originals}, originals)
        self.assertTrue(VGRWatcher(str(self.backup), str(self.source)).scan_once())
        self.assertEqual(len(self.snapshots()), 3)

    def test_watcher_failure_corrupt_snapshot_receipt_is_not_acknowledged(self):
        self.assertTrue(self.watcher.scan_once())
        saved = next(p for p in self.snapshots() if (p / 'a.0.vgr').exists())
        receipt = saved / 'snapshot.json'
        good = receipt.read_bytes()
        frame0 = self.source / 'a.0.vgr'
        def corrupt(data):
            data = json.loads(data)
            return {'invalid_json': lambda: b'{"sections": [',
                    'wrong_scope': lambda: json.dumps({**data, 'scope': '0' * 64}).encode(),
                    'wrong_source_scope': lambda: json.dumps({**data, 'source_scope': 'sha256:' + '0' * 64}).encode(),
                    'missing_sections': lambda: json.dumps({k: v for k, v in data.items() if k != 'sections'}).encode()}
        for kind, payload in corrupt(good).items():
            with self.subTest(kind=kind):
                receipt.chmod(0o644)
                receipt.write_bytes(payload())
                with self.assertRaises(archive.ArchiveError) as reused:
                    self.watcher.backup_replay('a')
                self.assertEqual(reused.exception.code, 'recovery_required')
                with self.assertRaises(archive.ArchiveError) as republished:
                    archive.snapshot(frame0, saved)
                self.assertEqual(republished.exception.code, 'recovery_required')
                self.assertEqual(receipt.read_bytes(), payload())
        receipt.write_bytes(good)
        identity = hashlib.sha256(str(frame0.absolute().resolve()).encode()).hexdigest()
        watcher_receipt = self.backup / '.watcher' / f'{identity}.json'
        acknowledged = watcher_receipt.read_bytes()
        for payload in (b'not json', b'[]', json.dumps({'snapshot': str(saved)}).encode()):
            with self.subTest(watcher_receipt=payload[:12]):
                watcher_receipt.write_bytes(payload)
                with self.assertRaises(archive.ArchiveError) as unreadable:
                    self.watcher.backup_replay('a')
                self.assertEqual(unreadable.exception.code, 'recovery_required')
        watcher_receipt.write_bytes(acknowledged)
        self.assertEqual(self.watcher.backup_replay('a'), saved)
        self.assertEqual(archive.snapshot(frame0, saved)['path'], str(saved))

    def test_watcher_failure_one_family_does_not_hide_other_and_cli_nonzero(self):
        (self.source / 'a.2.vgr').write_bytes(b'gap')
        self.assertTrue(self.watcher.scan_once())
        statuses = {Path(row['replay']).name: row['status'] for row in self.watcher.last_scan_report}
        self.assertEqual(statuses, {'a.0.vgr': 'error', 'b.0.vgr': 'success'})
        completed = subprocess.run([sys.executable, '-B', '-m', 'vg.core.vgr_watcher', str(self.backup),
                                    '--temp', str(self.source), '--once'], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(any(row['error_code'] == 'replay_gap' for row in report))

    def test_watcher_failure_concurrent_scan_and_latest_publication(self):
        real_copy = archive._copy
        competitor_reports = []
        invoked = False
        def competing(src, dst):
            nonlocal invoked
            if not invoked:
                invoked = True
                competitor = VGRWatcher(str(self.backup), str(self.source))
                competitor.scan_once()
                competitor_reports.extend(competitor.last_scan_report)
                self.assertFalse(any((p / 'a.0.vgr').exists() for p in self.snapshots()))
            real_copy(src, dst)
        with patch.object(archive, '_copy', side_effect=competing):
            self.assertTrue(self.watcher.scan_once())
        self.assertTrue(any(row['status'] == 'pending' and row['error_code'] == 'slot_busy' for row in competitor_reports))
        before = {str(p): p.read_bytes() for p in (self.backup / '.watcher').glob('*.json')}
        (self.source / 'a.1.vgr').write_bytes(b'new')
        with patch.object(watcher_module, 'write_report_output', side_effect=OSError('latest publication failed')):
            self.assertFalse(self.watcher.scan_once())
        self.assertEqual({path: Path(path).read_bytes() for path in before}, before)
        self.assertTrue(VGRWatcher(str(self.backup), str(self.source)).scan_once())

    def test_watcher_failure_process_restart_after_partial_stage(self):
        program = f'''from pathlib import Path
import os
from vg.core import replay_archive as archive
from vg.core.vgr_watcher import VGRWatcher
original = archive._copy
def crash(source, target):
    original(source, target)
    os._exit(0)
archive._copy = crash
VGRWatcher({str(self.backup)!r}, {str(self.source)!r}).scan_once()
'''
        child = subprocess.run([sys.executable, '-B', '-c', program], capture_output=True, text=True)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertTrue(list(self.backup.rglob('.snapshot-*')))
        self.assertFalse(list(self.backup.rglob('snapshot.json')))
        self.assertFalse(list((self.backup / '.watcher').glob('*.json')))
        self.assertEqual(VGRLoader().list_saved_replays(str(self.backup)), [])
        restarted = VGRWatcher(str(self.backup), str(self.source))
        self.assertTrue(restarted.scan_once(), restarted.last_scan_report)
        self.assertEqual(len(self.snapshots()), 2)
        self.assertEqual(len(VGRLoader().list_saved_replays(str(self.backup))), 2)
        self.assertFalse(VGRWatcher(str(self.backup), str(self.source)).scan_once())


if __name__ == '__main__':
    unittest.main()
