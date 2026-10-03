import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_native_stats import anchor, packet, snapshot
from vg.analysis.final_screen_comparison import compare_final_screen
from vg.core.stat_evidence import frame_scope


class ProductFinalScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'sample.0.vgr'
        self.screenshot = self.root / 'screen.png'
        self.observation = self.root / 'observation.json'
        self.output = self.root / 'report.json'
        self.screenshot.write_bytes(b'synthetic screenshot bytes; not visual proof')
        self.data = anchor(0, 100)
        for name, entity, team, values in (
            ('PlayerOne', 7, 1, (2, 4, 3, 17)),
            ('PlayerTwo', 8, 2, (4, 2, 1, 11)),
        ):
            block = bytearray(0xE2)
            block[:3] = b'\xda\x03\xee'
            block[3:3 + len(name)] = name.encode('ascii')
            block[0xA5:0xA7] = entity.to_bytes(2, 'big')
            block[0xA9:0xAB] = (0xB801).to_bytes(2, 'little')
            block[0xD5] = team
            self.data += packet(0, 1, block) + snapshot(0, values, entity=entity)
        self.data += packet(10, 1)
        self.replay.write_bytes(self.data)
        self.payload = {
            'schema_version': 'vg.final-screen-observation.v1',
            'capture_stage': 'final_screen',
            'replay_scope': frame_scope([(0, self.data)]),
            'screenshot_sha256': hashlib.sha256(self.screenshot.read_bytes()).hexdigest(),
            'provenance': {'transcription_method': 'manual_visual', 'observed_at_utc': '2026-10-03T07:15:23Z'},
            'screen_side_to_team': {'blue': 'left', 'orange': 'right'},
            'winner_screen_side': 'blue', 'duration_display': '1:49',
            'result_display': 'Victory',
            'players': [
                {'entity_id_be': 7, 'name': 'PlayerOne', 'screen_side': 'blue',
                 'kills': 2, 'deaths': 4, 'assists': 3, 'cs': 17, 'gold_display': '1.2k'},
                {'entity_id_be': 8, 'name': 'PlayerTwo', 'screen_side': 'orange',
                 'kills': 4, 'deaths': 2, 'assists': 1, 'cs': 11, 'gold_display': '1.3k'},
            ],
        }
        self.observation.write_text(json.dumps(self.payload))

    def input_hashes(self):
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (self.replay, self.screenshot, self.observation)}

    def cli(self):
        return subprocess.run(
            [sys.executable, '-B', '-m', 'vg.analysis.final_screen_comparison',
             str(self.replay), '--observation', str(self.observation),
             '--screenshot', str(self.screenshot), '-o', str(self.output)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
            check=False,
        )

    def assert_narrow_scope(self, result):
        self.assertEqual(result['compared_field_names'], ['kills', 'deaths', 'assists', 'minion_kills'])
        self.assertEqual(result['observation_only_fields'], ['gold', 'winner', 'duration', 'result'])
        self.assertIsInstance(result['comparison_scope'], str)
        self.assertTrue(result['comparison_scope'])
        self.assertEqual(result['scope'], 'recording_specific_final_screen')
        self.assertFalse(result['accepted_for_index'])
        self.assertEqual(result['replay_scope'], self.payload['replay_scope'])
        self.assertEqual(result['screenshot_sha256'], self.payload['screenshot_sha256'])
        for key in ('observed_duration', 'observed_winner', 'observed_result'):
            self.assertEqual(result[key]['status'], 'observation_only')
        self.assertIsNone(result['observed_duration']['native_seconds'])
        for player in result['players']:
            self.assertIsNone(player['gold']['exact_value'])
            self.assertEqual(player['gold']['status'], 'observation_only')

    def test_final_scope_happy_api_names_exact_counter_scope(self):
        # Given actual generated replay, observation and hash-bound image files.
        before = self.input_hashes()
        # When comparing through the public API without parser mocks.
        result = compare_final_screen(str(self.replay), str(self.observation), str(self.screenshot))
        # Then only the eight supplied counters match with explicit limitations.
        self.assertEqual(result['comparison_status'], 'matched')
        self.assertEqual((result['matched_fields'], result['compared_fields']), (8, 8))
        self.assert_narrow_scope(result)
        self.assertEqual(self.input_hashes(), before)

    def test_final_scope_happy_cli_publishes_narrow_match(self):
        # Given the same complete generated roster and independent observation.
        before = self.input_hashes()
        # When invoking the real module CLI in a fresh subprocess.
        completed = self.cli()
        # Then exit zero publishes a scoped match without modifying inputs.
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(self.output.read_text())
        self.assertEqual(result['comparison_status'], 'matched')
        self.assert_narrow_scope(result)
        self.assertEqual(self.input_hashes(), before)

    def test_final_scope_failure_counter_mismatch_exits_one(self):
        # Given one independently supplied counter that differs from the replay.
        self.payload['players'][0]['kills'] = 99
        self.observation.write_text(json.dumps(self.payload))
        before = self.input_hashes()
        # When invoking the real CLI.
        completed = self.cli()
        # Then mismatch is published with exit one and unchanged native values.
        self.assertEqual(completed.returncode, 1, completed.stderr)
        result = json.loads(self.output.read_text())
        self.assertEqual(result['comparison_status'], 'mismatch')
        self.assertEqual(result['matched_fields'], 7)
        self.assertEqual(result['players'][0]['fields']['kills']['native'], 2)
        self.assert_narrow_scope(result)
        self.assertEqual(self.input_hashes(), before)

    def test_final_scope_failure_invalid_hashes_preserve_prior_report(self):
        # Given either a mismatched screenshot or replay hash and a prior report.
        for key in ('screenshot_sha256', 'replay_scope'):
            with self.subTest(key=key):
                payload = dict(self.payload)
                payload[key] = ('sha256:' if key == 'replay_scope' else '') + '0' * 64
                self.observation.write_text(json.dumps(payload))
                self.output.write_bytes(b'prior report')
                before = self.input_hashes()
                # When the public CLI validates those supplied inputs.
                completed = self.cli()
                # Then exit two leaves inputs and the prior report intact.
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertNotIn('Traceback', completed.stderr)
                self.assertEqual(self.output.read_bytes(), b'prior report')
                self.assertEqual(self.input_hashes(), before)

    def test_final_scope_failure_empty_observed_or_recorded_roster(self):
        # Given an empty observed roster, then an empty actual recorded roster.
        for empty_observed in (True, False):
            with self.subTest(empty_observed=empty_observed):
                payload = dict(self.payload)
                if empty_observed:
                    payload['players'] = []
                else:
                    data = anchor(0, 100) + packet(10, 1)
                    self.replay.write_bytes(data)
                    payload['replay_scope'] = frame_scope([(0, data)])
                self.observation.write_text(json.dumps(payload))
                before = self.input_hashes()
                # When calling the actual CLI with incomplete roster evidence.
                completed = self.cli()
                # Then the comparison is rejected before publishing a match.
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertFalse(self.output.exists())
                self.assertEqual(self.input_hashes(), before)


if __name__ == '__main__':
    unittest.main()
