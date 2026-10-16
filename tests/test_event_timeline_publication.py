"""Failure and optimistic-conflict boundaries for timeline file publication."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.test_event_timeline import packet
from vg.analysis import event_timeline, timeline_output


class TimelinePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'
        self.replay.write_bytes(packet(1, 0x9999, b'opaque'))
        self.output = self.root / 'report.jsonl'
        self.output.write_bytes(b'prior report\n')

    def run_main(self, output=True):
        stdout, stderr = io.StringIO(), io.StringIO()
        args = [str(self.replay)] + (['--output', str(self.output)] if output else [])
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = event_timeline.main(args)
        return status, stdout.getvalue(), stderr.getvalue()

    def assert_clean(self):
        self.assertEqual(list(self.root.glob('.report.jsonl.*.tmp')), [])

    def test_success_replaces_only_after_all_rows_and_cleans_temporary(self):
        def rows(*args, **kwargs):
            for number in range(1000):
                self.assertEqual(self.output.read_bytes(), b'prior report\n')
                yield {'number': number, 'label': '한글'}
        with patch.object(event_timeline, 'iter_timeline', rows):
            status, stdout, stderr = self.run_main()
        self.assertEqual((status, stdout, stderr), (0, '', ''))
        data = self.output.read_bytes()
        self.assertNotIn(b'\r', data)
        self.assertEqual(len(data.splitlines()), 1000)
        self.assertEqual(json.loads(data.splitlines()[-1]), {'number': 999, 'label': '한글'})
        self.assert_clean()

    def test_success_creates_absent_output(self):
        self.output.unlink()
        with patch.object(event_timeline, 'iter_timeline', return_value=iter([{'value': 1}])):
            self.assertEqual(self.run_main(), (0, '', ''))
        self.assertEqual(self.output.read_bytes(), b'{"value": 1}\n')
        self.assert_clean()

    def test_late_malformed_input_preserves_existing_and_absent_outputs(self):
        (self.root / 'match.1.vgr').write_bytes(packet(2, 0x9999) + b'\0')
        for exists in (True, False):
            with self.subTest(exists=exists):
                if not exists:
                    self.output.unlink()
                status, _, error = self.run_main()
                self.assertEqual(status, 2)
                self.assertIn('truncated header', error)
                self.assertEqual(self.output.exists(), exists)
                if exists:
                    self.assertEqual(self.output.read_bytes(), b'prior report\n')
                self.assert_clean()

    def test_serialization_failure_after_valid_row_preserves_report(self):
        for bad in (float('nan'), object()):
            with self.subTest(bad=type(bad).__name__):
                with patch.object(event_timeline, 'iter_timeline', return_value=iter([{'ok': 1}, {'bad': bad}])):
                    self.assertEqual(self.run_main()[0], 2)
                self.assertEqual(self.output.read_bytes(), b'prior report\n')
                self.assert_clean()

    def test_partial_write_or_encoding_failure_preserves_report(self):
        for error in (OSError('disk full'), UnicodeError('encoding failed')):
            def fail(rows, stream):
                stream.write('partial\n')
                raise error
            with self.subTest(error=type(error).__name__), patch.object(event_timeline, '_write_jsonl', fail):
                self.assertEqual(self.run_main()[0], 2)
            self.assertEqual(self.output.read_bytes(), b'prior report\n')
            self.assert_clean()

    def test_fsync_and_replace_permission_errors_preserve_report(self):
        for method in ('fsync', 'replace'):
            with self.subTest(method=method), patch.object(timeline_output.os, method, side_effect=PermissionError('denied')):
                self.assertEqual(self.run_main()[0], 2)
            self.assertEqual(self.output.read_bytes(), b'prior report\n')
            self.assert_clean()

    def test_flush_failure_preserves_report_and_removes_stage(self):
        factory = timeline_output.tempfile.NamedTemporaryFile
        def fail_flush(*args, **kwargs):
            stream = factory(*args, **kwargs)
            stream.flush = lambda: (_ for _ in ()).throw(OSError('flush failed'))
            return stream
        with patch.object(timeline_output.tempfile, 'NamedTemporaryFile', fail_flush):
            self.assertEqual(self.run_main()[0], 2)
        self.assertEqual(self.output.read_bytes(), b'prior report\n')
        self.assert_clean()

    def test_external_overwrite_create_delete_and_same_bytes_replacement_conflict(self):
        for action in ('overwrite', 'create', 'delete', 'replace_same'):
            with self.subTest(action=action):
                self.output.write_bytes(b'prior report\n')
                if action == 'create':
                    self.output.unlink()
                def rows(*args, **kwargs):
                    yield {'before': 1}
                    if action in ('overwrite', 'create'):
                        self.output.write_bytes(b'external report\n')
                    elif action == 'delete':
                        self.output.unlink()
                    else:
                        other = self.root / 'external.tmp'
                        other.write_bytes(b'prior report\n')
                        os.replace(other, self.output)
                    yield {'after': 2}
                with patch.object(event_timeline, 'iter_timeline', rows):
                    status, _, error = self.run_main()
                self.assertEqual(status, 2)
                self.assertIn('publication_conflict', error)
                if action == 'delete':
                    self.assertFalse(self.output.exists())
                else:
                    expected = b'prior report\n' if action == 'replace_same' else b'external report\n'
                    self.assertEqual(self.output.read_bytes(), expected)
                self.assert_clean()

    def test_exclusive_creation_does_not_overwrite_a_last_moment_arrival(self):
        self.output.unlink()
        def appeared(source, target):
            self.output.write_bytes(b'external arrival')
            raise FileExistsError('appeared')
        with patch.object(timeline_output.os, 'link', appeared):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'external arrival')
        self.assert_clean()

    def test_destination_is_frozen_before_input_discovery(self):
        discover = event_timeline._discover_sections
        def changed(path):
            self.output.write_bytes(b'external before parsing')
            return discover(path)
        with patch.object(event_timeline, '_discover_sections', changed):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'external before parsing')
        self.assert_clean()

    def test_parent_replacement_preserves_foreign_stage_and_reports_conflict(self):
        parent = self.root / 'reports'
        parent.mkdir()
        self.output = parent / 'report.jsonl'
        self.output.write_bytes(b'prior report\n')
        moved = self.root / 'moved-reports'
        capture = timeline_output.capture_output
        foreign_stage = []
        def swap_parent(path):
            stages = list(parent.glob('.report.jsonl.*.tmp'))
            if stages and not moved.exists():
                name = stages[0].name
                parent.rename(moved)
                parent.mkdir()
                (parent / name).write_bytes(b'foreign staging file')
                foreign_stage.append(parent / name)
                self.output.write_bytes(b'external report')
            return capture(path)
        with patch.object(timeline_output, 'capture_output', swap_parent):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'external report')
        self.assertEqual(foreign_stage[0].read_bytes(), b'foreign staging file')
        self.assertEqual((moved / 'report.jsonl').read_bytes(), b'prior report\n')
        # The owned stage moved with its parent; conservative cleanup leaves it
        # there rather than deleting through a pathname that changed ownership.
        self.assertEqual(len(list(moved.glob('.report.jsonl.*.tmp'))), 1)

    def test_replaced_stage_is_not_published_or_deleted(self):
        for exists in (True, False):
            with self.subTest(exists=exists):
                self.output.write_bytes(b'prior report\n')
                if not exists:
                    self.output.unlink()
                foreign_stage = []
                validate = timeline_output.validate_report_outputs
                calls = 0
                def replaced(inputs, outputs):
                    nonlocal calls
                    validate(inputs, outputs)
                    calls += 1
                    if calls == 2:
                        stage, = self.root.glob('.report.jsonl.*.tmp')
                        replacement = self.root / 'foreign.tmp'
                        replacement.write_bytes(b'foreign stage bytes')
                        os.replace(replacement, stage)
                        foreign_stage.append(stage)
                with patch.object(timeline_output, 'validate_report_outputs', replaced):
                    status, _, error = self.run_main()
                self.assertEqual(status, 2)
                self.assertIn('publication_conflict', error)
                self.assertEqual(self.output.exists(), exists)
                if exists:
                    self.assertEqual(self.output.read_bytes(), b'prior report\n')
                self.assertEqual(foreign_stage[0].read_bytes(), b'foreign stage bytes')
                foreign_stage[0].unlink()

    def test_destination_rechecked_after_final_input_validation(self):
        validate = timeline_output.validate_report_outputs
        calls = 0
        def changed(inputs, outputs):
            nonlocal calls
            validate(inputs, outputs)
            calls += 1
            if calls == 2:
                self.output.write_bytes(b'external during input validation')
        with patch.object(timeline_output, 'validate_report_outputs', changed):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'external during input validation')
        self.assert_clean()

    def test_stage_modified_after_fsync_is_preserved_on_conflict(self):
        validate = timeline_output.validate_report_outputs
        calls = 0
        foreign_stage = []
        def changed(inputs, outputs):
            nonlocal calls
            validate(inputs, outputs)
            calls += 1
            if calls == 2:
                stage, = self.root.glob('.report.jsonl.*.tmp')
                stage.write_bytes(b'external same-inode stage modification')
                foreign_stage.append(stage)
        with patch.object(timeline_output, 'validate_report_outputs', changed):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'prior report\n')
        self.assertEqual(foreign_stage[0].read_bytes(), b'external same-inode stage modification')

    def test_parent_replacement_during_final_input_check_cannot_publish_foreign_stage(self):
        parent = self.root / 'reports'
        parent.mkdir()
        self.output = parent / 'report.jsonl'
        self.output.write_bytes(b'prior report\n')
        moved = self.root / 'moved'
        validate = timeline_output.validate_report_outputs
        calls = 0
        foreign_stage = []
        def changed(inputs, outputs):
            nonlocal calls
            validate(inputs, outputs)
            calls += 1
            if calls == 2:
                stage, = parent.glob('.report.jsonl.*.tmp')
                parent.rename(moved)
                parent.mkdir()
                self.output.write_bytes(b'external report')
                stage.write_bytes(b'foreign stage in replaced parent')
                foreign_stage.append(stage)
        with patch.object(timeline_output, 'validate_report_outputs', changed):
            status, _, error = self.run_main()
        self.assertEqual(status, 2)
        self.assertIn('publication_conflict', error)
        self.assertEqual(self.output.read_bytes(), b'external report')
        self.assertEqual((moved / 'report.jsonl').read_bytes(), b'prior report\n')
        self.assertEqual(foreign_stage[0].read_bytes(), b'foreign stage in replaced parent')
        self.assertEqual(len(list(moved.glob('.report.jsonl.*.tmp'))), 1)

    def test_input_changes_and_new_sibling_abort_publication(self):
        for action in ('change', 'sibling'):
            with self.subTest(action=action):
                def rows(*args, **kwargs):
                    yield {'before': 1}
                    if action == 'change':
                        self.replay.write_bytes(packet(3, 0x9999))
                    else:
                        (self.root / 'match.1.vgr').write_bytes(packet(4, 0x9999))
                with patch.object(event_timeline, 'iter_timeline', rows):
                    status, _, error = self.run_main()
                self.assertEqual(status, 2)
                self.assertIn('input_changed', error)
                self.assertEqual(self.output.read_bytes(), b'prior report\n')
                self.assert_clean()

    def test_bad_paths_and_stage_creation_permission_error(self):
        for output in (self.root, self.root / 'missing' / 'out.jsonl'):
            with self.subTest(output=output):
                self.output = output
                self.assertEqual(self.run_main()[0], 2)
        self.output = self.root / 'report.jsonl'
        with patch.object(timeline_output.tempfile, 'NamedTemporaryFile', side_effect=PermissionError('stage denied')):
            self.assertEqual(self.run_main()[0], 2)
        self.assertEqual(self.output.read_bytes(), b'prior report\n')
        self.assert_clean()

    def test_stdout_retains_streaming_output_and_late_error(self):
        def rows(*args, **kwargs):
            yield {'first': 1}
            raise ValueError('late error')
        with patch.object(event_timeline, 'iter_timeline', rows), patch.object(timeline_output.tempfile, 'NamedTemporaryFile') as staging:
            status, stdout, error = self.run_main(output=False)
        self.assertEqual(status, 2)
        self.assertEqual(stdout, '{"first": 1}\n')
        self.assertIn('late error', error)
        staging.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b'prior report\n')


if __name__ == '__main__':
    unittest.main()
