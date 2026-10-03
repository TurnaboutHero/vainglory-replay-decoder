import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_native_stats import anchor, snapshot, attribute, packet
from tests.test_native_stats_integration import PARSED
from vg.core.unified_decoder import UnifiedDecoder


class UnifiedTerminalKDAGateTests(unittest.TestCase):
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
            self.assertTrue(result.data_complete)
            self.assertTrue(result.kda_detection_used)
            self.assertEqual(result.left_team[0].kills, kills)
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
