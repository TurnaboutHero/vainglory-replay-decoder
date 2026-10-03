import struct
import unittest
from unittest.mock import patch

from vg.decoder_v2.credit_events import collect_credit_events_by_entity, iter_credit_events
from vg.core.vgr_records import VGRRecordError


def credit(entity_id: int, value: float, action: int) -> bytes:
    return struct.pack(">fIHIfBB4x", 0.0, 16, 0x041D, entity_id, value, action, 0)


class TestDecoderV2CreditEvents(unittest.TestCase):
    def test_iter_credit_events_parses_basic_credit_records(self) -> None:
        data = credit(0x1234, 1.0, 0x0E) + credit(0x1234, 2.5, 0x06)

        with patch("vg.decoder_v2.credit_events.load_frames", return_value=[(7, data)]):
            events = list(iter_credit_events("sample.0.vgr"))

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].frame_idx, 7)
        self.assertEqual(events[0].entity_id_be, 0x1234)
        self.assertEqual(events[0].action, 0x0E)
        self.assertAlmostEqual(events[0].value, 1.0)
        self.assertTrue(events[0].padding_ok)
        self.assertTrue(events[0].value_is_finite)
        self.assertEqual(events[0].raw_record_hex, data[7:19].hex())
        self.assertEqual(events[0].native_record_offset, 0)
        self.assertEqual(events[0].file_offset, 7)
        self.assertEqual(events[1].action, 0x06)

    def test_collect_credit_events_by_entity_groups_records(self) -> None:
        data = credit(0x1234, 1.0, 0x0E) + credit(0x1234, 2.5, 0x06) + credit(0x5678, 1.0, 0x0F)

        with patch("vg.decoder_v2.credit_events.load_frames", return_value=[(0, data)]):
            grouped = collect_credit_events_by_entity("sample.0.vgr")

        self.assertEqual(sorted(grouped.keys()), [0x1234, 0x5678])
        self.assertEqual(len(grouped[0x1234]), 2)
        self.assertEqual(len(grouped[0x5678]), 1)

    def test_embedded_signature_is_not_a_resource_record(self) -> None:
        fake = credit(0x1234, 9000.0, 6)[7:]
        data = struct.pack(">fIH", 0.0, len(fake) + 2, 0x9999) + fake
        with patch("vg.decoder_v2.credit_events.load_frames", return_value=[(0, data)]):
            events = list(iter_credit_events("sample.0.vgr"))
        self.assertEqual(events, [])

    def test_unsupported_layout_is_explicit(self) -> None:
        data = struct.pack(">fIH", 0.0, 2, 0x041D)
        with patch("vg.decoder_v2.credit_events.load_frames", return_value=[(0, data)]):
            with self.assertRaises(VGRRecordError):
                list(iter_credit_events("sample.0.vgr"))


if __name__ == "__main__":
    unittest.main()
