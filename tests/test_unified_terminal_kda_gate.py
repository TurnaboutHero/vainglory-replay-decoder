import unittest
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.test_native_inventory import anchor, packet
from tests.test_native_stats import attribute
from tests.test_native_roster import roster
from tests.test_player_state_service import state_snapshot
from vg.core.unified_decoder import UnifiedDecoder
from vg.decoder_v2.decode_match import decode_match


class UnifiedTerminalKDAGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.replay = Path(self.temporary.name) / 'x.0.vgr'

    def assert_final_safe_withheld(self):
        safe = decode_match(str(self.replay))
        self.assertEqual(safe.schema_version, 'decoder_v2.match.v2')
        self.assertEqual(safe.scope, 'final')
        self.assertEqual(len(safe.players), 1)
        self.assertEqual((safe.players[0].kills, safe.players[0].deaths, safe.players[0].assists,
                          safe.players[0].gold), (None, None, None, None))
        for name in ('kills', 'deaths', 'assists', 'minion_kills', 'gold', 'winner', 'duration_seconds'):
            self.assertFalse(safe.withheld_fields[name].accepted_for_index)
            self.assertTrue(safe.withheld_fields[name].reason)

    def test_public_gold_observation_uses_owning_records_and_rejects_bad_operation(self):
        credit = struct.pack('>fIHIfBB4x', 0., 16, 0x041D, 7, 100., 6, 0)
        fake = bytes.fromhex('10041d00000007') + struct.pack('>f', 9000.) + bytes([6,0])
        unrelated = struct.pack('>fIH', 0., len(fake)+2, 0x9999) + fake
        invalid = struct.pack('>fIHIfBB4x', 0., 16, 0x041D, 7, 100., 6, 2)
        for suffix, estimate, balance in ((unrelated, 700, 125.5), (invalid, None, 100)):
            data = anchor(0,100) + roster(7, b'PlayerOne') + state_snapshot() + credit + suffix + packet(10,1)
            with self.subTest(estimate=estimate):
                self.replay.write_bytes(data)
                player = UnifiedDecoder(str(self.replay)).decode().all_players[0]
                self.assertIsNone(player.gold_earned)
                self.assertEqual(player.observed_gold_estimate, estimate)
                self.assertEqual((player.gold_balance, player.net_worth), (balance, 200.5))
                self.assertEqual(player.state_scope, 'recorded_end')
                self.assert_final_safe_withheld()

    def test_complete_native_kill_lead_does_not_establish_winner(self):
        for kills, outcome in ((7, None), (0, SimpleNamespace(winner='right'))):
            data = anchor(0, 500) + roster(7, b'PlayerOne') + state_snapshot(counters=(kills, 2, 3, 100)) + packet(10, 1)
            self.replay.write_bytes(data)
            with self.subTest(kills=kills), \
                 patch.object(UnifiedDecoder, '_scan_kda_events', return_value=(None, {}, {}, 9.)), \
                 patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(9., 2000)), \
                 patch('vg.core.unified_decoder.WinLossDetector') as detector:
                detector.return_value.detect_winner.return_value = outcome
                result = UnifiedDecoder(str(self.replay)).decode()
                self.assertIsNone(result.data_complete)
                self.assertTrue(result.kda_detection_used)
                self.assertEqual(result.all_players[0].kills, kills)
                self.assertEqual(result.all_players[0].state_scope, 'recorded_end')
                self.assertEqual(result.final_validation_status, 'unverified')
                self.assertIsNone(result.winner)
                self.assert_final_safe_withheld()

    def test_valid_native_state_does_not_publish_unconfirmed_final_counters(self):
        data = anchor(0, 100) + roster(7, b'PlayerOne') + state_snapshot(counters=(6, 2, 3, 100)) + attribute(2) + packet(10, 1)
        self.replay.write_bytes(data)
        for estimate, expected_complete in ((9.0, None), (5.0, False)):
            with self.subTest(completeness=expected_complete), \
                 patch.object(UnifiedDecoder, '_scan_kda_events', return_value=(None, {}, {}, estimate)), \
                 patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(None, None)), \
                 patch('vg.core.unified_decoder.WinLossDetector') as winner:
                winner.return_value.detect_winner.return_value = None
                result = UnifiedDecoder(str(self.replay)).decode()
                self.assertIs(result.data_complete, expected_complete)
                self.assertEqual(result.native_stats_status, 'supported')
                player = result.all_players[0]
                self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills),
                                 (7, 2, 3, 100))
                self.assertTrue(result.kda_detection_used)
                self.assertEqual(player.state_scope, 'recorded_end')
                self.assertEqual(result.final_validation_status, 'unverified')
                self.assertIsNone(result.winner)
                self.assert_final_safe_withheld()


if __name__ == '__main__':
    unittest.main()
