import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_native_roster import roster
from tests.test_player_state_service import state_snapshot
from tests.test_native_inventory import anchor, packet
from vg.core.native_roster import read_native_roster
from vg.decoder_v2.player_state import decode_player_state, REQUIRED_FIELDS


def skin_snapshot(skin, *, definition=243, time=1, counters=(1, 2, 3, 4)):
    payload = bytearray(state_snapshot(time=time, actor=7, definition=definition, counters=counters)[10:])
    struct.pack_into('>I', payload, 4, skin)
    return packet(time, 0x03f3, payload)


class SkinIdentitySplitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'match.0.vgr'

    def decode(self, data, **kwargs):
        self.path.write_bytes(data)
        return decode_player_state(self.path, **kwargs)

    def test_skin_conflict_retains_first_spawn_and_partial_roster(self):
        data = anchor() + roster(7, skin=43) + skin_snapshot(42)
        result = read_native_roster([(0, data)])
        player = result.players[0]
        self.assertFalse(result.valid)
        self.assertEqual(player.association_status, 'conflicting_spawn')
        self.assertEqual(player.actor_identity_status, 'corroborated')
        self.assertEqual(player.hero_name, 'Ringo')
        self.assertEqual((player.skin_hash, player.spawn_observations[0].skin_hash), (43, 42))

    def test_same_actor_definition_supports_gameplay_but_not_skin(self):
        result = self.decode(anchor() + roster(7, skin=43) + skin_snapshot(42))
        player = result.players[0]
        self.assertEqual(result.support_status, 'partial')
        self.assertIn('skin mismatch', result.support_reason)
        self.assertTrue(all(player.field_status[k].status == 'supported' for k in REQUIRED_FIELDS))
        self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills), (1, 2, 3, 4))
        self.assertEqual((player.gold_balance, player.net_worth), (25.5, 100.5))
        self.assertEqual(player.native_items, ())
        self.assertEqual((player.skin_hash, player.spawn_skin_hash), (43, 42))
        self.assertEqual(player.field_status['skin'].status, 'conflicting_skin')
        self.assertIn('rendered', player.field_status['skin'].reason)
        self.assertFalse(result.definitive_analysis['eligible'])

    def test_later_matching_skin_cannot_replace_first_actor_or_counters(self):
        result = self.decode(anchor() + roster(7, skin=43) + skin_snapshot(42)
                             + skin_snapshot(43, time=2, counters=(99, 99, 99, 99)))
        player = result.players[0]
        self.assertEqual(player.spawn_skin_hash, 42)
        self.assertEqual(player.field_status['skin'].status, 'conflicting_skin')
        self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills), (1, 2, 3, 4))

    def test_definition_conflict_still_blocks_even_with_later_match(self):
        result = self.decode(anchor() + roster(7, skin=43)
                             + skin_snapshot(42, definition=925)
                             + skin_snapshot(43, time=2))
        player = result.players[0]
        self.assertEqual(player.field_status['native_actor_id'].status, 'identity_unproved')
        self.assertIsNone(player.hero_name)
        self.assertIsNone(player.kills)
        self.assertIsNone(player.gold_balance)
        self.assertIsNone(player.native_items)
        self.assertEqual(player.spawn_skin_hash, 42)

    def test_query_before_spawn_does_not_borrow_future_identity(self):
        result = self.decode(anchor() + roster(7, skin=43) + skin_snapshot(42), at_record_time=0)
        player = result.players[0]
        self.assertIsNone(player.spawn_skin_hash)
        self.assertIsNone(player.kills)
        self.assertEqual(player.field_status['native_actor_id'].status, 'identity_unproved')

    def test_selected_cli_api_preserve_both_raw_skins_and_unknown_rendering(self):
        data = anchor() + roster(7, skin=43) + skin_snapshot(42)
        api = self.decode(data, player_ids=[7]).to_dict()
        process = subprocess.run([sys.executable, '-B', '-m', 'vg.decoder_v2.decode_match',
                                  str(self.path), '--player-id', '7'],
                                 capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(process.stdout), json.loads(json.dumps(api)))
        self.assertEqual(api['players'][0]['spawn_skin_hash'], 42)
        self.assertEqual(api['players'][0]['field_status']['skin']['status'], 'conflicting_skin')
        self.assertEqual(api['support_status'], 'partial')


if __name__ == '__main__':
    unittest.main()
