import math
import struct
import unittest

from vg.core.native_stats import GameTime, RecordTime, inspect_native_clock, read_native_stats


def packet(time, opcode, payload=b''):
    return struct.pack('>fIH', time, len(payload) + 2, opcode) + payload


def anchor(time, game):
    data = bytearray(69)
    struct.pack_into('>f', data, 64, game)
    return packet(time, 0x046f, data)


def snapshot(time, values=(6, 2, 3, 100), entity=7, flag=0, extra=0):
    data = bytearray(746 + extra)
    struct.pack_into('>I', data, 8, entity)
    struct.pack_into('>I', data, 326, flag)
    for offset, value in zip((298, 302, 306, 310), values):
        struct.pack_into('>f', data, offset, value)
    return packet(time, 0x03f3, data)


def attribute(time, value=1, index=41, mode=0, layer=0, entity=7):
    data = bytearray(22)
    struct.pack_into('>I', data, 0, entity)
    struct.pack_into('>f', data, 8, value)
    data[12:15] = bytes((index, layer, mode))
    return packet(time, 0x041c, data)


def resource(time, value=1, index=11, mode=0, entity=7):
    data = bytearray(14)
    struct.pack_into('>If', data, 0, entity, value)
    data[8:10] = bytes((index, mode))
    return packet(time, 0x041d, data)


def frame(time=0, game=100):
    return anchor(time, game) + snapshot(time + .7) + packet(time + 10, 0xffff)


class NativeStatsTests(unittest.TestCase):
    def read(self, data, cutoff=None):
        return read_native_stats([(0, data)], [7], cutoff)

    def test_snapshot_is_initial_state_with_real_clock(self):
        result = self.read(frame(), GameTime(105))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual((result.players[0].kills, result.players[0].minion_kills), (6, 100))
        self.assertEqual(result.as_of_game_time, 105)
        self.assertEqual(result.first_game_time, 100)
        self.assertEqual(result.last_game_time, 110)

    def test_native_set_add_and_resource_clamp(self):
        data = anchor(0, 100) + snapshot(0) + attribute(1, 2) + attribute(2, 4, mode=1)
        data += resource(3, 10) + resource(4, 2, mode=4) + resource(5, -20) + packet(10, 1)
        result = self.read(data)
        self.assertTrue(result.valid, result.reason)
        self.assertEqual((result.players[0].kills, result.players[0].assists), (4, 0))

    def test_rebaseline_assigns_without_double_count(self):
        frames = [(0, anchor(0, 100) + snapshot(0) + attribute(9)),
                  (1, anchor(10, 110) + snapshot(10, (7, 2, 3, 100), extra=4) + attribute(11))]
        result = read_native_stats(frames, [7])
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].kills, 8)

    def test_capture_freezes_before_later_snapshot_and_unsupported_layer(self):
        data = anchor(0, 100) + snapshot(0) + attribute(2) + attribute(6, layer=1)
        data += snapshot(7, (50, 0, 0, 0)) + packet(10, 1)
        result = self.read(data, GameTime(104))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].kills, 7)
        self.assertFalse(self.read(data, GameTime(106)).valid)

    def test_record_time_converts_to_game_time(self):
        result = self.read(frame(20, 500), RecordTime(25))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.as_of_game_time, 505)
        self.assertEqual(result.requested_game_time, 505)

    def test_missing_or_bypassed_baseline_never_returns_zero_players(self):
        for data in (anchor(0, 0) + attribute(1), anchor(0, 0) + snapshot(0, flag=1) + attribute(1)):
            result = self.read(data)
            self.assertFalse(result.valid)
            self.assertEqual(result.players, ())
            self.assertEqual(result.status, 'missing_baseline')

    def test_cutoff_before_first_baseline_rejected(self):
        result = self.read(frame(), GameTime(100.1))
        self.assertEqual(result.status, 'missing_baseline')

    def test_outside_coverage_and_nonfinite_query_rejected(self):
        for cutoff in (GameTime(99), GameTime(111), RecordTime(-1), RecordTime(11)):
            self.assertEqual(self.read(frame(), cutoff).status, 'out_of_coverage')
        for cutoff in (GameTime(math.nan), RecordTime(math.inf)):
            self.assertEqual(self.read(frame(), cutoff).status, 'invalid_query')

    def test_invalid_counts_not_truncated(self):
        for value in (-1, .5, math.inf, math.nan):
            with self.subTest(value=value):
                self.assertFalse(self.read(anchor(0, 0) + snapshot(0, (value, 0, 0, 0))).valid)
        for value in (.5, math.inf, math.nan):
            self.assertFalse(self.read(anchor(0, 0) + snapshot(0) + attribute(1, value)).valid)

    def test_relevant_unsupported_layers_and_formats_reject(self):
        base = anchor(0, 0) + snapshot(0)
        self.assertEqual(self.read(base + attribute(1, layer=1)).status, 'unsupported_state')
        self.assertEqual(self.read(base + packet(1, 0x041c, struct.pack('>I', 7))).status, 'unsupported_state')
        self.assertEqual(self.read(base + packet(1, 0x03f3, b'\0' * 12)).status, 'accepted')

    def test_unknown_events_and_other_actor_changes_ignored(self):
        data = anchor(0, 0) + snapshot(0) + packet(1, 0x1234, b'anything')
        data += attribute(2, layer=2, entity=88) + attribute(3, index=3, layer=2)
        self.assertTrue(self.read(data).valid)

    def test_missing_one_player_withholds_entire_scoreboard(self):
        result = read_native_stats([(0, frame())], [7, 8])
        self.assertEqual(result.status, 'missing_baseline')
        self.assertEqual(result.players, ())

    def test_nonzero_attribute_mode_is_set(self):
        result = self.read(anchor(0, 0) + snapshot(0) + attribute(1, 2, mode=2))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].kills, 2)

    def test_repeated_spawn_values_are_ignored_for_existing_actor(self):
        data = anchor(0, 100) + snapshot(0) + snapshot(6, (math.nan, 0, 0, 0)) + packet(10, 1)
        self.assertTrue(self.read(data, GameTime(105)).valid)
        self.assertTrue(self.read(data).valid)
        self.assertEqual(self.read(data).players[0].kills, 6)

    def test_repeated_spawn_does_not_clear_unsupported_state(self):
        data = anchor(0, 0) + snapshot(0) + attribute(1, layer=2) + snapshot(2, (3, 4, 5, 6))
        result = self.read(data)
        self.assertFalse(result.valid)
        self.assertEqual(result.status, 'unsupported_state')

    def test_repeated_spawn_preserves_applied_updates(self):
        data = anchor(0, 0) + snapshot(0, (1, 0, 0, 0)) + attribute(1, 1) + snapshot(2, (99, 9, 9, 9))
        result = self.read(data)
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].kills, 2)

    def test_destroy_request_prevents_claiming_a_later_actor_lifetime(self):
        data = anchor(0, 0) + snapshot(0) + packet(1, 0x040b, struct.pack('>I', 7)) + snapshot(2)
        self.assertEqual(self.read(data).status, 'unsupported_state')

    def test_existing_actor_without_baseline_cannot_be_recreated(self):
        data = anchor(0, 0) + snapshot(0, flag=1) + snapshot(1)
        self.assertEqual(self.read(data).status, 'missing_baseline')

    def test_short_spawn_already_created_actor_before_full_spawn(self):
        spawn = bytearray(122)
        struct.pack_into('>I', spawn, 8, 7)
        data = anchor(0, 0) + packet(0, 0x03f2, spawn) + snapshot(1)
        self.assertEqual(self.read(data).status, 'missing_baseline')

    def test_layer_three_remains_unknown_after_later_snapshot(self):
        data = anchor(0, 0) + snapshot(0) + attribute(1, layer=3) + snapshot(2)
        result = self.read(data)
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIn('layer 3', result.reason)
        self.assertTrue(self.read(data, GameTime(.5)).valid)

    def test_negative_attribute_count_rejected(self):
        result = self.read(anchor(0, 0) + snapshot(0) + attribute(1, -10))
        self.assertEqual(result.status, 'unsupported_state')

    def test_short_target_snapshot_rejected_with_location(self):
        data = bytearray(12)
        struct.pack_into('>I', data, 8, 7)
        result = self.read(anchor(0, 0) + snapshot(0) + packet(1, 0x03f3, data))
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIn('opcode 03f3', result.reason)
        self.assertIn('frame 0 offset', result.reason)

    def test_empty_player_list_cannot_claim_valid_scoreboard(self):
        self.assertFalse(read_native_stats([(0, frame())], []).valid)


class NativeClockTests(unittest.TestCase):
    def test_global_mixed_clock_rejects_even_early_capture(self):
        frames = [(0, frame()), (1, frame(11, 1))]
        result = read_native_stats(frames, [7], GameTime(105))
        self.assertFalse(result.valid)
        self.assertEqual(result.status, 'mixed_segments')
        self.assertIn('0', result.reason)
        self.assertIn('1', result.reason)

    def test_forward_clock_jump_rejected(self):
        self.assertEqual(inspect_native_clock([(0, frame()), (1, frame(11, 200))]).status, 'unsupported_clock')

    def test_frame_gaps_duplicates_and_reverse_order_rejected(self):
        for second in (0, 2, -1):
            self.assertFalse(inspect_native_clock([(0, frame()), (second, frame(11, 111))]).valid)

    def test_clock_anchor_required_once_and_valid(self):
        for data in (snapshot(0), frame() + anchor(11, 111), anchor(0, math.nan), packet(0, 0x046f, bytes(68))):
            self.assertFalse(inspect_native_clock([(0, data)]).valid)

    def test_late_malformed_record_is_global_failure(self):
        result = read_native_stats([(0, frame() + b'x')], [7], GameTime(105))
        self.assertEqual(result.status, 'malformed_records')

    def test_disordered_record_times_rejected(self):
        self.assertFalse(inspect_native_clock([(0, anchor(0, 0) + packet(10, 1) + packet(9, 1))]).valid)

    def test_initial_zero_clock_pause_allowed(self):
        frames = [(0, anchor(0, 0)), (1, anchor(10, 0)), (2, anchor(20, 1) + snapshot(20))]
        self.assertTrue(inspect_native_clock(frames).valid)


if __name__ == '__main__':
    unittest.main()
