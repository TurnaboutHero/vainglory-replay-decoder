import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_inventory import anchor, grant, packet
from tests.test_player_state_service import recording
from vg.decoder_v2 import decode_match


class PlayerStateCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'
        self.data = recording() + grant(2) + packet(10, 0xffff)
        self.replay.write_bytes(self.data)
        self.output = self.root / 'report.json'

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-m', 'vg.decoder_v2.decode_match',
                               *map(str, args)], capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parents[1], timeout=30)

    def test_default_cli_exposes_state_and_explicit_capture_uses_common_time(self):
        end = self.cli(self.replay)
        self.assertEqual(end.returncode, 0, end.stderr)
        payload = json.loads(end.stdout)
        self.assertEqual(payload['schema_version'], 'decoder_v2.player_state.v3')
        self.assertEqual(payload['scope'], 'recorded_end')
        self.assertEqual(payload['support_status'], 'supported')
        self.assertEqual(payload['players'][0]['minion_kills'], 4)
        self.assertEqual(payload['players'][0]['gold_balance'], 25.5)
        self.assertEqual(payload['players'][0]['net_worth'], 100.5)
        self.assertEqual(len(payload['players'][0]['items']), 1)
        capture = self.cli(self.replay, '--at-game-time', '101', '--format', 'state-json')
        self.assertEqual(capture.returncode, 0, capture.stderr)
        state = json.loads(capture.stdout)
        self.assertEqual((state['scope'], state['requested_game_time'], state['as_of_game_time']), ('capture', 101, 100))
        self.assertEqual(state['players'][0]['items'], [])
        self.assertEqual(state['replay_scope'], payload['replay_scope'])
        self.assertEqual(self.replay.read_bytes(), self.data)

    def test_explicit_safe_debug_and_python_decode_match_keep_old_contracts(self):
        safe = decode_match.decode_match(str(self.replay))
        self.assertEqual(safe.schema_version, 'decoder_v2.match.v2')
        self.assertIsNone(safe.players[0].kills)
        self.assertIsNone(safe.players[0].gold)
        for format_name, schema in (('safe-json', 'decoder_v2.match.v2'), ('debug-json', 'decoder_v2.debug_match.v2')):
            with self.subTest(format=format_name):
                process = self.cli(self.replay, '--format', format_name)
                self.assertEqual(process.returncode, 0, process.stderr)
                payload = json.loads(process.stdout)
                self.assertEqual(payload['schema_version'], schema)
                value = payload if format_name == 'safe-json' else payload['safe_output']
                self.assertFalse(value['withheld_fields']['gold']['accepted_for_index'])
                self.assertIsNone(value['players'][0]['gold'])

    def test_output_direct_sibling_hardlink_and_symlink_collisions_are_rejected(self):
        sibling = self.root / 'match.1.vgr'
        sibling.write_bytes(packet(11, 0xffff))
        hard = self.root / 'hard.json'
        os.link(self.replay, hard)
        symbolic = self.root / 'symbolic.json'
        symbolic.symlink_to(sibling)
        for output in (self.replay, sibling, hard, symbolic, self.root / 'match.2.vgr'):
            with self.subTest(output=output), patch.object(decode_match, 'decode_player_state') as decode, \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                decode_match.main([str(self.replay), '-o', str(output)])
            self.assertEqual(error.exception.code, 2)
            decode.assert_not_called()
        self.assertEqual(self.replay.read_bytes(), self.data)
        self.assertFalse((self.root / 'match.2.vgr').exists())

    def test_regular_output_and_source_hashes_are_returned(self):
        result = self.cli(self.replay, '-o', self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(self.output.read_text())
        self.assertEqual(payload['schema_version'], 'decoder_v2.player_state.v3')
        self.assertEqual(payload['source_files'][0]['section'], 0)
        self.assertEqual(len(payload['source_files'][0]['sha256']), 64)
        self.assertEqual(payload['record_boundary']['section'], 0)
        self.assertEqual(self.replay.read_bytes(), self.data)

    def test_default_cli_selects_one_nested_family(self):
        nested = self.root / 'nested'
        nested.mkdir()
        moved = nested / self.replay.name
        self.replay.rename(moved)
        result = self.cli(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['schema_version'], 'decoder_v2.player_state.v3')
        self.assertEqual(payload['replay_file'], str(moved))
        self.assertEqual(payload['support_status'], 'supported')
        self.assertEqual(payload['players'][0]['name'], 'Same')

    def test_source_changed_after_service_return_cannot_publish(self):
        self.output.write_text('previous result')
        decode = decode_match.decode_player_state

        def mutate(*args, **kwargs):
            result = decode(*args, **kwargs)
            self.replay.write_bytes(self.data + packet(11, 0xffff))
            return result

        with patch.object(decode_match, 'decode_player_state', side_effect=mutate), \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            decode_match.main([str(self.replay), '-o', str(self.output)])
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.output.read_text(), 'previous result')

    def test_unknown_items_are_null_in_cli_and_real_zero_stays_zero(self):
        self.replay.write_bytes(recording(counters=(0, 0, 0, 0), gold=(0, 0)) + grant(definition=99999))
        result = self.cli(self.replay)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['support_status'], 'partial')
        self.assertIsNone(payload['players'][0]['items'])
        self.assertEqual(payload['players'][0]['minion_kills'], 0)
        self.assertEqual(payload['players'][0]['gold_balance'], 0)
        self.assertEqual(payload['players'][0]['field_status']['items']['status'], 'unsupported_state')

    def test_help_invalid_time_and_missing_input_have_real_cli_contracts(self):
        help_result = self.cli('--help')
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn('state-json', help_result.stdout)
        for arguments in ((self.root / 'missing.0.vgr',), (self.replay, '--at-game-time', 'nan'),
                          (self.replay, '--at-game-time', '-1')):
            with self.subTest(arguments=arguments):
                result = self.cli(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(result.stderr)

    def test_out_of_coverage_is_explicit_and_never_zero_filled(self):
        result = self.cli(self.replay, '--at-game-time', '99')
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['support_status'], 'out_of_coverage')
        self.assertEqual(payload['players'], [])
        self.assertEqual(payload['field_status']['items']['status'], 'out_of_coverage')

    def test_literal_glob_family_sources_and_future_sections_are_protected(self):
        replay = self.root / '[match].0.vgr'
        replay.write_bytes(recording())
        sibling = self.root / '[match].1.vgr'
        sibling.write_bytes(anchor(1, 101) + grant(2))
        good = self.cli(replay)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(len(json.loads(good.stdout)['source_files']), 2)
        before = (replay.read_bytes(), sibling.read_bytes())
        for output in (sibling, self.root / '[match].2.vgr'):
            with self.subTest(output=output):
                result = self.cli(replay, '-o', output)
                self.assertEqual(result.returncode, 2)
        self.assertEqual((replay.read_bytes(), sibling.read_bytes()), before)
        self.assertFalse((self.root / '[match].2.vgr').exists())

    def test_literal_glob_family_added_after_service_return_cannot_publish(self):
        replay = self.root / '[match].0.vgr'
        replay.write_bytes(recording())
        self.output.write_text('previous result')
        decode = decode_match.decode_player_state

        def add_section(*args, **kwargs):
            result = decode(*args, **kwargs)
            (self.root / '[match].1.vgr').write_bytes(anchor(1, 101) + packet(2, 0xffff))
            return result

        with patch.object(decode_match, 'decode_player_state', side_effect=add_section), \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            decode_match.main([str(replay), '-o', str(self.output)])
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.output.read_text(), 'previous result')


if __name__ == '__main__':
    unittest.main()
