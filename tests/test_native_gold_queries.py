import math
import struct
import unittest

from tests.test_native_gold import anchor, packet, resource, snapshot
from vg.core.native_gold import read_native_gold
from vg.core.native_stats import GameTime, RecordTime, read_native_stats


class NativeGoldQueryTests(unittest.TestCase):
    def test_paused_clock_eof_differs_from_game_time(self):
        frames = [(0, anchor(0, 100) + snapshot(0, balance=600, worth=600) + resource(10, 25)),
                  (1, anchor(11, 100) + packet(12, 0xffff))]
        eof = read_native_gold(frames, [7])
        timed = read_native_gold(frames, [7], GameTime(101))
        self.assertTrue(eof.valid, eof.reason)
        self.assertFalse(timed.valid)
        self.assertEqual(timed.status, 'ambiguous_game_time')
        self.assertEqual(eof.players[0].net_worth, 625)
        self.assertEqual(timed.players, ())
        self.assertEqual(eof.record_boundary, (1, len(anchor(11, 100))))
        self.assertIsNone(timed.record_boundary)

    def test_out_of_coverage(self):
        frames = [(0, anchor() + snapshot() + packet(10, 0xffff))]
        for cutoff in (GameTime(99), GameTime(111), RecordTime(-1), RecordTime(11)):
            with self.subTest(cutoff=cutoff):
                result = read_native_gold(frames, [7], cutoff)
                self.assertEqual(result.status, 'out_of_coverage')
                self.assertEqual(result.players, ())
                self.assertIsNone(result.record_boundary)

    def test_exact_boundary_and_between_records(self):
        initial = anchor() + snapshot(balance=600, worth=600)
        frames = [(0, initial + resource(2, 0.1) + resource(4, 0.2))]
        for cutoff in (GameTime(102), RecordTime(2), GameTime(103)):
            with self.subTest(cutoff=cutoff):
                result = read_native_gold(frames, [7], cutoff)
                self.assertTrue(result.valid, result.reason)
                self.assertEqual(struct.pack('>f', result.players[0].gold_balance),
                                 struct.pack('>f', 600 + struct.unpack('>f', struct.pack('>f', 0.1))[0]))
                self.assertEqual(result.record_boundary, (0, len(initial)))
                self.assertEqual(result.applied_game_time, 102)
        result = read_native_gold(frames, [7], GameTime(103))
        self.assertEqual(result.requested_game_time, 103)
        self.assertEqual(result.as_of_game_time, 103)

    def test_later_semantic_failure_does_not_poison_earlier_query(self):
        frames = [(0, anchor() + snapshot() + resource(3, math.nan) + packet(10, 0xffff))]
        self.assertTrue(read_native_gold(frames, [7], GameTime(102)).valid)
        self.assertEqual(read_native_gold(frames, [7]).status, 'unsupported_state')

    def test_future_framing_failure_rejects_early_query(self):
        frames = [(0, anchor() + snapshot() + b'bad')]
        self.assertEqual(read_native_gold(frames, [7], GameTime(100)).status, 'malformed_records')

    def test_capture_before_baseline_is_missing(self):
        frames = [(0, anchor() + snapshot(2) + packet(4, 0xffff))]
        self.assertEqual(read_native_gold(frames, [7], GameTime(101)).status, 'missing_baseline')

    def test_record_time_projection_and_common_counter_boundary(self):
        frames = [(0, anchor(0, 100) + snapshot(0) + resource(10, 7)),
                  (1, anchor(11, 100) + packet(12, 0xffff))]
        for cutoff, requested in ((RecordTime(10), 110), (RecordTime(12), 101)):
            result = read_native_gold(frames, [7], cutoff)
            counters = read_native_stats(frames, [7], cutoff)
            self.assertTrue(result.valid, result.reason)
            self.assertEqual(result.requested_game_time, requested)
            self.assertEqual(result.record_boundary, counters.record_boundary)
            self.assertEqual(result.applied_game_time, counters.applied_game_time)

    def test_nonfinite_invalid_cutoff(self):
        frames = [(0, anchor() + snapshot())]
        for cutoff in (GameTime(math.nan), RecordTime(math.inf), 100):
            self.assertEqual(read_native_gold(frames, [7], cutoff).status, 'invalid_query')

    def test_repeated_spawn_cannot_repair_early_bad_state(self):
        frames = [(0, anchor() + snapshot() + resource(1, math.nan) + snapshot(3, 700, 700) + packet(5, 0xffff))]
        self.assertEqual(read_native_gold(frames, [7], GameTime(102)).status, 'unsupported_state')
        self.assertEqual(read_native_gold(frames, [7], GameTime(104)).status, 'unsupported_state')

    def test_nonzero_mode_is_still_native_set(self):
        frames = [(0, anchor() + snapshot(balance=600, worth=600) + resource(1, 123.25, mode=255))]
        result = read_native_gold(frames, [7], RecordTime(1))
        self.assertEqual((result.players[0].gold_balance, result.players[0].net_worth), (123.25, 600))
