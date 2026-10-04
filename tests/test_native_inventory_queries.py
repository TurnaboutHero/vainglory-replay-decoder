import math
import unittest

from tests.test_native_inventory import anchor, packet, snapshot, grant, values
from vg.core.native_inventory import read_native_inventory
from vg.core.native_query import GameTime, RecordTime, select_native_query


class NativeInventoryQueryTests(unittest.TestCase):
    def test_exact_and_between_record_boundaries(self):
        initial = anchor() + snapshot()
        frames = [(0, initial + grant(2) + grant(4, instance=2001))]
        for cutoff in (GameTime(102), GameTime(103), RecordTime(2)):
            result = read_native_inventory(frames, [7], cutoff)
            self.assertEqual(values(result), [(458, 2000, 1)])
            self.assertEqual(result.record_boundary, (0, len(initial)))
            self.assertEqual(result.as_of_game_time, 102)

    def test_paused_clock_eof_differs_from_game_time(self):
        frames = [(0, anchor(0, 100) + snapshot() + grant(10)),
                  (1, anchor(11, 100) + packet(12, 0xffff))]
        self.assertEqual(values(read_native_inventory(frames, [7])), [(458, 2000, 1)])
        timed = read_native_inventory(frames, [7], GameTime(101))
        self.assertFalse(timed.valid)
        self.assertEqual(timed.status, 'ambiguous_game_time')
        self.assertIsNone(timed.record_boundary)

    def test_out_of_coverage_and_invalid_time(self):
        frames = [(0, anchor() + snapshot() + packet(10, 0xffff))]
        for cutoff in (GameTime(99), GameTime(111), RecordTime(-1), RecordTime(11)):
            self.assertEqual(read_native_inventory(frames, [7], cutoff).status, 'out_of_coverage')
        for cutoff in (GameTime(math.nan), RecordTime(math.inf), 100):
            self.assertEqual(read_native_inventory(frames, [7], cutoff).status, 'invalid_query')

    def test_future_framing_failure_rejects_earlier_capture(self):
        result = read_native_inventory([(0, anchor() + snapshot() + b'bad')], [7], GameTime(100))
        self.assertEqual(result.status, 'malformed_records')

    def test_future_semantic_failure_does_not_poison_earlier_capture(self):
        frames = [(0, anchor() + snapshot() + grant(3, definition=99999) + packet(10, 0xffff))]
        self.assertTrue(read_native_inventory(frames, [7], GameTime(102)).valid)
        self.assertEqual(read_native_inventory(frames, [7]).status, 'unsupported_state')

    def test_before_baseline_is_unavailable(self):
        frames = [(0, anchor() + snapshot(2) + packet(4, 0xffff))]
        self.assertEqual(read_native_inventory(frames, [7], GameTime(101)).status, 'missing_baseline')

    def test_nonconsecutive_sections_are_not_silently_joined(self):
        frames = [(0, anchor() + snapshot()), (2, anchor(10, 110))]
        self.assertEqual(read_native_inventory(frames, [7]).status, 'mixed_segments')


class OriginalC33NativeInventoryTests(unittest.TestCase):
    def test_every_c33_callback_state_matches_original_native_capture(self):
        import json
        from pathlib import Path
        import struct
        evidence = Path(__file__).resolve().parents[1] / 'vg/docs/evidence/2026-10-04-inventory'
        fixture = json.loads((evidence / 'c33-reducer-fixture.json').read_text())
        expected = json.loads((evidence / 'c33-runtime-matches.json').read_text())['matches']
        frames = []
        for frame in fixture['frames']:
            records = []
            for row in frame['records']:
                payload = bytes.fromhex(row['payload_hex'])
                records.append(struct.pack('>fIH', row['record_time'], len(payload) + 2, row['opcode']) + payload)
            frames.append((frame['section'], b''.join(records)))
        result = read_native_inventory(frames, [1500], include_transitions=True)
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(len(result.transitions), len(expected))
        compact = lambda items: [dict(array_index=x.array_index, definition_id=x.definition_id,
                                      instance_id=x.instance_id, quantity=x.quantity) for x in items]
        for actual, native in zip(result.transitions, expected):
            with self.subTest(observation=native['observation_id']):
                self.assertEqual(actual.section, native['section'])
                self.assertEqual(actual.opcode, int(native['opcode'], 16))
                self.assertEqual(actual.payload_length, native['payload_length'])
                self.assertEqual(compact(actual.after), [x for x in native['after']['items'] if x])
                if native['before'] is not None:
                    self.assertEqual(compact(actual.before), [x for x in native['before']['items'] if x])
        self.assertEqual([x.definition_id for x in result.players[0].visible_items], [515, 464, 499])


if __name__ == '__main__':
    unittest.main()
