"""Raw resource observations are not temporary-resource effect attribution."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tests.test_native_gold import anchor, packet, resource
from tests.test_native_stats import snapshot
from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.native_gold import read_native_gold
from vg.core.native_stats import read_native_stats
from vg.core.vgr_records import iter_records


def raw_resource(timestamp, index, bits, mode=0):
    # Exact existing 14-byte recorded layout; the final two bytes stay opaque.
    payload = struct.pack('>IIBBBB', 7, bits, index, mode, 0xA5, 0x5A) + b'\x12\x34'
    return packet(timestamp, 0x041D, payload)


class ResourceWireObservationTests(unittest.TestCase):
    def assert_raw_only(self, row):
        self.assertEqual(row['native_type'], 'resource_update')
        self.assertIsNone(row['native_stat'])
        for invented in ('barrier', 'fortified_health', 'source_id', 'buff_instance', 'instance_id'):
            self.assertNotIn(invented, row)

    def test_resource4_5_add_and_all_nonzero_modes_remain_raw(self):
        packets = []
        expected = []
        for index in (4, 5):
            for mode in (0, 1, 255):
                timestamp = len(packets) + 1
                wire = raw_resource(timestamp, index, 0xC0100000, mode)
                fields = decode_fields(next(iter_records(wire)))
                self.assert_raw_only(fields)
                self.assertEqual(fields['ref0'], 7)
                self.assertEqual((fields['value'], fields['value_bits']), (-2.25, 0xC0100000))
                self.assertEqual(fields['native_index'], index)
                self.assertEqual(fields['native_operation'], 'add' if mode == 0 else 'set')
                self.assertEqual(fields['native_flags'], [0xA5, 0x5A])
                self.assertEqual(fields['remaining_hex'], bytes((mode, 0xA5, 0x5A, 0x12, 0x34)).hex())
                packets.append(wire)
                expected.append(fields)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.3.vgr'
            path.write_bytes(b''.join(packets))
            rows = list(iter_timeline(path))
        self.assertEqual(len(rows), 6)
        offset = 0
        for i, (row, fields, wire) in enumerate(zip(rows, expected, packets)):
            self.assertEqual((row['frame_idx'], row['record_index'], row['record_offset'], row['timestamp']),
                             (3, i, offset, i + 1))
            self.assertEqual({key: row[key] for key in fields}, fields)
            self.assertEqual(row['payload_hex'], wire[10:].hex())
            offset += len(wire)

    def test_nonfinite_resource_bits_survive_decode_and_timeline_as_json_null(self):
        packets = [raw_resource(i + 1, index, bits, i % 2)
                   for i, (index, bits) in enumerate((index, bits) for index in (4, 5)
                       for bits in (0x7FC12345, 0x7F800000, 0xFF800000))]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.0.vgr'
            path.write_bytes(b''.join(packets))
            rows = list(iter_timeline(path))
        for wire, row in zip(packets, rows):
            fields = decode_fields(next(iter_records(wire)))
            self.assert_raw_only(row)
            self.assertIsNone(fields['value'])
            self.assertIsNone(row['value'])
            self.assertEqual(row['value_bits'], struct.unpack_from('>I', wire, 14)[0])
            json.dumps(row, allow_nan=False)

    def test_mixed_resource4_5_cannot_overwrite_or_taint_confirmed_readers(self):
        base_payload = bytearray(next(iter_records(snapshot(0))).payload)
        struct.pack_into('>ff', base_payload, 286, 600, 900)
        baseline = anchor() + packet(0, 0x03F3, base_payload)
        established = [resource(1, 5, index=6), resource(2, 1000, index=7, mode=1),
                       resource(3, 2, index=11), resource(4, 80, index=14, mode=255)]
        mixed = baseline
        for i, established_wire in enumerate(established):
            mixed += established_wire
            # Invalid as a state amount, yet irrelevant to the established indices.
            mixed += raw_resource(i + 1, 4, (0x7FC12345, 0x7F800000, 0xFF800000, 0xBF800000)[i])
            mixed += raw_resource(i + 1, 5, 0x7F800000, 255)
        clean = baseline + b''.join(established)
        for reader in (read_native_gold, read_native_stats):
            expected = reader([(0, clean)], [7])
            observed = reader([(0, mixed)], [7])
            self.assertTrue(expected.valid, expected.reason)
            self.assertTrue(observed.valid, observed.reason)
            self.assertEqual(observed.players, expected.players)
        gold = read_native_gold([(0, mixed)], [7]).players[0]
        stats = read_native_stats([(0, mixed)], [7]).players[0]
        self.assertEqual((gold.gold_balance, gold.net_worth), (605, 1000))
        self.assertEqual((stats.kills, stats.deaths, stats.assists, stats.minion_kills), (6, 2, 5, 80))


if __name__ == '__main__':
    unittest.main()
