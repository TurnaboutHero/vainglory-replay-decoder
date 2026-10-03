import math
import struct
import unittest
from dataclasses import FrozenInstanceError

from vg.core.native_gold import read_native_gold


def packet(time, opcode, payload=b''):
    return struct.pack('>fIH', time, len(payload) + 2, opcode) + payload


def anchor(time=0, game=100):
    data = bytearray(69)
    struct.pack_into('>f', data, 64, game)
    return packet(time, 0x046f, data)


def snapshot(time=0, balance=30000, worth=30000, entity=7, selector=0, extra=0):
    data = bytearray(746 + extra)
    struct.pack_into('>I', data, 8, entity)
    struct.pack_into('>ff', data, 286, balance, worth)
    struct.pack_into('>I', data, 326, selector)
    return packet(time, 0x03f3, data)


def resource(time=1, value=1, index=6, mode=0, entity=7):
    data = bytearray(14)
    struct.pack_into('>If', data, 0, entity, value)
    data[8:10] = bytes((index, mode))
    return packet(time, 0x041d, data)


class NativeGoldTests(unittest.TestCase):
    def read(self, data, ids=(7,)):
        return read_native_gold([(0, data)], ids)

    def assert_state(self, result, balance, worth):
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.status, 'accepted')
        self.assertEqual((result.players[0].gold_balance, result.players[0].net_worth), (balance, worth))

    def assert_withheld(self, result, status):
        self.assertFalse(result.valid)
        self.assertEqual(result.status, status)
        self.assertEqual(result.players, ())
        self.assertIsNone(result.as_of_game_time)

    def test_practice_baseline_and_eof_coverage(self):
        result = self.read(anchor(20, 100) + snapshot(20) + packet(25, 0xffff))
        self.assert_state(result, 30000, 30000)
        self.assertEqual((result.first_game_time, result.last_game_time, result.as_of_game_time), (100, 105, 105))
        self.assertIn('completion not asserted', result.reason)
        with self.assertRaises(FrozenInstanceError):
            result.players[0].gold_balance = 600

    def test_rebaseline_replaces_instead_of_accumulating(self):
        frames = [(0, anchor() + snapshot() + resource(value=100)),
                  (1, anchor(10, 110) + snapshot(10, 25000, 30100, extra=4) + resource(11, 20))]
        self.assert_state(read_native_gold(frames, [7]), 25020, 30120)

    def test_positive_add_changes_balance_and_worth(self):
        self.assert_state(self.read(anchor() + snapshot(balance=600, worth=600) + resource(value=15.5)), 615.5, 615.5)

    def test_smallest_positive_float_is_not_discarded_by_epsilon(self):
        tiny = struct.unpack('>f', bytes.fromhex('00000001'))[0]
        self.assert_state(self.read(anchor() + snapshot(balance=0, worth=0) + resource(value=tiny)), tiny, tiny)

    def test_each_native_store_rounds_to_float32(self):
        data = anchor() + snapshot(balance=16777216, worth=16777216)
        data += resource(1, 1) + resource(2, 1)
        self.assert_state(self.read(data), 16777216, 16777216)

    def test_debit_clamps_balance_without_reducing_worth(self):
        self.assert_state(self.read(anchor() + snapshot(balance=10, worth=600) + resource(value=-20)), 0, 600)

    def test_zero_add_does_not_change_worth(self):
        self.assert_state(self.read(anchor() + snapshot(balance=10, worth=600) + resource(value=-0.0)), 10, 600)

    def test_every_nonzero_mode_is_set_without_worth_credit(self):
        for mode in range(1, 256):
            with self.subTest(mode=mode):
                self.assert_state(self.read(anchor() + snapshot() + resource(value=15, mode=mode)), 15, 30000)

    def test_direct_worth_add_and_set(self):
        data = anchor() + snapshot(balance=30, worth=600) + resource(1, 10, index=7)
        self.assert_state(self.read(data), 30, 610)
        self.assert_state(self.read(data + resource(2, 125.5, index=7, mode=4)), 30, 125.5)
        self.assert_state(self.read(data + resource(2, -1000, index=7)), 30, 0)

    def test_negative_set_clamps_either_resource(self):
        data = anchor() + snapshot() + resource(1, -5, mode=255) + resource(2, -5, index=7, mode=2)
        self.assert_state(self.read(data), 0, 0)

    def test_missing_baseline_not_manufactured_by_updates(self):
        for data in (anchor(), anchor() + resource(), anchor() + resource(mode=1),
                     anchor() + snapshot(selector=1) + resource()):
            with self.subTest(data=data):
                self.assert_withheld(self.read(data), 'missing_baseline')

    def test_nonzero_selector_bypasses_snapshot(self):
        data = anchor() + snapshot() + snapshot(1, math.nan, -1, selector=2)
        self.assert_state(self.read(data), 30000, 30000)

    def test_unknown_actor_resource_and_opcode_are_ignored(self):
        data = anchor() + snapshot() + resource(1, math.nan, index=5)
        data += resource(2, math.nan, entity=8) + packet(3, 0x041c, b'')
        data += packet(4, 0x9999, b'any') + snapshot(5, math.nan, -1, entity=8)
        self.assert_state(self.read(data), 30000, 30000)

    def test_invalid_snapshot_values_withheld(self):
        for balance, worth in ((-1, 5), (5, -1), (math.nan, 5), (5, math.inf), (5, -math.inf)):
            with self.subTest(balance=balance, worth=worth):
                self.assert_withheld(self.read(anchor() + snapshot(balance=balance, worth=worth)), 'unsupported_state')

    def test_nonfinite_resource_values_withheld(self):
        for index in (6, 7):
            for mode in (0, 1):
                for value in (math.nan, math.inf, -math.inf):
                    with self.subTest(index=index, mode=mode, value=value):
                        self.assert_withheld(self.read(anchor() + snapshot() + resource(value=value, index=index, mode=mode)), 'unsupported_state')

    def test_float32_overflow_in_either_state_withheld(self):
        maximum = struct.unpack('>f', bytes.fromhex('7f7fffff'))[0]
        for balance, worth, index in ((maximum, 0, 6), (0, maximum, 6), (0, maximum, 7)):
            with self.subTest(balance=balance, worth=worth, index=index):
                self.assert_withheld(self.read(anchor() + snapshot(balance=balance, worth=worth) + resource(value=maximum, index=index)), 'unsupported_state')

    def test_short_relevant_payloads_withhold_state(self):
        actor = struct.pack('>I', 7)
        records = [packet(1, 0x041d, b''), packet(1, 0x041d, actor),
                   packet(1, 0x041d, actor + bytes(4) + b'\x06'),
                   packet(1, 0x041d, actor + bytes(4) + b'\x06\x00'),
                   packet(1, 0x03f3, b''), packet(1, 0x03f3, bytes(8) + actor)]
        for record in records:
            with self.subTest(record=record):
                result = self.read(anchor() + snapshot() + record)
                self.assert_withheld(result, 'unsupported_state')
                self.assertIn('frame 0 offset', result.reason)

    def test_unsupported_snapshot_size_and_resource_size_withheld(self):
        data = resource()[10:] + b'x'
        self.assert_withheld(self.read(anchor() + snapshot(extra=1)), 'unsupported_state')
        self.assert_withheld(self.read(anchor() + snapshot() + packet(1, 0x041d, data)), 'unsupported_state')

    def test_later_valid_baseline_restores_semantic_failure(self):
        for bad in (snapshot(1, math.nan, 1), resource(1, math.inf), packet(1, 0x041d, b'')):
            with self.subTest(bad=bad):
                self.assert_state(self.read(anchor() + snapshot() + bad + snapshot(2, 12, 34)), 12, 34)

    def test_resource_set_cannot_restore_unknown_state(self):
        data = anchor() + snapshot() + resource(1, math.nan) + resource(2, 1, mode=1)
        data += resource(3, 1, index=7, mode=1)
        self.assert_withheld(self.read(data), 'unsupported_state')

    def test_unknown_actor_short_payload_requires_rebaseline_for_all(self):
        data = anchor() + snapshot(entity=7) + snapshot(entity=8) + packet(1, 0x041d, b'')
        self.assert_withheld(self.read(data + snapshot(2, entity=7), [7, 8]), 'unsupported_state')
        result = self.read(data + snapshot(2, entity=7) + snapshot(3, entity=8), [8, 7])
        self.assertTrue(result.valid, result.reason)
        self.assertEqual([player.entity_id for player in result.players], [7, 8])

    def test_missing_one_actor_withholds_entire_result(self):
        self.assert_withheld(self.read(anchor() + snapshot(), [7, 8]), 'missing_baseline')

    def test_empty_id_list_withheld(self):
        self.assert_withheld(self.read(anchor() + snapshot(), []), 'missing_baseline')

    def test_invalid_or_duplicate_ids_rejected_without_coercion(self):
        for ids in ([True], [False], [0], [-1], [2**32], [7.0], ['7'], [None], [7, 7], [7, '7']):
            with self.subTest(ids=ids):
                self.assert_withheld(self.read(anchor() + snapshot(), ids), 'invalid_query')

    def test_full_unsigned_entity_range_accepted(self):
        result = self.read(anchor() + snapshot(entity=0xffffffff), [0xffffffff])
        self.assert_state(result, 30000, 30000)

    def test_mixed_clock_suppresses_even_later_valid_snapshot(self):
        frames = [(0, anchor() + snapshot()), (1, anchor(10, 1) + snapshot(10))]
        self.assert_withheld(read_native_gold(frames, [7]), 'mixed_segments')

    def test_full_input_malformed_framing_suppresses_state(self):
        self.assert_withheld(self.read(anchor() + snapshot() + b'x'), 'malformed_records')
        self.assert_withheld(read_native_gold([], [7]), 'malformed_records')

    def test_missing_clock_and_frame_gap_rejected(self):
        self.assert_withheld(self.read(snapshot()), 'unsupported_clock')
        frames = [(0, anchor() + snapshot()), (2, anchor(10, 110) + snapshot(10))]
        self.assert_withheld(read_native_gold(frames, [7]), 'mixed_segments')


if __name__ == '__main__':
    unittest.main()
