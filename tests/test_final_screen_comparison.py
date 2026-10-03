import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_stats import anchor, packet, snapshot
from vg.analysis.final_screen_comparison import compare_final_screen, main
from vg.core.stat_evidence import frame_scope


class FinalScreenComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'
        self.image = self.root / 'screen.png'
        self.image.write_bytes(b'independent screenshot bytes')
        self.data = anchor(0, 100) + snapshot(0, (2, 4, 3, 17), entity=7)
        self.data += snapshot(0, (4, 2, 1, 11), entity=8) + packet(10, 1)
        self.replay.write_bytes(self.data)
        self.observation = self.root / 'observation.json'
        self.payload = {
            'schema_version': 'vg.final-screen-observation.v1',
            'replay_scope': frame_scope([(0, self.data)]),
            'screenshot_sha256': hashlib.sha256(self.image.read_bytes()).hexdigest(),
            'capture_stage': 'final_screen',
            'provenance': {'transcription_method': 'manual_visual', 'observed_at_utc': '2026-10-03T07:15:23Z'},
            'screen_side_to_team': {'blue': 'left', 'orange': 'right'},
            'winner_screen_side': 'blue', 'duration_display': '1:49',
            'players': [
                {'entity_id_be': 7, 'screen_side': 'blue', 'kills': 2, 'deaths': 4, 'assists': 3, 'cs': 17, 'gold_display': '1.2k'},
                {'entity_id_be': 8, 'screen_side': 'orange', 'kills': 4, 'deaths': 2, 'assists': 1, 'cs': 11, 'gold_display': '1.3k'},
            ],
        }
        self.parsed = {'teams': {
            'left': [{'name': 'same_name', 'team': 'left', 'entity_id': 1792}],
            'right': [{'name': 'same_name', 'team': 'right', 'entity_id': 2048}],
        }}
        self.parser = patch('vg.analysis.final_screen_comparison.VGRParser')
        self.mock_parser = self.parser.start()
        self.addCleanup(self.parser.stop)
        self.mock_parser.return_value.parse.return_value = self.parsed

    def run_comparison(self, payload=None):
        self.observation.write_text(json.dumps(payload or self.payload), encoding='utf-8')
        return compare_final_screen(str(self.replay), str(self.observation), str(self.image))

    def test_exact_counters_match_by_entity_even_with_duplicate_names(self):
        result = self.run_comparison()
        self.assertEqual(result['comparison_status'], 'matched')
        self.assertEqual(result['matched_fields'], 8)
        self.assertFalse(result['accepted_for_index'])
        self.assertEqual(result['players'][0]['entity_id_be'], 7)
        self.assertEqual(result['observed_winner']['screen_side'], 'blue')
        self.assertEqual(result['observed_winner']['status'], 'observation_only')
        self.assertEqual(result['observed_duration']['display'], '1:49')
        self.assertIsNone(result['observed_duration']['native_seconds'])
        self.assertIsNone(result['players'][0]['gold']['exact_value'])

    def test_changed_source_or_screenshot_is_rejected(self):
        self.replay.write_bytes(self.data + packet(11, 1))
        with self.assertRaisesRegex(ValueError, 'scope'):
            self.run_comparison()
        self.replay.write_bytes(self.data)
        self.image.write_bytes(b'changed screenshot')
        with self.assertRaisesRegex(ValueError, 'screenshot'):
            self.run_comparison()

    def test_section_gap_cannot_be_accepted_with_a_fresh_hash(self):
        tail = anchor(20, 120) + packet(21, 1)
        (self.root / 'match.2.vgr').write_bytes(tail)
        payload = copy.deepcopy(self.payload)
        payload['replay_scope'] = frame_scope([(0, self.data), (2, tail)])
        with self.assertRaisesRegex(ValueError, 'Recording'):
            self.run_comparison(payload)

    def test_duplicate_missing_and_foreign_entities_are_rejected(self):
        for mutation in ('duplicate', 'missing', 'foreign'):
            payload = copy.deepcopy(self.payload)
            if mutation == 'duplicate':
                payload['players'][1]['entity_id_be'] = 7
            elif mutation == 'missing':
                payload['players'].pop()
            else:
                payload['players'][1]['entity_id_be'] = 99
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.run_comparison(payload)

    def test_invalid_counts_and_side_mapping_are_rejected(self):
        for value in (True, -1, 1.5, '2'):
            payload = copy.deepcopy(self.payload)
            payload['players'][0]['kills'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_comparison(payload)
        payload = copy.deepcopy(self.payload)
        payload['players'][0]['screen_side'] = 'orange'
        with self.assertRaisesRegex(ValueError, 'side'):
            self.run_comparison(payload)

    def test_mismatch_is_reported_without_changing_native_values(self):
        payload = copy.deepcopy(self.payload)
        payload['players'][0]['deaths'] = 5
        result = self.run_comparison(payload)
        self.assertEqual(result['comparison_status'], 'mismatch')
        self.assertEqual(result['matched_fields'], 7)
        self.assertEqual(result['players'][0]['fields']['deaths'], {'native': 4, 'observed': 5, 'status': 'mismatch'})

    def test_missing_baseline_is_unavailable_not_zero(self):
        data = anchor(0, 100) + snapshot(0, entity=7) + packet(10, 1)
        self.replay.write_bytes(data)
        payload = copy.deepcopy(self.payload)
        payload['replay_scope'] = frame_scope([(0, data)])
        result = self.run_comparison(payload)
        self.assertEqual(result['comparison_status'], 'unavailable')
        self.assertIsNone(result['players'][1]['fields']['kills']['native'])

    def test_missing_hash_or_provenance_is_rejected(self):
        for key in ('screenshot_sha256', 'replay_scope', 'provenance'):
            payload = copy.deepcopy(self.payload)
            del payload[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_comparison(payload)

    def test_malformed_side_values_and_nonfinal_capture_are_rejected(self):
        for key, value in [('winner_screen_side', []), ('screen_side_to_team', {'blue': None, 'orange': 'right'}), ('capture_stage', 'midgame')]:
            payload = copy.deepcopy(self.payload)
            payload[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_comparison(payload)
        payload = copy.deepcopy(self.payload)
        payload['players'][0]['screen_side'] = []
        with self.assertRaises(ValueError):
            self.run_comparison(payload)

    def test_roster_read_cannot_join_values_from_a_changed_source(self):
        def change_source():
            self.replay.write_bytes(self.data + packet(11, 1))
            return self.parsed
        self.mock_parser.return_value.parse.side_effect = change_source
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.run_comparison()

    def test_invalid_recorded_ids_and_wrong_name_are_rejected(self):
        for value in (True, 0, -1, 1792):
            self.parsed['teams']['right'][0]['entity_id'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_comparison()
        self.parsed['teams']['right'][0]['entity_id'] = 2048
        payload = copy.deepcopy(self.payload)
        payload['players'][0]['name'] = 'foreign name'
        with self.assertRaisesRegex(ValueError, 'name'):
            self.run_comparison(payload)

    def test_cli_preserves_replay_and_evidence_on_output_aliases(self):
        self.run_comparison()
        for target in (self.replay, self.image, self.observation, self.root / 'match.1.vgr'):
            with self.subTest(target=target), patch('sys.stderr'), self.assertRaises(SystemExit) as exc:
                main([str(self.replay), '--observation', str(self.observation), '--screenshot', str(self.image), '-o', str(target)])
            self.assertEqual(exc.exception.code, 2)
        hardlink = self.root / 'alias.json'
        os.link(self.image, hardlink)
        with patch('sys.stderr'), self.assertRaises(SystemExit):
            main([str(self.replay), '--observation', str(self.observation), '--screenshot', str(self.image), '-o', str(hardlink)])
        self.assertEqual(self.replay.read_bytes(), self.data)
        self.assertEqual(self.image.read_bytes(), b'independent screenshot bytes')

    def test_cli_writes_report_but_returns_failure_on_counter_mismatch(self):
        payload = copy.deepcopy(self.payload)
        payload['players'][0]['kills'] = 20
        self.run_comparison(payload)
        target = self.root / 'report.json'
        with patch('sys.stdout'):
            code = main([str(self.replay), '--observation', str(self.observation), '--screenshot', str(self.image), '-o', str(target)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(target.read_text())['comparison_status'], 'mismatch')


if __name__ == '__main__':
    unittest.main()
