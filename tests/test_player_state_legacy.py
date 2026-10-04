from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from tests.test_player_state_service import recording, state_snapshot
from tests.test_native_inventory import anchor
from tests.test_native_roster import roster
from vg.core.unified_decoder import DecodedMatch, DecodedPlayer, UnifiedDecoder, _le_to_be
from vg.decoder_v2.player_state import decode_player_state


class PlayerStateLegacyTests(unittest.TestCase):
    def state(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(data)
            return decode_player_state(path)

    def test_full_actor_ids_same_names_and_unknown_teams_survive(self):
        state = self.state(anchor() + roster(70000, b'Same') + state_snapshot(actor=70000)
                           + roster(0xabcdef01, b'Same') + state_snapshot(actor=0xabcdef01))
        players = UnifiedDecoder._native_players(state, [])
        self.assertEqual([p.native_actor_id for p in players], [70000, 0xabcdef01])
        self.assertEqual([p.name for p in players], ['Same', 'Same'])
        self.assertTrue(all(p.entity_id is None and p.team is None for p in players))
        match = DecodedMatch('match', 'match.0.vgr', 'unknown', 'unknown', 3, unassigned_players=players)
        self.assertEqual(match.all_players, players)
        self.assertEqual(len(match.to_dict()['unassigned_players']), 2)

    def test_six_fields_and_recorded_net_worth_alias_use_shared_state(self):
        state = self.state(recording(items=((458, 2000, 1), (458, 2001, 1))))
        player = UnifiedDecoder._native_players(state, [DecodedPlayer('Wrong', 'left', 'Wrong', 0, 0)])[0]
        source = state.players[0]
        self.assertEqual((player.name, player.hero_name, player.kills, player.deaths, player.assists,
                          player.minion_kills), (source.name, source.hero_name, 1, 2, 3, 4))
        self.assertEqual(player.items, ['Weapon Blade', 'Weapon Blade'])
        self.assertEqual((player.gold, player.net_worth, player.gold_balance), (100.5, 100.5, 25.5))
        self.assertIsNone(player.gold_earned)
        self.assertEqual(player.state_scope, 'recorded_end')
        self.assertEqual(player.as_of_game_time, state.as_of_game_time)
        self.assertEqual(player.field_status['gold']['alias_of'], 'net_worth')
        self.assertEqual(player.field_status['gold']['provenance']['record_boundary'], player.record_boundary)
        self.assertTrue(all('reconstruction_index' not in item for item in player.item_details))

    def test_auxiliary_positions_join_only_unique_representable_actor(self):
        state = self.state(recording())
        old = DecodedPlayer('Different', 'left', 'Different', 0, _le_to_be(7), positions=[(1, 2, 3)])
        self.assertEqual(UnifiedDecoder._native_players(state, [old])[0].positions, [(1, 2, 3)])
        self.assertEqual(UnifiedDecoder._native_players(state, [old, old])[0].positions, [])
        other = replace(old, entity_id=_le_to_be(8), name=state.players[0].name)
        self.assertEqual(UnifiedDecoder._native_players(state, [other])[0].positions, [])

    def test_unknown_fields_stay_null_and_zero_stays_zero(self):
        state = self.state(recording(counters=(0, 0, 0, 0), gold=(0, 0)))
        zero = UnifiedDecoder._native_players(state, [])[0]
        self.assertEqual((zero.kills, zero.gold, zero.items), (0, 0, []))
        source = replace(state.players[0], kills=None, net_worth=None, items=None, native_items=None)
        unknown = UnifiedDecoder._native_players(replace(state, players=(source,)), [])[0]
        self.assertEqual((unknown.kills, unknown.gold, unknown.items, unknown.native_items), (None,) * 4)


if __name__ == '__main__':
    unittest.main()
