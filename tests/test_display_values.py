from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tests.test_player_state_service import recording
from tests.test_native_inventory import anchor, packet
from vg.core.display_values import CLIENT_SHA256, f32
from vg.decoder_v2.decode_match import main
from vg.decoder_v2.player_state import decode_player_state


def float_value(value):
    value = f32(value)
    return {'value': value, 'bits': struct.unpack('<I', struct.pack('<f', value))[0]}


def receipt(state):
    return {'schema_version': 'vg.terminal-display-observation.v1',
        'client_sha256': CLIENT_SHA256, 'probe_sha256': 'a' * 64,
        'guard_manifest_sha256': 'b' * 64, 'recording_build_certified': True,
        'server_final_result_certified': True, 'cases': [{
            'replay_scope': state.replay_scope, 'trace_complete': True,
            'source_sections_rehashed': len(state.source_files), 'trace_sha256': 'c' * 64,
            'screenshot_sha256': 'd' * 64, 'event_counts': {'terminal': 1, 'final': 1},
            'gold': [{'actor_id': 7, 'native7': float_value(10899.3955078125),
                'format_input': float_value(10800.3955078125), 'label': '10.8k',
                'last_format_row_seq': 1, 'format_seq': 2, 'label_seq': 3,
                'last_format_previous_cache': 107}],
            'clock': {'decoder_eof_seconds': state.last_game_time,
                'last_anchor': float_value(100), 'terminal_clock': float_value(110),
                'time_format_input': float_value(110), 'terminal_seq': 4, 'final_seq': 5,
                'time_format_seq': 6, 'screenshot_duration_display': '1:50'},
            'accepted_for_definitive_analysis': True}]}


class DisplayValuesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'
        self.replay.write_bytes(recording(gold=(25.5, 10899.3955078125)) + packet(2, 1))
        self.state = decode_player_state(self.replay)
        self.receipt = receipt(self.state)

    def test_default_has_raw_and_estimate_but_no_observed_or_cached_display(self):
        output = self.state.to_dict()
        row = output['display_values']['gold'][0]
        self.assertEqual(row['raw']['value'], output['players'][0]['net_worth'])
        self.assertEqual(row['direct_raw_candidate']['label'], '10.9k')
        self.assertEqual(row['direct_raw_candidate']['status'], 'estimated')
        self.assertIsNone(row['observed'])
        self.assertIsNone(row['reconstructed'])
        self.assertIsNone(output['display_values']['time']['playback_clock_estimate'])
        self.assertFalse(output['definitive_analysis']['eligible'])

    def test_supplied_observation_reproduces_cached_value_without_overwriting_raw(self):
        before = self.replay.read_bytes()
        original_receipt = copy.deepcopy(self.receipt)
        state = decode_player_state(self.replay, runtime_evidence=self.receipt, playback_speed=5)
        row = state.display_values['gold'][0]
        self.assertEqual(row['observed']['label'], '10.8k')
        self.assertEqual(row['reconstructed']['label'], '10.8k')
        self.assertEqual(row['direct_raw_candidate']['label'], '10.9k')
        self.assertEqual(state.players, self.state.players)
        self.assertEqual(state.display_values['time']['raw']['seconds'], 102)
        self.assertEqual(state.display_values['time']['observed']['seconds'], 110)
        self.assertEqual(state.display_values['time']['playback_clock_estimate']['seconds'], 110)
        self.assertIn('not_independently_authenticated', row['observed']['source']['authentication'])
        self.assertFalse(state.definitive_analysis['eligible'])
        self.assertFalse(row['accepted_for_definitive_analysis'])
        self.assertFalse(state.display_values['server_final_result_certified'])
        self.assertEqual(self.receipt, original_receipt)
        self.assertEqual(self.replay.read_bytes(), before)

    def test_measured_zero_is_distinct_from_unavailable(self):
        self.replay.write_bytes(recording(gold=(0, 0)))
        row = decode_player_state(self.replay).display_values['gold'][0]
        self.assertEqual(row['raw']['value'], 0)
        self.assertEqual(row['direct_raw_candidate']['label'], '0.0k')
        self.replay.write_bytes(anchor())
        result = decode_player_state(self.replay).display_values
        self.assertEqual(result['gold'], [])
        self.assertIsNone(result['time']['observed'])

    def test_unchanged_preterminal_time_formatter_attaches_with_unknown_recorded_clock(self):
        (self.root / 'match.1.vgr').write_bytes(anchor(3, 200) + packet(4, 1))
        state = decode_player_state(self.replay)
        evidence = copy.deepcopy(self.receipt)
        case = evidence['cases'][0]
        case['replay_scope'] = state.replay_scope
        case['source_sections_rehashed'] = 2
        clock = case['clock']
        clock.update(decoder_eof_seconds=None, last_anchor=float_value(200),
                     terminal_clock=float_value(210), time_format_input=float_value(210),
                     time_format_seq=4, terminal_seq=5, final_seq=6,
                     screenshot_duration_display='3:30')
        result = decode_player_state(self.replay, runtime_evidence=evidence, playback_speed=5)
        time = result.display_values['time']
        self.assertIsNone(time['raw']['seconds'])
        self.assertIsNone(time['playback_clock_estimate'])
        self.assertEqual(time['observed']['label'], '3:30')
        self.assertEqual(time['reconstructed']['label'], '3:30')
        self.assertFalse(result.definitive_analysis['eligible'])
        for changes in ({'time_format_input': float_value(209)}, {'time_format_seq': 5},
                        {'time_format_seq': 6}, {'terminal_seq': 7}):
            invalid = copy.deepcopy(evidence)
            invalid['cases'][0]['clock'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                decode_player_state(self.replay, runtime_evidence=invalid)

    def test_receipt_rejects_scope_actor_value_bits_label_and_call_order_mismatches(self):
        variants = []
        for key, value in [('replay_scope', 'other'), ('trace_complete', False),
                           ('source_sections_rehashed', 2), ('trace_sha256', 'bad')]:
            item = copy.deepcopy(self.receipt)
            item['cases'][0][key] = value
            variants.append(item)
        for key, value in [('actor_id', 8), ('native7', float_value(1)),
                           ('format_input', {'value': 1, 'bits': 2}), ('label', '10.9k'),
                           ('format_seq', 3), ('last_format_previous_cache', 108)]:
            item = copy.deepcopy(self.receipt)
            item['cases'][0]['gold'][0][key] = value
            variants.append(item)
        for key, value in [('decoder_eof_seconds', 1), ('last_anchor', float_value(99)),
                           ('time_format_input', float_value(111)), ('final_seq', 6),
                           ('screenshot_duration_display', '1:51')]:
            item = copy.deepcopy(self.receipt)
            item['cases'][0]['clock'][key] = value
            variants.append(item)
        duplicate = copy.deepcopy(self.receipt)
        duplicate['cases'].append(copy.deepcopy(duplicate['cases'][0]))
        variants.extend([duplicate, {}, {'schema_version': 'wrong'}])
        for item in variants:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    decode_player_state(self.replay, runtime_evidence=item)

    def test_terminal_receipt_cannot_be_attached_to_capture(self):
        with self.assertRaises(ValueError):
            decode_player_state(self.replay, at_record_time=1, runtime_evidence=self.receipt)
        capture = decode_player_state(self.replay, at_record_time=1, playback_speed=5)
        self.assertIsNone(capture.display_values['time']['observed'])
        self.assertEqual(capture.display_values['time']['scope'], 'capture')

    def test_unknown_clock_mapping_does_not_invent_a_time_estimate(self):
        (self.root / 'match.1.vgr').write_bytes(anchor(3, 200) + packet(4, 1))
        state = decode_player_state(self.replay, playback_speed=5)
        self.assertEqual(state.support_status, 'supported')
        self.assertIsNone(state.display_values['time']['raw']['seconds'])
        self.assertEqual(state.display_values['time']['raw']['status'], 'unknown')
        self.assertEqual(state.display_values['time']['raw']['last_anchor_seconds'], 200)
        self.assertIsNone(state.display_values['time']['playback_clock_estimate'])

    def test_invalid_speeds_rejected_by_api(self):
        for speed in (True, 0, -1, float('nan'), float('inf'), '5'):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                decode_player_state(self.replay, playback_speed=speed)

    def test_cli_attaches_receipt_and_protects_both_replay_and_evidence_outputs(self):
        evidence = self.root / 'receipt.json'
        evidence.write_text(json.dumps(self.receipt))
        before = evidence.read_bytes(), self.replay.read_bytes()
        output = self.root / 'out.json'
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.replay), '--display-evidence', str(evidence),
                                   '--playback-speed', '5', '-o', str(output)]), 0)
        result = json.loads(output.read_text())
        self.assertEqual(result['display_values']['gold'][0]['observed']['label'], '10.8k')
        for target in (evidence, self.replay):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main([str(self.replay), '--display-evidence', str(evidence), '-o', str(target)])
            self.assertEqual(caught.exception.code, 2)
        output_before = output.read_bytes()
        evidence.write_text('{}')
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main([str(self.replay), '--display-evidence', str(evidence), '-o', str(output)])
        self.assertEqual(output.read_bytes(), output_before)
        self.assertEqual(self.replay.read_bytes(), before[1])


if __name__ == '__main__':
    unittest.main()
