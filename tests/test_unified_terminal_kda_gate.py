import unittest
import struct
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_native_stats import anchor, snapshot, attribute, packet
from tests.test_native_stats_integration import PARSED
from vg.core.unified_decoder import UnifiedDecoder


class UnifiedTerminalKDAGateTests(unittest.TestCase):
    def test_public_gold_observation_uses_owning_records_and_rejects_bad_operation(self):
        credit = struct.pack('>fIHIfBB4x', 0., 16, 0x041D, 7, 100., 6, 0)
        fake = bytes.fromhex('10041d00000007') + struct.pack('>f', 9000.) + bytes([6,0])
        unrelated = struct.pack('>fIH', 0., len(fake)+2, 0x9999) + fake
        invalid = struct.pack('>fIHIfBB4x', 0., 16, 0x041D, 7, 100., 6, 2)
        for suffix, estimate in ((unrelated, 700), (invalid, None)):
            data = anchor(0,100) + snapshot(0) + credit + suffix + packet(10,1)
            with self.subTest(estimate=estimate), \
                 patch('vg.core.unified_decoder.VGRParser') as parser, \
                 patch.object(UnifiedDecoder, '_load_frames', return_value=[(0,data)]), \
                 patch.object(UnifiedDecoder, '_scan_kda_events', return_value=(None,{},{},9.)), \
                 patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(None,None)), \
                 patch('vg.core.unified_decoder.WinLossDetector') as winner:
                parser.return_value.parse.return_value = PARSED
                winner.return_value.detect_winner.return_value = None
                player = UnifiedDecoder('x.0.vgr').decode().left_team[0]
                self.assertIsNone(player.gold_earned)
                self.assertEqual(player.observed_gold_estimate, estimate)

    def test_complete_native_kill_lead_does_not_establish_winner(self):
        for kills, outcome in ((7, None), (0, SimpleNamespace(winner='right'))):
            data = anchor(0, 500) + snapshot(0, (kills, 2, 3, 100)) + packet(10, 1)
            with self.subTest(kills=kills), \
                 patch('vg.core.unified_decoder.VGRParser') as parser, \
                 patch.object(UnifiedDecoder, '_load_frames', return_value=[(0, data)]), \
                 patch.object(UnifiedDecoder, '_scan_kda_events', return_value=(None, {}, {}, 9.)), \
                 patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(9., 2000)), \
                 patch('vg.core.unified_decoder.WinLossDetector') as detector:
                parser.return_value.parse.return_value = PARSED
                detector.return_value.detect_winner.return_value = outcome
                result = UnifiedDecoder('x.0.vgr').decode()
            self.assertIsNone(result.data_complete)
            self.assertFalse(result.kda_detection_used)
            self.assertIsNone(result.left_team[0].kills)
            self.assertIsNone(result.winner)

    def test_valid_native_state_does_not_publish_unconfirmed_final_counters(self):
        data = anchor(0, 100) + snapshot(0) + attribute(2) + packet(10, 1)
        for estimate, expected_complete in ((9.0, None), (5.0, False)):
            with self.subTest(completeness=expected_complete), \
                 patch('vg.core.unified_decoder.VGRParser') as parser, \
                 patch.object(UnifiedDecoder, '_load_frames', return_value=[(0, data)]), \
                 patch.object(UnifiedDecoder, '_scan_kda_events', return_value=(None, {}, {}, estimate)), \
                 patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(None, None)), \
                 patch('vg.core.unified_decoder.WinLossDetector') as winner:
                parser.return_value.parse.return_value = PARSED
                winner.return_value.detect_winner.return_value = None
                result = UnifiedDecoder('x.0.vgr').decode()
                self.assertIs(result.data_complete, expected_complete)
                self.assertEqual(result.native_stats_status, 'accepted')
                player = result.left_team[0]
                self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills),
                                 (None, None, None, None))
                self.assertFalse(result.kda_detection_used)
                self.assertIsNone(result.winner)


if __name__ == '__main__':
    unittest.main()
