import struct
import unittest

from vg.core.native_roster import read_native_roster
from vg.core.native_stats import GameTime, RecordTime


def packet(opcode, payload=b'', time=0):
    return struct.pack('>fIH', time, len(payload) + 2, opcode) + payload


def anchor(time=0, game=100):
    payload = bytearray(69)
    struct.pack_into('>f', payload, 64, game)
    return packet(0x046f, payload, time)


def roster(entity=1500, name=b'A', definition=243, skin=42, team=1, extra=0, time=0):
    payload = bytearray(216 + extra)
    payload[:len(name)] = name
    struct.pack_into('>III', payload, 160, entity, definition, skin)
    payload[210] = team
    return packet(0x03ee, payload, time)


def spawn(entity=1500, definition=243, skin=42, opcode=0x03f3, extra=0, time=0):
    payload = bytearray((746 if opcode == 0x03f3 else 122) + extra)
    struct.pack_into('>III', payload, 0, definition, skin, entity)
    return packet(opcode, payload, time)


class NativeRosterTests(unittest.TestCase):
    def read(self, data):
        return read_native_roster([(0, anchor() + data)])

    def test_distinct_actors_same_name(self):
        result = self.read(roster(70000, b'Same') + roster(70001, b'Same') +
                           spawn(70000) + spawn(70001))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual([p.entity_id for p in result.players], [70000, 70001])
        self.assertEqual([p.name for p in result.players], ['Same', 'Same'])

    def test_embedded_marker_is_not_roster(self):
        result = self.read(packet(0x7777, roster() + b'\xda\x03\xeeFake'))
        self.assertEqual(result.players, ())
        self.assertEqual(result.status, 'missing_roster')

    def test_short_name_and_32bit_actor(self):
        result = self.read(roster(0xabcdef01) + spawn(0xabcdef01))
        self.assertTrue(result.valid, result.reason)
        player = result.players[0]
        self.assertEqual(player.name, 'A')
        self.assertEqual(player.entity_id, 0xabcdef01)
        self.assertEqual((player.definition_index, player.skin_hash), (243, 42))
        self.assertEqual(player.hero_name, 'Ringo')

    def test_utf8_bmp_and_unsupported_encoding(self):
        result = self.read(roster(name='한글é'.encode()) + spawn())
        self.assertEqual(result.players[0].name, '한글é')
        for raw in (b'\xff', '😀'.encode()):
            with self.subTest(raw=raw):
                result = self.read(roster(name=raw) + spawn())
                self.assertFalse(result.valid)
                self.assertIsNone(result.players[0].name)
                self.assertEqual(result.players[0].observations[0].raw_name_hex, raw.hex())

    def test_64byte_name_requires_terminator(self):
        result = self.read(roster(name=b'A' * 64) + spawn())
        self.assertFalse(result.valid)
        self.assertEqual(result.players[0].name_status, 'unterminated_name')

    def test_repeated_snapshots_and_name_changes_are_preserved(self):
        result = self.read(roster(name=b'A') + spawn() + roster(name=b'B', extra=6) + spawn(extra=4))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(len(result.players), 1)
        self.assertEqual(result.players[0].name, 'B')
        self.assertEqual([x.name for x in result.players[0].observations], ['A', 'B'])

    def test_conflicting_definition_is_explicit(self):
        result = self.read(roster() + spawn(definition=925))
        self.assertFalse(result.valid)
        self.assertEqual(result.players[0].association_status, 'conflicting_spawn')
        self.assertIsNone(result.players[0].hero_name)

    def test_missing_spawn_cannot_prove_association(self):
        result = self.read(roster())
        self.assertFalse(result.valid)
        self.assertEqual(result.players[0].association_status, 'missing_spawn')

    def test_spawn_without_roster_is_not_a_player(self):
        self.assertEqual(self.read(spawn()).players, ())

    def test_unknown_team_never_filled(self):
        result = self.read(roster(team=0xff) + spawn())
        self.assertEqual(result.players[0].team_id, 15)
        self.assertIsNone(result.players[0].team)
        self.assertEqual(result.players[0].observations[0].raw_team_byte, 255)

    def test_cutoff_cannot_read_future_identity(self):
        frames = [(0, anchor() + roster() + spawn() + roster(name=b'Later', time=2) + spawn(time=2))]
        for cutoff in (GameTime(101), RecordTime(1)):
            result = read_native_roster(frames, cutoff)
            self.assertEqual(result.players[0].name, 'A')
        self.assertEqual(read_native_roster(frames).players[0].name, 'Later')
        self.assertEqual(read_native_roster(frames, GameTime(103)).status, 'out_of_coverage')

    def test_malformed_future_records_fail_even_early_query(self):
        result = read_native_roster([(0, anchor() + roster() + spawn() + b'bad')], GameTime(100))
        self.assertEqual(result.status, 'malformed_records')

    def test_unsupported_roster_layout_and_reserved_id(self):
        self.assertFalse(self.read(roster(extra=1) + spawn()).valid)
        self.assertFalse(self.read(roster(0xffffffff) + spawn(0xffffffff)).valid)

    def test_ignored_spawn_cannot_redefine_effective_actor(self):
        result = self.read(roster() + spawn() + roster(definition=925, skin=17) + spawn(definition=925, skin=17))
        self.assertFalse(result.valid)
        self.assertIsNone(result.players[0].hero_name)
        self.assertEqual(result.players[0].association_status, 'conflicting_spawn')
        self.assertEqual([x.definition_index for x in result.players[0].observations], [243, 925])
        self.assertEqual([x.definition_index for x in result.players[0].spawn_observations], [243, 925])

    def test_unknown_definition_not_guessed(self):
        result = self.read(roster(definition=999999) + spawn(definition=999999))
        self.assertFalse(result.valid)
        self.assertIsNone(result.players[0].hero_name)

    def test_original_asset_aliases_replace_legacy_guesses(self):
        for definition, name in ((254, 'Krul'), (255, 'Skaarf'), (256, 'Taka'),
                                 (260, 'Rona'), (446, 'San Feng')):
            with self.subTest(definition=definition):
                result = self.read(roster(definition=definition) + spawn(definition=definition))
                self.assertEqual(result.players[0].hero_name, name)

    def test_skin_conflict_and_unknown_layout_are_not_accepted(self):
        self.assertEqual(self.read(roster() + spawn(skin=43)).players[0].association_status, 'conflicting_spawn')
        self.assertFalse(self.read(roster() + spawn(extra=2)).valid)

    def test_short_spawn_variant_can_corroborate(self):
        result = self.read(roster() + spawn(opcode=0x03f2, extra=4))
        self.assertTrue(result.valid, result.reason)

    def test_item_definition_is_not_a_hero(self):
        result = self.read(roster(definition=515) + spawn(definition=515))
        self.assertFalse(result.valid)
        self.assertIsNone(result.players[0].hero_name)

    def test_boundary_is_last_included_record_not_query(self):
        initial = anchor() + roster() + spawn()
        middle = packet(0x7777, time=1)
        frames = [(0, initial + middle + packet(0x7777, time=3))]
        result = read_native_roster(frames, GameTime(102))
        self.assertEqual(result.record_boundary, (0, len(initial)))
        self.assertEqual(result.as_of_game_time, 101)
        self.assertEqual(read_native_roster(frames).record_boundary, (0, len(initial + middle)))
        self.assertIsNone(read_native_roster(frames, GameTime(999)).record_boundary)

    def test_boundary_tracks_numbered_section(self):
        first = anchor() + roster() + spawn()
        second = anchor(10, 110) + roster(time=10) + spawn(time=10)
        result = read_native_roster([(0, first), (1, second)])
        self.assertEqual(result.record_boundary, (1, len(anchor(10, 110) + roster(time=10))))
