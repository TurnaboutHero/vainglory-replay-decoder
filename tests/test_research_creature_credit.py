"""Existing raw death-parser guardrails; never assign an awarded killer."""
import struct
import unittest
from vg.analysis.native_event_fields import decode_fields
from vg.core.vgr_records import VGRRecord


class CreatureCreditGuards(unittest.TestCase):
    def decode(self, payload):
        return decode_fields(VGRRecord(0, 1.0, len(payload) + 2, 0x430, memoryview(payload)))

    def test_unsigned_ids_remain_raw(self):
        for source in (0, 1, 0x80000001, 0xffffffff):
            result = self.decode(struct.pack('>II', 0x80000002, source) + b'ABCDEF')
            self.assertEqual(result['native_victim_id'], 0x80000002)
            self.assertEqual(result['native_source_raw'], source)

    def test_opaque_suffix_is_retained(self):
        self.assertEqual(self.decode(struct.pack('>II', 7, 9) + b'ABCDEF')['remaining_hex'], b'ABCDEF'.hex())

    def test_raw_source_does_not_create_award_fields(self):
        result = self.decode(struct.pack('>II', 7, 9) + b'ABCDEF')
        self.assertNotIn('killer', result)
        self.assertNotIn('credited_killer', result)

    def test_unsupported_lengths_fail_closed(self):
        for length in (0, 8, 13, 15):
            self.assertNotEqual(self.decode(bytes(length))['decoding_status'], 'decoded')


if __name__ == '__main__':
    unittest.main()
