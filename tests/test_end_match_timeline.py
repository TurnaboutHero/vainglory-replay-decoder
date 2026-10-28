from pathlib import Path
import struct
import tempfile
import unittest

from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.vgr_records import iter_records


WINDOWS_SHA = '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642'


def packet(timestamp: float, payload: bytes) -> bytes:
    return struct.pack('>fIH', timestamp, len(payload) + 2, 0x03f1) + payload


class EndMatchTimelineTests(unittest.TestCase):
    def test_exact_end_action_decodes_consumer_fields_and_preserves_raw(self) -> None:
        for reason in (0, 2, 5, 6, 7, 8, 255):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                # Given: one final record with opaque trailing payload byte.
                payload = struct.pack('>IBB', 2, reason, 0xa5)
                path = Path(directory) / 'match.0.vgr'
                path.write_bytes(packet(289.875, payload))
                # When: the default CLI reader selects native event families.
                rows = list(iter_timeline(path))
                # Then: only consumer-proven fields are labeled.
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row['native_type'], 'end_match_action')
                self.assertEqual(row['native_class'], 'Nuo::Kindred::ActionEndMatch')
                self.assertEqual(row['native_winning_team_id'], 2)
                self.assertEqual(row['native_winning_team_raw'], 2)
                self.assertEqual(row['native_end_reason'], reason)
                self.assertEqual(row['native_surrender'], reason == 2)
                self.assertEqual(row['native_evidence'], 'windows-659f9eed')
                self.assertEqual(row['native_evidence_sha256'], WINDOWS_SHA)
                self.assertEqual(row['payload_hex'], payload.hex())
                self.assertEqual(row['remaining_hex'], 'a5')
                self.assertEqual(row['timestamp'], 289.875)
                self.assertNotIn('ref0', row)
                self.assertNotIn('ref1', row)
                self.assertNotIn('match_completed', row)
                self.assertNotIn('winner', row)

    def test_high_bits_preserved_but_native_team_is_low_byte(self) -> None:
        # Given: a full network uint32 with nonzero upper bytes.
        framed = packet(100, struct.pack('>IBB', 0x12345602, 2, 0))
        # When: decode the exact native layout.
        fields = decode_fields(next(iter_records(framed)))
        # Then: constructor truncation does not lose the recorded full value.
        self.assertEqual(fields['native_winning_team_raw'], 0x12345602)
        self.assertEqual(fields['native_winning_team_id'], 2)

    def test_wrong_content_lengths_have_no_native_interpretation(self) -> None:
        for size in (0, 5, 7):
            with self.subTest(size=size):
                fields = decode_fields(next(iter_records(packet(100, bytes(size)))))
                self.assertEqual(fields['decoding_status'], 'unexpected_content_length')
                self.assertEqual(fields['expected_content_length'], 8)
                self.assertFalse(any(key.startswith('native_') for key in fields))

    def test_contradictory_end_requests_remain_independent_operands(self) -> None:
        values = (0x12345602, 0xabcdef01, 0xfedcba02)
        payloads = [struct.pack('>IBB', raw, 2, 0xa5) for raw in values]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(b''.join(packet(100 + i, payload)
                                      for i, payload in enumerate(payloads)))
            rows = list(iter_timeline(path, opcodes=[0x03f1]))
        self.assertEqual([row['native_requested_team_raw'] for row in rows], list(values))
        self.assertEqual([row['native_requested_team_id'] for row in rows], [2, 1, 2])
        for row, raw, payload in zip(rows, values, payloads):
            self.assertEqual(row['native_requested_team_raw'], row['native_winning_team_raw'])
            self.assertEqual(row['native_requested_team_id'], row['native_winning_team_id'])
            self.assertEqual(row['native_result_scope'], 'end_request')
            self.assertEqual(row['payload_hex'], payload.hex())
            self.assertEqual(row['native_requested_team_raw'], raw)
            for unsupported in ('winner', 'certified_winner', 'winning_color', 'team_color',
                                'match_completed', 'request_accepted', 'selected_actor_won'):
                self.assertNotIn(unsupported, row)

    def test_following_record_does_not_supply_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(packet(100, bytes.fromhex('000000020200')) + packet(200, bytes.fromhex('000000010000')))
            rows = list(iter_timeline(path, opcodes=[0x03f1]))
        self.assertEqual([row['timestamp'] for row in rows], [100, 200])

    def test_global_action_does_not_match_player_entity_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(packet(100, bytes.fromhex('000000020200')))
            rows = list(iter_timeline(path, opcodes=[0x03f1], entity_ids=[2]))
        self.assertEqual(rows, [])
