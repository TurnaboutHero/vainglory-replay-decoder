import unittest

from tests.test_native_stats import anchor, snapshot, attribute, packet
from vg.core.native_query import GameTime, RecordTime, select_native_query
from vg.core.native_roster import read_native_roster


class NativeQueryPrefixTests(unittest.TestCase):
    def test_paused_clock_cannot_select_discontinuous_record_subset(self):
        frames = [(0, anchor(0, 0) + snapshot(0) + attribute(9)),
                  (1, anchor(10, 0) + packet(11, 0xffff))]
        timed = select_native_query(frames, GameTime(1))
        self.assertFalse(timed.valid)
        self.assertEqual(timed.status, 'ambiguous_game_time')
        self.assertEqual(list(timed.records()), [])
        self.assertIsNone(timed.record_boundary)
        self.assertEqual(read_native_roster(frames, GameTime(1)).status, 'ambiguous_game_time')
        eof = select_native_query(frames)
        self.assertTrue(eof.valid)
        self.assertEqual(len(list(eof.records())), 5)
        record_cutoff = select_native_query(frames, RecordTime(9))
        self.assertTrue(record_cutoff.valid)
        self.assertEqual(len(list(record_cutoff.records())), 3)

    def test_continuous_clock_inclusive_selection_is_a_prefix(self):
        frames = [(0, anchor(0, 0) + snapshot(0) + attribute(1) + packet(2, 0xffff))]
        query = select_native_query(frames, GameTime(1))
        self.assertTrue(query.valid)
        self.assertEqual([r.timestamp for _, r in query.records()], [0, 0, 1])

    def test_forward_jump_is_clock_failure_but_not_record_order_failure(self):
        frames = [(0, anchor(0, 0) + snapshot(0)),
                  (1, anchor(10, 21) + attribute(11))]
        for cutoff in (None, RecordTime(11)):
            query = select_native_query(frames, cutoff)
            self.assertTrue(query.valid, query.reason)
            self.assertFalse(query.audit.game_time_mapping_valid)
            self.assertEqual(len(list(query.records())), 4)
            self.assertIsNone(query.applied_game_time)
            self.assertIsNone(query.as_of_game_time)
            self.assertIsNone(query.requested_game_time)
        self.assertEqual(select_native_query(frames, GameTime(1)).status, 'unsupported_clock')

    def test_forward_jump_does_not_hide_a_later_backward_reset(self):
        frames = [(0, anchor(0, 0)), (1, anchor(10, 21)), (2, anchor(20, 1))]
        self.assertEqual(select_native_query(frames).status, 'mixed_segments')
