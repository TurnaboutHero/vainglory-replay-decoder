import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.vgr_records import VGRRecord, iter_records
from tests.test_native_inventory import anchor, consume, packet, snapshot, values
from vg.core.native_inventory import read_native_inventory
from vg.core.native_query import RecordTime


BUILD_SHA256 = '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642'


def record(opcode, payload):
    return next(iter_records(packet(1, opcode, payload)))


class ItemEventTimelineTests(unittest.TestCase):
    def test_sell_request_preserves_actor_instance_and_opaque_suffix(self):
        payload = struct.pack('>II', 0xf1234567, 0xe2345678) + bytes(range(6))
        fields = decode_fields(record(0x044d, payload))
        self.assertEqual(fields['decoding_status'], 'decoded')
        self.assertEqual(fields['native_type'], 'item_sell_request')
        self.assertEqual(fields['native_class'], 'Nuo::Kindred::ActionSellItem')
        self.assertEqual(fields['ref0'], 0xf1234567)
        self.assertEqual(fields['native_item_instance_id'], 0xe2345678)
        self.assertTrue(fields['native_conditional'])
        self.assertEqual(fields['native_semantic_scope'], 'receiver_prefix')
        self.assertEqual(fields['native_evidence_sha256'], BUILD_SHA256)
        self.assertEqual(fields['remaining_hex'], bytes(range(6)).hex())
        self.assertNotIn('ref1', fields)
        for unsupported_claim in ('sold', 'refund', 'quantity', 'gold'):
            self.assertNotIn(unsupported_claim, fields)
        json.dumps(fields, allow_nan=False)

    def test_reject_notification_has_no_invented_reason_or_actor(self):
        for raw_byte in (0, 1, 0xff):
            with self.subTest(raw_byte=raw_byte):
                fields = decode_fields(record(0x048f, bytes([raw_byte]) + b'abcde'))
                self.assertEqual(fields['decoding_status'], 'decoded')
                self.assertEqual(fields['native_type'], 'item_buy_reject_notification')
                self.assertEqual(fields['native_class'], 'Nuo::Kindred::ActionRejectBuyItem_Client')
                self.assertEqual(fields['native_callback'], 'method_onRejectBuyItem')
                self.assertEqual(fields['uninterpreted_bytes'], [raw_byte])
                self.assertEqual(fields['remaining_hex'], b'abcde'.hex())
                self.assertEqual(fields['native_semantic_scope'], 'receiver_prefix')
                self.assertEqual(fields['native_evidence_sha256'], BUILD_SHA256)
                for unsupported_claim in ('ref0', 'ref1', 'reason', 'native_item_instance_id'):
                    self.assertNotIn(unsupported_claim, fields)

    def test_exact_recorded_lengths_do_not_accept_native_serialized_lengths(self):
        for opcode, payload_length in ((0x044d, 14), (0x048f, 6)):
            for size in (*range(payload_length), payload_length + 1, payload_length + 6):
                with self.subTest(opcode=opcode, size=size):
                    fields = decode_fields(record(opcode, bytes(size)))
                    self.assertEqual(fields, {
                        'decoding_status': 'unexpected_content_length',
                        'expected_content_length': payload_length + 2,
                    })

    def test_direct_record_cannot_read_beyond_actual_payload(self):
        for opcode, size in ((0x044d, 14), (0x048f, 6)):
            for actual_size in (0, size - 1, size + 1):
                with self.subTest(opcode=opcode, size=actual_size):
                    supplied = VGRRecord(0, 1.0, size + 2, opcode, memoryview(bytes(actual_size)))
                    self.assertEqual(decode_fields(supplied), {
                        'decoding_status': 'unexpected_payload_length',
                        'expected_payload_length': size,
                    })

    def test_default_timeline_preserves_order_and_filters_by_actor_not_item(self):
        sell_payload = struct.pack('>II', 7, 8) + bytes(6)
        rejected_payload = bytes.fromhex('ff0102030405')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(packet(1, 0x044d, sell_payload) + packet(1, 0x048f, rejected_payload))
            rows = list(iter_timeline(path))
            explicit = list(iter_timeline(path, opcodes={0x044d, 0x048f}))
            by_actor = list(iter_timeline(path, entity_ids={7}))
            by_instance = list(iter_timeline(path, entity_ids={8}))
        self.assertEqual(rows, explicit)
        self.assertEqual([row['opcode'] for row in rows], [0x044d, 0x048f])
        self.assertEqual([row['record_index'] for row in rows], [0, 1])
        self.assertEqual([row['payload_hex'] for row in rows], [sell_payload.hex(), rejected_payload.hex()])
        self.assertEqual([row['opcode'] for row in by_actor], [0x044d])
        self.assertEqual(by_instance, [])

    def test_request_and_notification_do_not_change_possession(self):
        baseline = anchor() + snapshot(items=((458, 2000, 1), (458, 2001, 1)))
        selling = packet(1, 0x044d, struct.pack('>II', 7, 2000) + bytes(6))
        rejecting = packet(2, 0x048f, bytes(6))
        data = baseline + selling + rejecting + consume(3, instance=2000)
        before = read_native_inventory([(0, baseline)], [7], include_transitions=True)
        through_notification = read_native_inventory([(0, data)], [7], cutoff=RecordTime(2),
                                                     include_transitions=True)
        after_consume = read_native_inventory([(0, data)], [7], include_transitions=True)
        self.assertTrue(through_notification.valid, through_notification.reason)
        self.assertEqual(values(before), values(through_notification))
        self.assertEqual(before.players[0].record_boundary, through_notification.players[0].record_boundary)
        self.assertEqual(before.transitions, through_notification.transitions)
        self.assertEqual(values(after_consume), [(458, 2001, 1)])
        self.assertEqual(after_consume.transitions[-1].opcode, 0x044b)

    def test_notifications_never_supply_or_repair_inventory_baseline(self):
        notification = packet(1, 0x048f, bytes(6))
        request = packet(2, 0x044d, struct.pack('>II', 7, 2000) + bytes(6))
        missing = read_native_inventory([(0, anchor() + snapshot(actor=8) + notification + request)], [7])
        self.assertFalse(missing.valid)
        damaged = anchor() + snapshot(items=((458, 2000, 1),)) + packet(1, 0x044b, b'bad')
        before = read_native_inventory([(0, damaged)], [7], include_transitions=True)
        after = read_native_inventory([(0, damaged + notification + request)], [7], include_transitions=True)
        self.assertFalse(before.valid)
        self.assertEqual(before.status, after.status)
        self.assertEqual(before.players, after.players)
        self.assertEqual(before.transitions, after.transitions)

    def test_real_cli_emits_structured_item_rows_and_rejects_truncated_body(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            data = packet(1, 0x048f, bytes(6)) + packet(2, 0x044d, struct.pack('>II', 7, 2000) + bytes(6))
            path.write_bytes(data)
            command = [sys.executable, '-B', '-m', 'vg.analysis.event_timeline', str(path)]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            rows = [json.loads(line) for line in completed.stdout.splitlines()]
            self.assertEqual([row['native_type'] for row in rows],
                             ['item_buy_reject_notification', 'item_sell_request'])
            path.write_bytes(data[:-1])
            truncated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(truncated.returncode, 0)
            self.assertIn('truncated body', truncated.stderr)


if __name__ == '__main__':
    unittest.main()
