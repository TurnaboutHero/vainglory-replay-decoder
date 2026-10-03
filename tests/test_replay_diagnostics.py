"""Owner tests for positional observations without final-result inference."""
from hashlib import sha256
import struct

import unittest

from vg.analysis.replay_diagnostics import InputError, diagnose, first_difference
from vg.core.vgr_records import VGRRecordError


def packet(timestamp: float, opcode: int, payload: bytes = b'') -> bytes:
    return struct.pack('>fIH', timestamp, len(payload) + 2, opcode) + payload


class ReplayDiagnosticsTests(unittest.TestCase):
    def test_trailing_same_time_keeps_unrelated_entity_and_original_order(self) -> None:
        # Given: same-time updates on both sides of an opaque terminal anchor.
        update = packet(2, 0x041D, struct.pack('>IfBB', 99, 1, 11, 0) + bytes(4))
        anchor = packet(2, 0x0452)
        data = update + anchor + update + packet(3, 0x041D, bytes(14)) + update
        # When: diagnose the complete record stream.
        result = diagnose([(0, data)])
        # Then: preserve both later observations, even the backward-time one.
        assert [row['sequence'] for row in result.trailing_same_time] == [2, 4]
        assert [row['fields']['ref0'] for row in result.trailing_same_time] == [99, 99]
        assert result.sections[0].sha256 == sha256(data).hexdigest()


    def test_end_error_or_noop_reason_is_retained_without_completion(self) -> None:
        for reason in (5, 6, 7, 8):
            with self.subTest(reason=reason):
                # Given: a native request with validation error or no-op reason.
                data = packet(1, 0x03F1, struct.pack('>IBB', 0x12340102, reason, 0))
                # When: inspect it.
                result = diagnose([(0, data)])
                # Then: preserve the full raw value and reason, without final-result fields.
                fields = result.terminals[0]['fields']
                assert fields['native_winning_team_raw'] == 0x12340102
                assert fields['native_end_reason'] == reason
                assert not any(key in fields for key in ('winner', 'complete', 'accepted_for_index'))


    def test_first_difference_reports_exact_second_record_locator(self) -> None:
        # Given: identical first records and differing body lengths in the second.
        common = packet(1, 0x0452)
        left = diagnose([(4, common + packet(1, 0x048D, b'x'))])
        right = diagnose([(4, common + packet(1, 0x048D, b'xx'))])
        # When: compare ordered signatures.
        result = first_difference(left, right)
        # Then: report the actual second-record location and lengths.
        assert result is not None and result.index == 1
        assert result.left is not None and result.right is not None
        assert (result.left.section, result.left.offset) == (4, len(common))
        assert (result.left.content_length, result.right.content_length) == (3, 4)


    def test_shorter_prefix_is_a_difference(self) -> None:
        # Given: one recording ends after a shared record.
        data = packet(1, 0x048D)
        left, right = diagnose([(0, data)]), diagnose([(0, data + data)])
        # When: compare.
        result = first_difference(left, right)
        # Then: EOF is explicit.
        assert result is not None and result.index == 1 and result.left is None


    def test_malformed_known_layout_is_visible_and_truncation_rejected(self) -> None:
        # Given: a framed but short end request.
        data = packet(1, 0x03F1, b'bad')
        # When: diagnose.
        result = diagnose([(0, data)])
        # Then: no fields are fabricated.
        assert result.undecoded_layouts == ((0x03F1, 5, 'unexpected_content_length', 1),)


    def test_truncation_is_rejected(self) -> None:
        # Given: incomplete outer framing.
        data = packet(1, 0x048D)[:-1]
        # When/Then: framing failure prevents a partial success report.
        with self.assertRaises(VGRRecordError):
            diagnose([(0, data)])


    def test_duplicate_sections_are_rejected(self) -> None:
        # Given: ambiguous section numbering.
        data = packet(1, 0x048D)
        # When/Then: do not silently merge observations.
        with self.assertRaises(InputError):
            diagnose([(0, data), (0, data)])


    def test_structure_comparison_does_not_confuse_payload_change_with_layout(self) -> None:
        # Given: equal layouts whose contents differ, followed by a layout change.
        left = diagnose([(0, packet(1, 0x048D, b'a') + packet(2, 0x0452))])
        right = diagnose([(0, packet(1, 0x048D, b'b') + packet(2, 0x0452, b'x'))])
        # When: compare only opcode and content-length signatures.
        result = first_difference(left, right, structure_only=True)
        # Then: content differences do not obscure the first layout difference.
        assert result is not None and result.index == 1
