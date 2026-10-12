import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_display_values import receipt
from tests.test_native_inventory import anchor, grant, packet
from tests.test_native_roster import roster
from tests.test_native_stats import attribute, resource
from tests.test_player_state_service import state_snapshot
from vg.core.display_values import DisplayEvidenceError
from vg.decoder_v2.player_state import decode_player_state


class PlayerStateTimeQueryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.replay = Path(self.temp.name) / 'match.0.vgr'
        self.data = anchor(0, 590)
        for actor in (7, 70000):
            self.data += roster(actor, b'Same') + state_snapshot(actor=actor)
        self.data += attribute(9, value=2) + resource(9.5, value=10, index=6)
        self.data += attribute(11, value=4) + packet(20, 0xffff)
        self.replay.write_bytes(self.data)

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-m', 'vg.decoder_v2.decode_match',
            str(self.replay), *map(str, args)], capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[1], timeout=30)

    def test_all_and_selected_share_boundary_and_every_field(self):
        all_state = decode_player_state(self.replay, at_game_time=600)
        selected = decode_player_state(self.replay, at_game_time=600, player_ids=[7])
        self.assertEqual(all_state.support_status, 'supported', all_state.support_reason)
        self.assertEqual(selected.players, (all_state.players[0],))
        self.assertEqual(selected.players[0].kills, 3)
        self.assertEqual(selected.players[0].gold_balance, 35.5)
        for key in ('record_boundary', 'replay_scope', 'source_files', 'field_status', 'query_timing'):
            self.assertEqual(getattr(selected, key), getattr(all_state, key))
        self.assertEqual(selected.display_values['gold'], all_state.display_values['gold'][:1])
        self.assertEqual(selected.display_values['time'], all_state.display_values['time'])
        reversed_ids = decode_player_state(self.replay, at_game_time=600, player_ids=(70000, 7))
        self.assertEqual(reversed_ids.players, all_state.players)
        self.assertFalse(selected.definitive_analysis['eligible'])
        self.assertEqual(self.replay.read_bytes(), self.data)

    def test_preceding_record_reports_actual_and_projected_times_without_interpolation(self):
        state = decode_player_state(self.replay, at_game_time=600)
        timing = state.query_timing
        self.assertEqual(state.as_of_game_time, 599.5)
        self.assertEqual(timing['cutoff_relation'], 'preceding_record')
        self.assertEqual(timing['applied']['record_time'], 9.5)
        self.assertEqual(timing['applied']['projected_game_time'], 599.5)
        self.assertEqual(timing['applied']['anchor_record_time'], 0)
        self.assertEqual(timing['applied']['anchor_game_time'], 590)
        self.assertEqual(timing['applied']['record_boundary'], {'section': 0,
            'record_offset': state.record_boundary.record_offset})
        self.assertEqual(timing['next_record']['record_time'], 11)
        self.assertEqual(timing['next_record']['projected_game_time'], 601)
        self.assertEqual(timing['seconds_before_requested'], .5)
        self.assertEqual(timing['bracketing_record_interval_seconds'], 1.5)
        self.assertFalse(timing['state_interpolated'])
        self.assertFalse(timing['native_game_clock_observed'])

    def test_exact_record_and_record_clock_queries_are_consistent(self):
        mapped = decode_player_state(self.replay, at_game_time=599.5)
        recorded = decode_player_state(self.replay, at_record_time=9.5)
        self.assertEqual(mapped.players, recorded.players)
        self.assertEqual(mapped.record_boundary, recorded.record_boundary)
        for state in (mapped, recorded):
            self.assertEqual(state.query_timing['cutoff_relation'], 'exact_record_boundary')
            self.assertEqual(state.query_timing['seconds_before_requested'], 0)
        end = decode_player_state(self.replay)
        self.assertEqual(end.query_timing['cutoff_relation'], 'recorded_end')
        self.assertIsNone(end.query_timing['next_record'])

    def test_unknown_player_fails_entire_selection_without_partial_success(self):
        for ids in ([999], [7, 999]):
            with self.subTest(ids=ids):
                state = decode_player_state(self.replay, at_game_time=600, player_ids=ids)
                self.assertEqual(state.support_status, 'player_not_found')
                self.assertEqual(state.players, ())
                self.assertEqual(state.player_selection['missing_ids'], [999])
                self.assertEqual(state.display_values['gold'], [])
                self.assertIsNotNone(state.query_timing['applied'])

    def test_invalid_player_ids_are_rejected_before_loading(self):
        for ids in ([], (), [True], [1.0], [0], [-1], [0xffffffff], [2**32],
                    [7, 7], ['7'], [[7]], '7', {7}):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                decode_player_state('missing.vgr', player_ids=ids)

    def test_selection_keeps_full_roster_partial_support(self):
        self.replay.write_bytes(self.data + grant(21, definition=99999, actor=70000))
        state = decode_player_state(self.replay, player_ids=[7])
        self.assertEqual(state.support_status, 'partial')
        self.assertEqual(state.players[0].field_status['items'].status, 'supported')
        self.assertNotEqual(state.field_status['items'].status, 'supported')
        self.assertEqual(state.player_selection['support_scope'], 'all_recorded_players_before_selection')

    def test_out_of_coverage_cannot_be_masked_by_missing_selection(self):
        for time in (589, 611):
            with self.subTest(time=time):
                state = decode_player_state(self.replay, at_game_time=time, player_ids=[999])
                self.assertEqual(state.support_status, 'out_of_coverage')
                self.assertEqual(state.player_selection['status'], 'unavailable')
                self.assertIsNone(state.query_timing['applied'])
                self.assertEqual(state.query_timing['coverage']['last_game_time'], 610)

    def test_future_malformed_data_blocks_earlier_query(self):
        self.replay.write_bytes(self.data + b'broken')
        state = decode_player_state(self.replay, at_game_time=600, player_ids=[7])
        self.assertEqual(state.support_status, 'malformed_records')
        self.assertEqual(state.players, ())
        self.assertFalse(state.query_timing['clock_audit']['game_time_mapping_valid'])

    def test_forward_jump_blocks_game_query_and_record_query_keeps_game_time_unknown(self):
        self.replay.with_name('match.1.vgr').write_bytes(anchor(21, 650) + packet(22, 0xffff))
        state = decode_player_state(self.replay, at_game_time=600, player_ids=[7])
        self.assertEqual(state.support_status, 'unsupported_clock')
        self.assertIsNone(state.query_timing['applied'])
        recorded = decode_player_state(self.replay, at_record_time=9.5, player_ids=[7])
        self.assertEqual(recorded.support_status, 'supported', recorded.support_reason)
        self.assertEqual(recorded.query_timing['applied']['record_time'], 9.5)
        self.assertIsNone(recorded.query_timing['applied']['projected_game_time'])
        self.assertIsNone(recorded.query_timing['next_record']['projected_game_time'])
        self.assertIsNone(recorded.as_of_game_time)
        self.assertEqual(recorded.query_timing['clock_audit']['status'], 'record_order_only')

    def test_nonconsecutive_sections_block_query(self):
        self.replay.with_name('match.2.vgr').write_bytes(anchor(21, 611))
        state = decode_player_state(self.replay, at_game_time=600, player_ids=[7])
        self.assertEqual(state.support_status, 'mixed_segments')
        self.assertEqual(state.players, ())
        self.assertEqual(state.query_timing['coverage']['section_count'], 2)

    def test_display_anchor_belongs_to_applied_section(self):
        self.replay.with_name('match.1.vgr').write_bytes(anchor(21, 611) + packet(22, 0xffff))
        state = decode_player_state(self.replay, at_game_time=600)
        self.assertEqual(state.display_values['time']['raw']['last_anchor_seconds'], 590)
        self.assertIsNone(state.display_values['time']['observed'])
        self.assertIsNone(state.display_values['time']['reconstructed'])

    def test_terminal_receipt_is_validated_before_projection_and_rejected_at_capture(self):
        self.replay.write_bytes(anchor() + roster(7) + state_snapshot(actor=7, gold=(25.5, 10899.3955078125))
            + roster(70000) + state_snapshot(actor=70000, gold=(25.5, 10899.3955078125)))
        state = decode_player_state(self.replay)
        evidence = receipt(state)
        extra = copy.deepcopy(evidence['cases'][0]['gold'][0])
        extra['actor_id'] = 70000
        evidence['cases'][0]['gold'].append(extra)
        all_state = decode_player_state(self.replay, runtime_evidence=evidence)
        selected = decode_player_state(self.replay, runtime_evidence=evidence, player_ids=[7])
        self.assertEqual(selected.display_values['gold'], all_state.display_values['gold'][:1])
        evidence['cases'][0]['gold'].pop()
        with self.assertRaises(DisplayEvidenceError):
            decode_player_state(self.replay, runtime_evidence=evidence, player_ids=[7])
        with self.assertRaises(DisplayEvidenceError):
            decode_player_state(self.replay, at_game_time=100, runtime_evidence=evidence, player_ids=[7])

    def test_cli_selected_matches_api_and_does_not_modify_source(self):
        process = self.cli('--at-game-time', 600, '--player-id', 70000, '--player-id', 7)
        self.assertEqual(process.returncode, 0, process.stderr)
        expected = decode_player_state(self.replay, at_game_time=600, player_ids=[70000, 7]).to_dict()
        self.assertEqual(json.loads(process.stdout), json.loads(json.dumps(expected)))
        self.assertEqual(self.replay.read_bytes(), self.data)

    def test_cli_rejects_bad_selection_without_overwriting_existing_report(self):
        output = Path(self.temp.name) / 'report.json'
        output.write_text('previous report')
        for args in (('--player-id', '0'), ('--player-id', '4294967295'),
                     ('--player-id', 'true'), ('--player-id', '7', '--player-id', '7'),
                     ('--player-id', '7', '--format', 'safe-json'),
                     ('--player-id', '7', '--format', 'debug-json')):
            with self.subTest(args=args):
                process = self.cli('-o', output, *args)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(output.read_text(), 'previous report')

    def test_cli_missing_player_is_explicit_not_empty_success(self):
        process = self.cli('--at-game-time', 600, '--player-id', 999)
        self.assertEqual(process.returncode, 0, process.stderr)
        state = json.loads(process.stdout)
        self.assertEqual(state['support_status'], 'player_not_found')
        self.assertEqual(state['players'], [])
        self.assertEqual(state['player_selection']['missing_ids'], [999])


if __name__ == '__main__':
    unittest.main()
