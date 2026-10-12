import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_player_state_service import recording
from vg.analysis.batch_statistics import generate_report
from vg.core.analysis_eligibility import evaluate_definitive_analysis, partition_definitive_analysis
from vg.core.unified_decoder import UnifiedDecoder
from vg.decoder_v2.player_state import RecordingClient, decode_player_state


class AnalysisEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        self.replay = self.inputs / 'sample.0.vgr'
        self.replay.write_bytes(recording(counters=(0, 0, 0, 0), gold=(0.0, 0.0)))
        self.before = hashlib.sha256(self.replay.read_bytes()).hexdigest()

    def assert_excluded(self, decision):
        self.assertIs(decision['eligible'], False)
        self.assertEqual(decision['status'], 'excluded')
        self.assertIn('recording_source_unverified', decision['reason_codes'])
        self.assertIn('final_result_unverified', decision['reason_codes'])
        self.assertTrue(decision['reason'])

    def cli(self, module, *args):
        process = subprocess.run([sys.executable, '-B', '-m', module, *map(str, args)],
                                 capture_output=True, text=True,
                                 cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(hashlib.sha256(self.replay.read_bytes()).hexdigest(), self.before)
        return process

    def test_missing_unknown_and_declared_verified_metadata_all_fail_closed(self):
        for client in (None, {}, {'status': 'unverified'}, {'status': 'verified'},
                       {'status': 'verified', 'sha256': 'a' * 64, 'source': 'local'}):
            with self.subTest(client=client):
                payload = {'recording_client': client, 'support_status': 'supported',
                           'supported_client_sha256': 'a' * 64,
                           'final_validation_status': 'verified', 'data_complete': True,
                           'winner': 'left', 'truth_source': 'truth.json',
                           'definitive_analysis': {'eligible': True}}
                self.assert_excluded(evaluate_definitive_analysis(payload))
                partition = partition_definitive_analysis([payload])
                self.assertEqual(partition['included_matches'], 0)
                self.assertEqual(partition['matches'], [])
                self.assertEqual(partition['excluded_matches'], 1)

    def test_different_build_is_distinct_from_unknown_build(self):
        state = decode_player_state(self.replay)
        for status in ('incompatible', 'mismatch', 'unsupported_version'):
            with self.subTest(status=status):
                changed = replace(state, recording_client=RecordingClient(status, 'different recording build'))
                self.assert_excluded(changed.definitive_analysis)
                self.assertIn('recording_version_mismatch', changed.definitive_analysis['reason_codes'])
                self.assertNotIn('recording_version_unverified', changed.definitive_analysis['reason_codes'])
        self.assertIn('recording_version_unverified', state.definitive_analysis['reason_codes'])

    def test_supported_state_and_legacy_api_preserve_measured_zero_and_unknowns(self):
        state = decode_player_state(self.replay)
        self.assertEqual(state.support_status, 'supported')
        self.assert_excluded(state.definitive_analysis)
        self.assertEqual(state.to_dict()['players'][0]['kills'], 0)
        match = UnifiedDecoder(str(self.replay)).decode()
        self.assert_excluded(match.definitive_analysis)
        self.assertEqual(match.all_players[0].kills, 0)
        self.assertIsNone(match.winner)
        self.assertIsNone(match.all_players[0].gold_earned)
        self.assertEqual(json.loads(match.to_json())['definitive_analysis'], state.to_dict()['definitive_analysis'])

    def test_capture_is_excluded_even_with_supported_fields(self):
        state = decode_player_state(self.replay, at_game_time=100)
        self.assertEqual(state.scope, 'capture')
        self.assert_excluded(state.to_dict()['definitive_analysis'])

    def test_observed_statistics_and_definitive_statistics_have_separate_denominators(self):
        matches = [UnifiedDecoder(str(self.replay)).decode() for _ in range(2)]
        matches[1].final_validation_status = 'verified'
        matches[1].winner = 'left'
        report = generate_report(matches)
        self.assertEqual(report['match_stats']['total_matches'], 2)
        self.assertEqual(report['match_stats']['total_kills'], 0)
        definitive = report['definitive_analysis']
        self.assertEqual((definitive['included_matches'], definitive['excluded_matches']), (0, 2))
        self.assertEqual(definitive['matches'], [])
        stats = definitive['statistics']['match_stats']
        self.assertEqual(stats['total_matches'], 0)
        self.assertIsNone(stats['total_kills'])
        self.assertIsNone(stats['avg_duration_s'])
        self.assertEqual(definitive['statistics']['hero_stats'], [])

    def test_supplied_truth_does_not_authorize_definitive_analysis(self):
        truth = self.root / 'truth.json'
        truth.write_text(json.dumps({'matches': [{'replay_file': str(self.replay),
                         'match_info': {'duration_seconds': 0}, 'players': {}}]}))
        match = UnifiedDecoder(str(self.replay)).decode_with_truth(str(truth))
        self.assertEqual(match.duration_provenance['status'], 'supplied_truth')
        self.assertEqual(match.duration_seconds, 0)
        self.assert_excluded(match.to_dict()['definitive_analysis'])

    def test_single_default_safe_and_legacy_cli_exports_exclusion(self):
        for mode in ('state-json', 'safe-json'):
            output = self.root / (mode + '.json')
            self.cli('vg.decoder_v2.decode_match', self.replay, '--format', mode, '-o', output)
            payload = json.loads(output.read_text())
            self.assert_excluded(payload['definitive_analysis'])
            self.assertTrue(payload['players'])
        output = self.root / 'legacy.json'
        self.cli('vg.core.export_matches', self.replay, '-o', output)
        self.assert_excluded(json.loads(output.read_text())['definitive_analysis'])
        with output.with_suffix('.csv').open(encoding='utf-8-sig') as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row['definitive_analysis_eligible'], 'False')
        self.assertEqual(row['definitive_analysis_status'], 'excluded')
        self.assertIn('recording_version_unverified', row['definitive_analysis_reason_codes'])
        self.assertEqual(row['kills'], '0')

    def test_batch_apis_and_clis_remove_unknown_replay_from_definitive_set(self):
        commands = [('vg.decoder_v2.batch_decode', '--format', 'safe-json'),
                    ('vg.decoder_v2.batch_decode', '--format', 'state-json'),
                    ('vg.decoder_v2.index_export',), ('vg.analysis.batch_report',)]
        for ordinal, command in enumerate(commands):
            with self.subTest(command=command):
                output = self.root / f'batch-{ordinal}.json'
                self.cli(command[0], self.inputs, *command[1:], '-o', output)
                payload = json.loads(output.read_text())
                self.assertEqual((payload['succeeded'], payload['failed']), (1, 0))
                definitive = payload['definitive_analysis']
                self.assertEqual((definitive['included_matches'], definitive['excluded_matches']), (0, 1))
                self.assertEqual(definitive['matches'], [])
                self.assert_excluded(definitive['excluded'][0])
                self.assertEqual(definitive['excluded'][0]['replay_file'], str(self.replay))
        out = self.root / 'exports'
        self.cli('vg.core.export_matches', self.inputs, '--batch', '-o', out)
        report = json.loads((out / 'all_matches.json').read_text())
        self.assertEqual(len(report['matches']), 1)
        self.assertEqual(report['definitive_analysis']['matches'], [])
        self.assertEqual(report['definitive_analysis']['excluded'][0]['input_id'], 'sample.0.vgr')
        with (out / 'match_summary.csv').open(encoding='utf-8-sig') as stream:
            self.assertEqual(next(csv.DictReader(stream))['definitive_analysis_eligible'], 'False')

    def test_empty_and_malformed_metadata_do_not_enable_inclusion(self):
        empty = partition_definitive_analysis([])
        self.assertEqual((empty['included_matches'], empty['excluded_matches']), (0, 0))
        self.assertIsNone(generate_report([])['definitive_analysis']['statistics']['match_stats']['total_kills'])
        for state in (None, [], 'verified', True):
            self.assertEqual(partition_definitive_analysis([{'player_state': state}])['included_matches'], 0)
