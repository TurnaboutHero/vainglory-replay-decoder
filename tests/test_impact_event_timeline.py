"""Exact raw impact operands; no accepted damage or resource split is inferred."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tests.test_event_timeline import packet, record
from tests.test_native_gold import anchor
from tests.test_native_stats import snapshot
from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.native_gold import read_native_gold
from vg.core.native_stats import read_native_stats
from vg.core.vgr_records import VGRRecord, iter_records


def impact(source=0xFFFFFFFF, bits=0xC0100000):
    return struct.pack('>IIIHBB', 7, source, bits, 0xABCD, 0x81, 0xFE) + bytes.fromhex('102030405060')


class ImpactEventTimelineTests(unittest.TestCase):
    def assert_no_effect_claim(self, fields):
        for key in ('accepted_damage', 'barrier_decrement', 'fortified_health_decrement',
                    'credited_killer', 'credited_source', 'native_stat', 'buff_instance', 'game_timestamp'):
            self.assertNotIn(key, fields)

    def test_exact_raw_fields_and_source_roles_preserve_sentinels(self):
        for source in (0, 2007, 0x80001234, 0xFFFFFFFF):
            with self.subTest(source=source):
                fields = decode_fields(record(0x041E, impact(source)))
                self.assertEqual(fields['decoding_status'], 'decoded')
                self.assertEqual((fields['ref0'], fields['ref1']), (7, source))
                self.assertEqual((fields['value'], fields['value_bits']), (-2.25, 0xC0100000))
                self.assertEqual(fields['native_code_raw'], 0xABCD)
                self.assertEqual((fields['native_byte14_raw'], fields['native_byte15_raw']), (0x81, 0xFE))
                self.assertEqual(fields['remaining_hex'], '102030405060')
                self.assertEqual(fields['native_type'], 'impact_health_action')
                self.assertEqual(fields['native_class'], 'Nuo::Kindred::ActionImpactHealth')
                self.assertEqual(fields['native_semantic_scope'], 'raw_impact_operand')
                self.assertEqual(fields['native_evidence_sha256'],
                    'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc')
                self.assert_no_effect_claim(fields)

    def test_wrong_lengths_and_inconsistent_payload_never_decode_prefix(self):
        for size in (0, 8, 15, 16, 21, 23, 24, 32):
            with self.subTest(size=size):
                fields = decode_fields(record(0x041E, bytes(size)))
                self.assertEqual(fields['decoding_status'], 'unexpected_content_length')
                self.assertEqual(fields['expected_content_length'], 24)
                self.assertNotIn('ref0', fields)
                self.assertNotIn('value', fields)
        malformed = VGRRecord(0, 1, 24, 0x041E, memoryview(impact()[:-1]))
        fields = decode_fields(malformed)
        self.assertEqual(fields['decoding_status'], 'unexpected_payload_length')
        self.assertEqual(fields['expected_payload_length'], 22)
        self.assertNotIn('ref0', fields)

    def test_nonfinite_bits_are_retained_without_nonstandard_json_numbers(self):
        for bits in (0x7FC12345, 0x7F800000, 0xFF800000):
            with self.subTest(bits=hex(bits)):
                fields = decode_fields(record(0x041E, impact(bits=bits)))
                self.assertIsNone(fields['value'])
                self.assertEqual(fields['value_bits'], bits)
                self.assert_no_effect_claim(fields)
                json.dumps(fields, allow_nan=False)

    def test_timeline_owns_timestamp_offsets_and_ignores_nested_marker(self):
        hidden = packet(999, 0x041E, impact(source=123))
        prefix = packet(1, 0x9999, hidden)
        first = packet(2, 0x041E, impact(source=2007))
        last = packet(3, 0x041E, impact(source=0))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'synthetic.2.vgr'
            path.write_bytes(prefix + first)
            (root / 'synthetic.10.vgr').write_bytes(last)
            rows = list(iter_timeline(path, opcodes={0x041E}))
            by_source = list(iter_timeline(path, opcodes={0x041E}, entity_ids={2007}))
            self.assertEqual(by_source, rows[:1])
            self.assertEqual(list(iter_timeline(path, opcodes={0x041E}, entity_ids={123})), [])
        self.assertEqual([(r['frame_idx'], r['record_index'], r['record_offset'], r['timestamp']) for r in rows],
                         [(2, 1, len(prefix), 2), (10, 0, 0, 3)])
        self.assertEqual(rows[0]['payload_hex'], impact(source=2007).hex())
        self.assertEqual(rows[1]['payload_hex'], impact(source=0).hex())
        for row in rows:
            self.assert_no_effect_claim(row)

    def test_raw_impact_operands_do_not_mutate_established_gold_or_counters(self):
        payload = bytearray(next(iter_records(snapshot(0))).payload)
        struct.pack_into('>ff', payload, 286, 600, 900)
        clean = anchor() + packet(0, 0x03F3, payload)
        mixed = clean + b''.join(packet(i + 1, 0x041E, impact(bits=bits))
            for i, bits in enumerate((0x447A0000, 0xC47A0000, 0x7FC12345, 0x7F800000)))
        for reader in (read_native_gold, read_native_stats):
            expected = reader([(0, clean)], [7])
            observed = reader([(0, mixed)], [7])
            self.assertTrue(expected.valid, expected.reason)
            self.assertTrue(observed.valid, observed.reason)
            self.assertEqual(observed.players, expected.players)


if __name__ == '__main__':
    unittest.main()
