import unittest

from tests.test_native_stats import anchor, attribute, packet, resource, snapshot
from vg.core.native_stats import GameTime, RecordTime, read_native_stats


def paused_frames(update: bytes) -> list[tuple[int, bytes]]:
    return [(0, anchor(0, 100) + snapshot(0) + update),
            (1, anchor(11, 100) + packet(12, 0xffff))]


class NativeStatsQueryTests(unittest.TestCase):
    def test_eof_includes_updates_before_a_paused_clock_anchor(self) -> None:
        # Given an update projected beyond the final frame's game time.
        frames = paused_frames(resource(10, value=9))

        # When reading recorded EOF.
        result = read_native_stats(frames, [7])

        # Then the recorded update is included.
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].assists, 12)
        self.assertEqual(result.as_of_game_time, 101)
        self.assertIsNone(result.requested_game_time)

    def test_eof_withholds_unsupported_update_before_paused_anchor(self) -> None:
        # Given a relevant unsupported update with a projected time of 110.
        frames = paused_frames(attribute(10, layer=3))

        # When reading EOF, whose final projected time is only 101.
        result = read_native_stats(frames, [7])

        # Then the unsupported state cannot silently become accepted.
        self.assertEqual(result.status, 'unsupported_state')
        self.assertFalse(result.valid)
        self.assertEqual(result.players, ())

    def test_eof_applies_snapshot_and_update_in_record_order(self) -> None:
        # Given a later snapshot before a paused anchor and a subsequent ADD.
        frames = [(0, anchor(0, 100) + snapshot(0)
                   + snapshot(10, values=(6, 2, 40, 100))),
                  (1, anchor(11, 100) + resource(12, value=2))]

        # When restoring EOF.
        result = read_native_stats(frames, [7])

        # Then the later snapshot replaces the baseline before the ADD.
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].assists, 42)

    def test_explicit_game_cutoff_keeps_game_time_filter(self) -> None:
        # Given an update beyond the explicit game-time cutoff.
        frames = paused_frames(resource(10, value=9))

        # When querying game time 101.
        result = read_native_stats(frames, [7], GameTime(101))

        # Then the update at projected game time 110 remains excluded.
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].assists, 3)
        self.assertEqual(result.requested_game_time, 101)

    def test_explicit_record_cutoff_keeps_record_time_filter(self) -> None:
        # Given an update at record time 10 and a paused next anchor.
        frames = paused_frames(resource(10, value=9))
        for cutoff, assists, game_time in ((0, 3, 100), (10, 12, 110), (12, 12, 101)):
            with self.subTest(cutoff=cutoff):
                # When querying within existing record/game coverage.
                result = read_native_stats(frames, [7], RecordTime(cutoff))

                # Then record time controls inclusion and mapping is retained.
                self.assertTrue(result.valid, result.reason)
                self.assertEqual(result.players[0].assists, assists)
                self.assertEqual(result.requested_game_time, game_time)

    def test_record_cutoff_outside_record_coverage_is_rejected(self) -> None:
        frames = paused_frames(resource(10, value=9))
        for cutoff in (-1, 13):
            with self.subTest(cutoff=cutoff):
                result = read_native_stats(frames, [7], RecordTime(cutoff))
                self.assertEqual(result.status, 'out_of_coverage')
                self.assertFalse(result.valid)

    def test_eof_accepts_clock_endpoint_below_first_endpoint(self) -> None:
        frames = [(0, anchor(0, 100) + snapshot(0)),
                  (1, anchor(1, 99.5) + resource(1, value=9))]
        result = read_native_stats(frames, [7])
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].assists, 12)
        self.assertEqual(result.as_of_game_time, 99.5)

    def test_invalid_identity_types_and_ranges_return_invalid_query(self) -> None:
        # Given valid bytes and malformed identities, including mixed/unhashable inputs.
        frames = [(0, anchor(0, 0) + snapshot(0, entity=1))]
        for ids in ([True], [False], [1.0], [0], [-1], [0x100000000],
                    ['1'], [None], [1, '1'], [1, None], [1, []], [1, {}]):
            with self.subTest(ids=ids):
                # When parsing identity input at the reader boundary.
                result = read_native_stats(frames, ids)

                # Then it returns a withheld query result without coercion or exceptions.
                self.assertEqual(result.status, 'invalid_query')
                self.assertFalse(result.valid)
                self.assertEqual(result.players, ())

    def test_duplicate_identities_return_invalid_query(self) -> None:
        # Given repeated identities rather than a unique roster.
        frames = [(0, anchor(0, 0) + snapshot(0, entity=1))]

        # When reading the duplicated roster.
        result = read_native_stats(frames, [1, 1])

        # Then it is rejected rather than silently deduplicated.
        self.assertEqual(result.status, 'invalid_query')
        self.assertFalse(result.valid)
        self.assertEqual(result.players, ())

    def test_unsigned_identity_boundaries_are_accepted_and_sorted(self) -> None:
        # Given both boundaries of the supported positive uint32 range.
        frames = [(0, anchor(0, 0) + snapshot(0, entity=1)
                   + snapshot(0, entity=0xffffffff))]

        # When supplying the unique roster in reverse order.
        result = read_native_stats(frames, [0xffffffff, 1])

        # Then the complete scoreboard is returned in deterministic order.
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(tuple(player.entity_id for player in result.players), (1, 0xffffffff))

    def test_empty_identities_retain_missing_baseline_status(self) -> None:
        # Given a valid frame and an empty roster.
        frames = [(0, anchor(0, 0) + snapshot(0))]

        # When reading without identities.
        result = read_native_stats(frames, [])

        # Then the established missing-baseline outcome is retained.
        self.assertEqual(result.status, 'missing_baseline')
        self.assertFalse(result.valid)
        self.assertEqual(result.players, ())


if __name__ == '__main__':
    unittest.main()
