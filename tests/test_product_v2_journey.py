import contextlib
from dataclasses import replace
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

from tests.test_native_stats import anchor, packet
from tests.test_product_duration_provenance import replay_bytes
from vg.core.stat_evidence import frame_scope
from vg.core.replay_input import ReplayInputError
from vg.core import replay_output
from vg.core.vgr_records import iter_records
from vg.decoder_v2 import batch_decode, decode_match, index_export
from vg.decoder_v2.kda import decode_kda_from_replay


class ProductV2JourneyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replays = self.root / 'replays'
        self.replays.mkdir()
        self.replay = self.replays / 'sample.0.vgr'
        self.data = replay_bytes(crystal=120, death=110)
        self.replay.write_bytes(self.data)
        self.output = self.root / 'report.json'

    def run_cli(self, module, *arguments):
        return subprocess.run([sys.executable, '-B', '-m', f'vg.decoder_v2.{module}',
                               *map(str, arguments)], capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parents[1], timeout=30, check=False)

    def hashes(self):
        return {path.relative_to(self.replays).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.replays.rglob('*.vgr')}

    def test_v2_journey_happy_safe_and_debug_capture(self):
        # Given a real framed recording with known player identity and native counters.
        before = self.hashes()
        for format_name in ('safe-json', 'debug-json'):
            with self.subTest(format=format_name):
                # When its public CLI captures at game time 105.
                completed = self.run_cli('decode_match', self.replay, '--format', format_name,
                                         '--at-game-time', 105)
                # Then source, native game time, roster and final withholding remain explicit.
                self.assertEqual(completed.returncode, 0, completed.stderr)
                payload = json.loads(completed.stdout)
                result = payload['safe_output'] if format_name == 'debug-json' else payload
                self.assertEqual(result['schema_version'], 'decoder_v2.capture.v2')
                self.assertEqual(result['replay_scope'], frame_scope([(0, self.data)]))
                self.assertEqual((result['at_game_time'], result['as_of_game_time']), (105, 105))
                self.assertEqual(result['players'][0]['entity_id_be'], 7)
                self.assertEqual(result['players'][0]['kills'], 6)
                self.assertFalse(result['accepted_fields']['kills']['accepted_for_index'])
                for key in ('winner', 'gold', 'duration_seconds'):
                    self.assertIsNone(result['withheld_fields'][key]['value'])
                    self.assertFalse(result['withheld_fields'][key]['accepted_for_index'])
                self.assertEqual(self.hashes(), before)

    def test_v2_journey_happy_final_index_retains_duration_decision(self):
        # Given a crystal candidate that estimates duration but proves no final statistics.
        for number in range(1, 20):
            timestamp = 120 + 10 * number
            (self.replays / f'sample.{number}.vgr').write_bytes(
                anchor(timestamp, 100 + timestamp) + packet(timestamp + 1, 1))
        before = self.hashes()
        # When publishing through the actual index CLI.
        completed = self.run_cli('index_export', self.replays, '-o', self.output)
        # Then duration stays a match-only withheld estimate with source reason.
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(self.output.read_text())
        self.assertEqual((report['status'], report['discovered'], report['succeeded'], report['failed']),
                         ('complete', 1, 1, 0))
        match = report['matches'][0]
        duration = match['withheld_fields']['duration_seconds']
        self.assertEqual(duration['value'], 120)
        self.assertIn('crystal', duration['reason'])
        self.assertFalse(duration['accepted_for_index'])
        self.assertNotIn('duration_seconds', match['players'][0]['withheld_fields'])
        for key in ('kills', 'deaths', 'assists', 'gold', 'minion_kills', 'winner'):
            self.assertFalse(match['withheld_fields'][key]['accepted_for_index'])
            self.assertIsNone(match['withheld_fields'][key]['value'])
        self.assertEqual(self.hashes(), before)

    def test_v2_journey_happy_empty_tree_is_explicit(self):
        # Given an existing empty root.
        empty = self.root / 'empty'
        empty.mkdir()
        for module in ('batch_decode', 'index_export'):
            with self.subTest(module=module):
                # When requesting its report without an output path.
                completed = self.run_cli(module, empty)
                # Then an intentional empty dataset is successful and accounted for.
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(completed.stdout)
                self.assertEqual(report['status'], 'empty')
                self.assertEqual((report['discovered'], report['succeeded'], report['failed']), (0, 0, 0))
                self.assertEqual(report['results'], [])

    def test_v2_journey_happy_nested_directory_selection(self):
        # Given one nested replay and excluded macOS metadata beside it.
        nested = self.replays / 'nested'
        nested.mkdir()
        self.replay.rename(nested / self.replay.name)
        metadata = self.replays / '__MACOSX'
        metadata.mkdir()
        (metadata / '._sample.0.vgr').write_bytes(b'metadata')
        before = self.hashes()
        # When the safe CLI selects a directory without an explicit output path.
        completed = self.run_cli('decode_match', self.replays, '--format', 'safe-json', '--at-game-time', 105)
        # Then the one real family determines the capture and source path.
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result['replay_file'], str(nested / self.replay.name))
        self.assertEqual(result['players'][0]['kills'], 6)
        self.assertEqual(self.hashes(), before)

    def test_v2_journey_happy_partial_batch_and_index_preserve_ordered_ids(self):
        # Given same-name recordings in different directories and one malformed family.
        self.replay.unlink()
        for folder, data in (('a', self.data), ('b', self.data), ('z', b'malformed')):
            directory = self.replays / folder
            directory.mkdir()
            (directory / 'sample.0.vgr').write_bytes(data)
        before = self.hashes()
        for module in ('batch_decode', 'index_export'):
            with self.subTest(module=module):
                # When the CLI publishes all discovered outcomes.
                completed = self.run_cli(module, self.replays, '-o', self.output)
                # Then a partial receipt retains both successes and the precise failed input.
                self.assertEqual(completed.returncode, 1, completed.stderr)
                report = json.loads(self.output.read_text())
                self.assertEqual((report['status'], report['discovered'], report['succeeded'], report['failed']),
                                 ('partial', 3, 2, 1))
                self.assertEqual([row['input_id'] for row in report['results']],
                                 ['a/sample.0.vgr', 'b/sample.0.vgr', 'z/sample.0.vgr'])
                self.assertEqual([row['input_id'] for row in report['matches']],
                                 ['a/sample.0.vgr', 'b/sample.0.vgr'])
                self.assertEqual(report['results'][-1]['error_code'], 'replay_malformed')
                self.assertEqual(self.hashes(), before)

    def test_v2_journey_failure_missing_and_file_roots(self):
        # Given a missing directory or a file where a root directory is required.
        for module in ('batch_decode', 'index_export'):
            for path, code in ((self.root / 'missing', 'input_missing'), (self.replay, 'input_not_directory')):
                with self.subTest(module=module, path=path):
                    # When requesting stdout output, which must still validate inputs.
                    completed = self.run_cli(module, path)
                    # Then invalid global input exits two without a success payload or traceback.
                    self.assertEqual(completed.returncode, 2)
                    self.assertIn(code, completed.stderr)
                    self.assertNotIn('Traceback', completed.stderr)
                    self.assertEqual(completed.stdout, '')

    def test_v2_journey_failure_ambiguous_directory_and_sibling_selection(self):
        # Given two families and an explicitly selected nonzero section.
        second = self.replays / 'other.0.vgr'
        second.write_bytes(self.data)
        sibling = self.replays / 'sample.1.vgr'
        sibling.write_bytes(anchor(121, 221) + packet(131, 1))
        for path, expected in ((self.replays, 'replay_ambiguous'), (sibling, 'replay_malformed')):
            with self.subTest(path=path):
                # When either public API or CLI receives an invalid selection.
                with self.assertRaises(ReplayInputError) as error:
                    decode_match.decode_match(str(path))
                completed = self.run_cli('decode_match', path)
                # Then neither boundary guesses a different replay.
                self.assertEqual(error.exception.code, expected)
                self.assertEqual(completed.returncode, 2)
                self.assertIn(expected, completed.stderr)

    def test_v2_journey_failure_malformed_single_and_all_failed_batch(self):
        # Given a malformed explicit replay and a prior report.
        self.replay.write_bytes(b'malformed')
        self.output.write_bytes(b'previous report')
        # When decoding the single input then publishing its batch outcome.
        single = self.run_cli('decode_match', self.replay, '-o', self.output)
        self.assertEqual(single.returncode, 2)
        self.assertNotIn('Traceback', single.stderr)
        self.assertEqual(self.output.read_bytes(), b'previous report')
        batch = self.run_cli('batch_decode', self.replays)
        # Then batch reports one explicit failed input and no successful match.
        self.assertEqual(batch.returncode, 1)
        report = json.loads(batch.stdout)
        self.assertEqual((report['status'], report['discovered'], report['succeeded'], report['failed']),
                         ('failed', 1, 0, 1))
        self.assertEqual(report['matches'], [])

    def test_v2_journey_failure_specific_capture_causes(self):
        # Given native coverage, baseline, clock, identity and recording failures.
        no_baseline = b''.join(packet(r.timestamp, r.opcode, r.payload)
                               for r in iter_records(self.data) if r.opcode != 0x03F3)
        bad_identity = bytearray(self.data)
        offset = bad_identity.find(b'\xda\x03\xee') + 0xA5
        bad_identity[offset:offset + 2] = b'\0\0'
        cases = [('coverage', self.data, 9999, 'out_of_coverage'),
                 ('baseline', no_baseline, 105, 'missing_baseline'),
                 ('identity', bytes(bad_identity), 105, 'Player IDs'),
                 ('clock', self.data, 105, None),
                 ('gap', self.data, 105, None)]
        for name, data, cutoff, expected in cases:
            with self.subTest(cause=name):
                for number in (1, 2):
                    (self.replays / f'sample.{number}.vgr').unlink(missing_ok=True)
                self.replay.write_bytes(data)
                extra = None
                if name in ('clock', 'gap'):
                    extra = self.replays / f'sample.{1 if name == "clock" else 2}.vgr'
                    extra.write_bytes(anchor(121, 1 if name == 'clock' else 221) + packet(131, 1))
                # When safe and debug CLI output describes the rejected capture.
                completed = self.run_cli('decode_match', self.replay, '--format', 'debug-json',
                                         '--at-game-time', cutoff)
                # Then safe fields preserve a specific rejection and remain unaccepted.
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(completed.stdout)
                reason = report['safe_output']['withheld_fields']['kills']['reason']
                if expected is not None:
                    self.assertIn(expected.lower(), reason.lower())
                elif name == 'clock':
                    self.assertEqual(reason, report['safe_output']['evidence']['native_clock']['reason'])
                else:
                    self.assertEqual(reason, report['safe_output']['evidence']['recording_reason'])
                if name in ('coverage', 'baseline'):
                    self.assertEqual(reason, report['kda_debug']['reason'])
                self.assertIsNone(report['safe_output']['players'][0]['kills'])
                if extra is not None:
                    extra.unlink()

    def test_v2_journey_failure_capture_scope_mismatch(self):
        # Given otherwise accepted real native capture with a foreign content scope.
        capture = decode_kda_from_replay(str(self.replay), at_game_time=105)
        self.assertTrue(capture.accepted)
        foreign = replace(capture, replay_scope='sha256:' + '0' * 64)
        # When only the native result seam returns that conflicting scope.
        with patch('vg.decoder_v2.decode_match.decode_kda_from_replay', return_value=foreign):
            result = decode_match.decode_match(str(self.replay), at_game_time=105)
        # Then the public API names the mismatch without adopting foreign values.
        self.assertIn('scope', result.withheld_fields['kills'].reason)
        self.assertFalse(result.withheld_fields['kills'].accepted_for_index)
        self.assertIsNone(result.players[0].kills)

    def test_v2_journey_failure_publication_preserves_prior_bytes(self):
        # Given an existing report and a failing replace operation.
        before = self.hashes()
        for module in (batch_decode, index_export):
            with self.subTest(module=module.__name__):
                self.output.write_bytes(b'previous report')
                # When the actual API/decoder runs and only publication fails.
                with patch('vg.core.replay_output.os.replace', side_effect=OSError('replace failed')), \
                     contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    code = module.main([str(self.replays), '-o', str(self.output)])
                # Then exit two preserves source/report bytes and removes staging files.
                self.assertEqual(code, 2)
                self.assertEqual(self.output.read_bytes(), b'previous report')
                self.assertEqual(self.hashes(), before)
                self.assertEqual(list(self.root.glob('.report.json.*.tmp')), [])

    def test_v2_journey_failure_correction_aliases_and_late_alias(self):
        # Given a supplied correction file, which remains untrusted and withheld.
        correction = self.root / 'correction.json'
        correction.write_text('{"players": []}')
        original = correction.read_bytes()
        for target in (correction, self.output):
            with self.subTest(target=target):
                if target == self.output:
                    os.link(correction, target)
                # When the actual index CLI targets the correction or its hard link.
                completed = self.run_cli('index_export', self.replays, '--kda-correction-path', correction,
                                         '-o', target)
                # Then neither input can be replaced by an index report.
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(correction.read_bytes(), original)
                if target == self.output:
                    target.unlink()
        build = index_export.build_index_ready_export

        def create_alias(*args, **kwargs):
            result = build(*args, **kwargs)
            self.output.symlink_to(correction)
            return result

        with patch.object(index_export, 'build_index_ready_export', side_effect=create_alias), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = index_export.main([str(self.replays), '--kda-correction-path', str(correction),
                                      '-o', str(self.output)])
        self.assertEqual(code, 2)
        self.assertEqual(correction.read_bytes(), original)

    def test_v2_journey_failure_input_changed_after_preflight(self):
        # Given a real decode that completes before its source changes.
        self.output.write_bytes(b'previous report')
        decode = decode_match.decode_match

        def change_source(*args, **kwargs):
            result = decode(*args, **kwargs)
            self.replay.write_bytes(self.data + packet(121, 1))
            return result

        # When publication reuses the original predecode input snapshot.
        with patch.object(decode_match, 'decode_match', side_effect=change_source), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
             self.assertRaises(SystemExit) as error:
            decode_match.main([str(self.replay), '--format', 'safe-json', '-o', str(self.output)])
        # Then source changes invalidate publication instead of silently rebinding it.
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.output.read_bytes(), b'previous report')

    def test_v2_journey_failure_unreadable_family_is_counted(self):
        # Given one readable family and another whose section cannot be read.
        blocked = self.replays / 'blocked.0.vgr'
        blocked.write_bytes(self.data)
        original_identity = replay_output.file_identity

        def read_identity(path):
            if path == blocked:
                raise PermissionError(13, 'read denied', str(path))
            return original_identity(path)

        before = self.hashes()
        for module in (batch_decode, index_export):
            with self.subTest(module=module.__name__):
                # When the real CLI entrypoint receives a deterministic file-read failure.
                with patch.object(replay_output, 'file_identity', side_effect=read_identity), \
                     contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    code = module.main([str(self.replays), '-o', str(self.output)])
                # Then one failed input is retained alongside the successful family.
                self.assertEqual(code, 1)
                report = json.loads(self.output.read_text())
                self.assertEqual((report['status'], report['discovered'], report['succeeded'], report['failed']),
                                 ('partial', 2, 1, 1))
                self.assertEqual(report['results'][0]['input_id'], 'blocked.0.vgr')
                self.assertEqual(report['results'][0]['error_code'], 'input_unreadable')
                self.assertEqual(report['matches'][0]['input_id'], 'sample.0.vgr')
                self.assertEqual(self.hashes(), before)

    def test_v2_journey_failure_reserved_sources_reject_stage_time_aliases(self):
        # Given unreadable reserved paths and an otherwise usable report destination.
        blocked = self.replays / 'blocked.0.vgr'
        blocked.write_bytes(self.data)
        original_identity = replay_output.file_identity
        stage = replay_output.stage_payload

        def read_identity(path):
            if path == blocked:
                raise PermissionError(13, 'read denied', str(path))
            return original_identity(path)

        def stage_and_alias(*args, **kwargs):
            temporary = stage(*args, **kwargs)
            self.output.symlink_to(blocked)
            return temporary

        before = self.hashes()
        # When reserved paths are checked without claiming their content was read.
        with patch.object(replay_output, 'file_identity', side_effect=read_identity):
            with self.assertRaises(replay_output.ReplayOutputError) as error:
                replay_output.ReportInputs(files=(blocked,))
            self.assertEqual(error.exception.code, 'input_unreadable')
            reserved = replay_output.ReportInputs(reserved_files=(blocked,), reserved_replays=(blocked,))
            self.assertIn(blocked, reserved.sources())
            self.assertEqual(reserved.identities, ())
            for output in (blocked, self.replays / 'blocked.999.vgr'):
                with self.subTest(output=output), self.assertRaises(replay_output.ReplayOutputError):
                    replay_output.write_report_output(reserved, output, 'report')
            with patch.object(replay_output, 'stage_payload', side_effect=stage_and_alias), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = batch_decode.main([str(self.replays), '-o', str(self.output)])
        # Then preflight and post-stage aliases cannot overwrite unreadable inputs.
        self.assertEqual(code, 2)
        self.assertEqual(self.hashes(), before)
        self.assertEqual(list(self.root.glob('.report.json.*.tmp')), [])
        self.assertTrue(self.output.is_symlink())


if __name__ == '__main__':
    unittest.main()
