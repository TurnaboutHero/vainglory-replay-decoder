from dataclasses import asdict, replace
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_inventory import anchor, grant, packet, snapshot
from tests.test_native_roster import roster
from tests.test_native_stats import attribute, resource
from vg.core.replay_output import ReplayOutputError
from vg.decoder_v2 import player_state


def state_snapshot(time=0, actor=7, items=(), counters=(1, 2, 3, 4), gold=(25.5, 100.5), definition=243):
    payload = bytearray(snapshot(time, items, actor)[10:])
    struct.pack_into('>II', payload, 0, definition, 42)
    struct.pack_into('>ff', payload, 286, *gold)
    for offset, value in zip((298, 302, 306, 310), counters):
        struct.pack_into('>f', payload, offset, value)
    return packet(time, 0x03f3, payload)


def recording(actor=7, items=(), counters=(1, 2, 3, 4), gold=(25.5, 100.5)):
    return anchor() + roster(actor, b'Same') + state_snapshot(actor=actor, items=items, counters=counters, gold=gold)


class PlayerStateServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'

    def write(self, data, tail=()):
        self.replay.write_bytes(data)
        for index, section in enumerate(tail, 1):
            (self.root / f'match.{index}.vgr').write_bytes(section)
        return self.replay

    def test_same_names_and_full_native_actor_ids_are_not_merged(self):
        data = anchor()
        for actor, kills in ((70000, 5), (0xabcdef01, 9)):
            data += roster(actor, b'Same', team=0x1d)
            data += state_snapshot(actor=actor, counters=(kills, 2, 3, 4))
        result = player_state.decode_player_state(self.write(data))
        self.assertEqual(result.support_status, 'supported', result.support_reason)
        self.assertEqual([p.native_actor_id for p in result.players], [70000, 0xabcdef01])
        self.assertEqual([p.name for p in result.players], ['Same', 'Same'])
        self.assertEqual([p.kills for p in result.players], [5, 9])
        self.assertTrue(all(p.hero_name == 'Ringo' for p in result.players))
        self.assertTrue(all(p.team_id == 13 and p.team is None for p in result.players))
        self.assertEqual(result.players[0].field_status['team'].status, 'unresolved_team_side')
        self.assertEqual(result.players[0].field_status['team_id'].status, 'supported')

    def test_end_requests_are_reported_raw_within_the_query_boundary(self):
        end = packet(5, 0x03f1, struct.pack('>IBB', 0x0102, 2, 0))
        result = player_state.decode_player_state(self.write(recording() + end))
        self.assertEqual(result.support_status, 'supported', result.support_reason)
        serialized = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(serialized['end_requests'], [{
            'record_boundary': {'section': 0, 'record_offset': len(recording())}, 'record_time': 5.0,
            'winning_team_raw': 0x0102, 'winning_team_id': 2, 'end_reason': 2, 'request_status': 'queued_request'}])
        early = player_state.decode_player_state(self.write(recording() + end), at_record_time=1)
        self.assertEqual(early.end_requests, ())
        self.assertEqual(player_state.decode_player_state(self.write(recording())).end_requests, ())
        invalid = player_state.decode_player_state(self.write(anchor() + end))
        self.assertNotEqual(invalid.support_status, 'supported')

    def test_duplicate_items_and_hidden_native_possession_are_distinct(self):
        items = ((457, 2000, 1), (526, 2001, 1), (515, 2002, 1), (458, 2003, 1), (458, 2004, 1))
        result = player_state.decode_player_state(self.write(recording(items=items)))
        player = result.players[0]
        self.assertEqual([i.instance_id for i in player.items], [2002, 2003, 2004])
        self.assertEqual([i.definition_id for i in player.items], [515, 458, 458])
        self.assertEqual(len(player.native_items), 5)
        self.assertEqual(player.inventory_capacity, 8)
        self.assertEqual(player.items[0].name, 'Level Juice')
        serialized = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(result.to_dict(), asdict(result))
        self.assertNotIn('reconstruction_index', serialized['players'][0]['items'][1])
        self.assertNotIn('array_index', serialized['players'][0]['items'][1])
        self.assertNotIn('slot', serialized['players'][0]['items'][1])

    def test_every_reader_uses_the_same_capture_boundary(self):
        data = recording() + attribute(2, value=2) + resource(3, value=10, index=6)
        data += resource(3.5, value=8, index=14) + grant(4) + packet(10, 0xffff)
        replay = self.write(data)
        before = player_state.decode_player_state(replay, at_game_time=101)
        after = player_state.decode_player_state(replay, at_game_time=105)
        a, b = before.players[0], after.players[0]
        self.assertEqual((a.kills, a.gold_balance, a.net_worth, a.minion_kills, a.items), (1, 25.5, 100.5, 4, ()))
        self.assertEqual((b.kills, b.gold_balance, b.net_worth, b.minion_kills), (3, 35.5, 110.5, 12))
        self.assertEqual([i.instance_id for i in b.items], [2000])
        self.assertEqual((after.requested_game_time, after.as_of_game_time), (105, 104))
        self.assertEqual(after.scope, 'capture')
        for status in b.field_status.values():
            self.assertEqual(status.provenance.record_boundary, after.record_boundary)
            self.assertEqual(status.provenance.replay_scope, after.replay_scope)
        self.assertIn('native_scoreboard_cs', b.field_status['minion_kills'].provenance.native_fields)
        timed = player_state.decode_player_state(replay, at_record_time=4)
        self.assertEqual(timed.players, after.players)
        self.assertEqual(timed.query_clock, 'record_time')

    def test_eof_includes_every_record_despite_a_paused_last_game_time(self):
        data = recording() + attribute(9, value=2) + resource(9.5, value=10, index=6) + grant(10)
        replay = self.write(data, (anchor(11, 100) + packet(12, 0xffff),))
        end = player_state.decode_player_state(replay)
        timed = player_state.decode_player_state(replay, at_game_time=101)
        self.assertEqual((end.as_of_game_time, end.last_game_time, end.scope), (101, 101, 'recorded_end'))
        self.assertEqual((end.players[0].kills, end.players[0].gold_balance, len(end.players[0].items)), (3, 35.5, 1))
        self.assertEqual(timed.support_status, 'ambiguous_game_time')
        self.assertEqual(timed.players, ())
        self.assertIsNone(timed.record_boundary)

    def test_forward_clock_jump_allows_record_order_without_inventing_game_time(self):
        replay = self.write(recording(), (anchor(10, 125) + attribute(11, value=2),))
        for kwargs in ({}, {'at_record_time': 11}):
            result = player_state.decode_player_state(replay, **kwargs)
            self.assertEqual(result.support_status, 'supported', result.support_reason)
            self.assertEqual(result.players[0].kills, 3)
            self.assertIsNotNone(result.record_boundary)
            self.assertIsNone(result.as_of_game_time)
            self.assertIsNone(result.first_game_time)
            self.assertIsNone(result.last_game_time)
            self.assertIsNone(result.requested_game_time)
            self.assertIn('game-time mapping unavailable', result.support_reason)
        timed = player_state.decode_player_state(replay, at_game_time=101)
        self.assertEqual(timed.support_status, 'unsupported_clock')
        self.assertEqual(timed.players, ())

    def test_backward_clock_reset_remains_unsupported_at_eof(self):
        replay = self.write(recording(), (anchor(10, 80),))
        result = player_state.decode_player_state(replay)
        self.assertEqual(result.support_status, 'mixed_segments')
        self.assertEqual(result.players, ())

    def test_conflicting_roster_cannot_mix_new_hero_with_old_actor_stats(self):
        data = recording() + roster(7, b'Same', definition=925, time=1) + state_snapshot(1, definition=925, counters=(90, 0, 0, 0))
        result = player_state.decode_player_state(self.write(data))
        self.assertNotEqual(result.support_status, 'supported')
        self.assertIsNone(result.players[0].hero_name)
        self.assertNotEqual(result.players[0].field_status['hero'].status, 'supported')

    def test_unknown_items_do_not_zero_other_fields_or_become_empty(self):
        data = recording(counters=(0, 0, 0, 0), gold=(0, 0)) + grant(definition=99999)
        result = player_state.decode_player_state(self.write(data))
        player = result.players[0]
        self.assertEqual(result.support_status, 'partial')
        self.assertIsNone(player.items)
        self.assertIsNone(player.native_items)
        self.assertEqual(player.field_status['items'].status, 'unsupported_state')
        self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills), (0, 0, 0, 0))
        self.assertEqual((player.gold_balance, player.net_worth), (0, 0))
        self.assertEqual(player.field_status['gold_balance'].status, 'supported')

    def test_unknown_gold_keeps_known_empty_inventory_and_counters(self):
        result = player_state.decode_player_state(self.write(recording(gold=(float('nan'), 1))))
        player = result.players[0]
        self.assertIsNone(player.gold_balance)
        self.assertIsNone(player.net_worth)
        self.assertEqual(player.items, ())
        self.assertEqual(player.kills, 1)
        self.assertEqual(player.field_status['gold_balance'].status, 'unsupported_state')

    def test_uncorroborated_identity_cannot_receive_numeric_fields(self):
        data = anchor() + roster(7, b'Same') + state_snapshot(definition=99999)
        result = player_state.decode_player_state(self.write(data))
        player = result.players[0]
        self.assertEqual(player.name, 'Same')
        self.assertIsNone(player.hero_name)
        self.assertIsNone(player.kills)
        self.assertIsNone(player.gold_balance)
        self.assertIsNone(player.items)
        self.assertEqual(player.field_status['kda'].status, 'identity_unproved')

    def test_out_of_coverage_and_future_framing_errors_block_fields(self):
        replay = self.write(recording() + packet(10, 0xffff))
        outside = player_state.decode_player_state(replay, at_game_time=99)
        self.assertEqual(outside.support_status, 'out_of_coverage')
        self.assertEqual(outside.players, ())
        self.assertTrue(all(s.status == 'out_of_coverage' for s in outside.field_status.values()))
        (self.root / 'match.1.vgr').write_bytes(b'bad future framing')
        broken = player_state.decode_player_state(replay, at_game_time=101)
        self.assertEqual(broken.support_status, 'malformed_records')
        self.assertEqual(broken.players, ())

    def test_boundary_or_actor_mismatch_cannot_receive_supported_values(self):
        replay = self.write(recording())
        read = player_state.read_native_gold
        for changes in ({'record_boundary': (0, 9999)}, {'players': ()}):
            with self.subTest(changes=changes), patch.object(
                player_state, 'read_native_gold', side_effect=lambda *a, **k: replace(read(*a, **k), **changes)
            ):
                result = player_state.decode_player_state(replay)
            self.assertIsNone(result.players[0].gold_balance)
            self.assertIn(result.players[0].field_status['gold_balance'].status, ('boundary_mismatch', 'identity_mismatch'))

    def test_source_changed_during_decoding_is_rejected(self):
        original = recording()
        replay = self.write(original)
        read = player_state.read_native_inventory

        def mutate(*args, **kwargs):
            result = read(*args, **kwargs)
            replay.write_bytes(original + packet(2, 0xffff))
            return result

        with patch.object(player_state, 'read_native_inventory', side_effect=mutate):
            with self.assertRaises(ReplayOutputError) as error:
                player_state.decode_player_state(replay)
        self.assertEqual(error.exception.code, 'input_changed')

    def test_invalid_api_clocks_are_not_coerced(self):
        replay = self.write(recording())
        for time in (True, float('nan'), float('inf'), -1, '100'):
            with self.subTest(time=time), self.assertRaises(ValueError):
                player_state.decode_player_state(replay, at_game_time=time)
        with self.assertRaises(ValueError):
            player_state.decode_player_state(replay, at_game_time=100, at_record_time=0)

    def test_literal_glob_characters_do_not_omit_actual_source_sections(self):
        replay = self.root / '[match].0.vgr'
        replay.write_bytes(recording())
        (self.root / '[match].1.vgr').write_bytes(anchor(1, 101) + grant(2))
        result = player_state.decode_player_state(replay)
        self.assertEqual(result.support_status, 'supported', result.support_reason)
        self.assertEqual(len(result.source_files), 2)
        self.assertEqual([i.instance_id for i in result.players[0].items], [2000])


if __name__ == '__main__':
    unittest.main()
