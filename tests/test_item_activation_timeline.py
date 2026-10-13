import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from tests.test_native_inventory import anchor, consume, packet, snapshot, values
from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.native_inventory import read_native_inventory
from vg.core.native_query import RecordTime
from vg.core.vgr_records import VGRRecord, iter_records


def activation(mode, actor=7, instance=2000, target=9, x=1.25, y=-2.5):
    return struct.pack('>IIIffB', actor, instance, target, x, y, mode) + b'\xaa'


def fields(opcode, payload):
    return decode_fields(next(iter_records(packet(1, opcode, payload))))


class ItemActivationTimelineTests(unittest.TestCase):
    def test_requests_preserve_arguments_without_actor_attribution(self):
        cases = (
            (0x0448, struct.pack('>I', 0xf1234567) + b'\xaa\xbb'),
            (0x0449, struct.pack('>II', 0x12345678, 0xf1234567) + b'abcdef'),
            (0x044a, struct.pack('>IIII', 0x3f800000, 0x80000000, 0x7fc12345, 0xf1234567) + b'abcdef'),
        )
        for opcode, payload in cases:
            with self.subTest(opcode=opcode):
                result = fields(opcode, payload)
                self.assertEqual(result['decoding_status'], 'decoded')
                self.assertEqual(result['native_type'], 'item_activation_request')
                self.assertEqual(result['native_semantic_scope'], 'serializer_prefix')
                self.assertNotIn('ref0', result)
                self.assertNotIn('ref1', result)
                self.assertNotIn('native_activation_mode', result)
                if opcode == 0x0448:
                    self.assertEqual(result['native_item_instance_id'], 0xf1234567)
                    self.assertEqual(result['remaining_hex'], 'aabb')
                elif opcode == 0x0449:
                    self.assertEqual(result['native_request_arguments'], [0x12345678, 0xf1234567])
                    self.assertNotIn('native_item_instance_id', result)
                    self.assertEqual(result['remaining_hex'], b'abcdef'.hex())
                else:
                    self.assertEqual(result['native_vector_bits'], [0x3f800000, 0x80000000, 0x7fc12345])
                    self.assertEqual(result['native_request_arguments'], [0xf1234567])
                    self.assertNotIn('native_item_instance_id', result)
                    self.assertEqual(result['remaining_hex'], b'abcdef'.hex())
                json.dumps(result, allow_nan=False)

    def test_activation_modes_expose_only_active_target_fields(self):
        for mode in (0, 1, 2):
            with self.subTest(mode=mode):
                result = fields(0x044c, activation(mode, actor=0xf1234567, instance=0xe2345678))
                self.assertEqual(result['decoding_status'], 'decoded')
                self.assertEqual(result['native_type'], 'item_activation_message')
                self.assertEqual(result['ref0'], 0xf1234567)
                self.assertEqual(result['native_item_instance_id'], 0xe2345678)
                self.assertEqual(result['native_activation_mode'], mode)
                self.assertEqual(result['native_target_raw'], 9)
                self.assertEqual(result['native_coordinate_bits'], [0x3fa00000, 0xc0200000])
                self.assertEqual(result['remaining_hex'], 'aa')
                self.assertEqual(result['native_semantic_scope'], 'receiver_prefix')
                self.assertTrue(result['native_conditional'])
                if mode == 0:
                    self.assertEqual(result['ref1'], 9)
                    self.assertNotIn('native_position', result)
                elif mode == 1:
                    self.assertEqual(result['native_position'], [1.25, -2.5])
                    self.assertNotIn('ref1', result)
                else:
                    self.assertNotIn('ref1', result)
                    self.assertNotIn('native_position', result)

    def test_unknown_modes_retain_envelope_without_targeting_claims(self):
        for mode in (3, 0xff):
            result = fields(0x044c, activation(mode))
            self.assertEqual(result['decoding_status'], 'unsupported_mode')
            self.assertEqual(result['native_activation_mode'], mode)
            self.assertEqual(result['ref0'], 7)
            self.assertEqual(result['native_item_instance_id'], 2000)
            self.assertEqual(result['native_target_raw'], 9)
            self.assertNotIn('ref1', result)
            self.assertNotIn('native_position', result)

    def test_float_bits_survive_nonfinite_and_inactive_coordinate_slots(self):
        for mode in (0, 1, 2, 0xff):
            for bits in (0x80000000, 0x7fc12345, 0x7f800000, 0xff800000):
                for offset in (12, 16):
                    with self.subTest(mode=mode, bits=bits, offset=offset):
                        payload = bytearray(activation(mode))
                        struct.pack_into('>I', payload, offset, bits)
                        result = fields(0x044c, bytes(payload))
                        self.assertEqual(result['native_coordinate_bits'][(offset - 12) // 4], bits)
                        if mode == 1:
                            value = result['native_position'][(offset - 12) // 4]
                            if bits == 0x80000000:
                                self.assertEqual(math.copysign(1, value), -1)
                            else:
                                self.assertIsNone(value)
                        else:
                            self.assertNotIn('native_position', result)
                        json.dumps(result, allow_nan=False)

    def test_exact_recorded_lengths_and_direct_record_consistency(self):
        for opcode, size in ((0x0448, 6), (0x0449, 14), (0x044a, 22), (0x044c, 22)):
            for wrong_size in (*range(size), size + 1, size + 6):
                with self.subTest(opcode=opcode, wrong_size=wrong_size):
                    self.assertEqual(fields(opcode, bytes(wrong_size)), {
                        'decoding_status': 'unexpected_content_length', 'expected_content_length': size + 2,
                    })
            for actual_size in (0, size - 1, size + 1):
                direct = VGRRecord(0, 1, size + 2, opcode, memoryview(bytes(actual_size)))
                self.assertEqual(decode_fields(direct), {
                    'decoding_status': 'unexpected_payload_length', 'expected_payload_length': size,
                })

    def test_entity_filter_ignores_item_and_inactive_target_words(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'activation.0.vgr'
            path.write_bytes(packet(1, 0x0448, struct.pack('>I', 7) + bytes(2))
                             + b''.join(packet(2 + mode, 0x044c, activation(mode, instance=8))
                                        for mode in (0, 1, 2)))
            rows = list(iter_timeline(path))
            explicit = list(iter_timeline(path, opcodes={0x0448, 0x0449, 0x044a, 0x044c}))
            by_actor = list(iter_timeline(path, entity_ids={7}))
            by_target = list(iter_timeline(path, entity_ids={9}))
            by_item = list(iter_timeline(path, entity_ids={8}))
        self.assertEqual(rows, explicit)
        self.assertEqual([row['opcode'] for row in rows], [0x0448, 0x044c, 0x044c, 0x044c])
        self.assertEqual([row['record_index'] for row in rows], [0, 1, 2, 3])
        self.assertEqual([row['native_activation_mode'] for row in by_actor], [0, 1, 2])
        self.assertEqual([row['native_activation_mode'] for row in by_target], [0])
        self.assertEqual(by_item, [])
        sentinel = fields(0x044c, activation(0, target=0xffffffff))
        self.assertEqual(sentinel['ref1'], 0xffffffff)

    def test_activation_requests_never_consume_or_repair_inventory(self):
        requests = (packet(1, 0x0448, struct.pack('>I', 2000) + bytes(2))
                    + packet(2, 0x0449, struct.pack('>II', 9, 2000) + bytes(6))
                    + packet(3, 0x044a, struct.pack('>IIII', 0, 0, 0, 2000) + bytes(6))
                    + b''.join(packet(4 + mode, 0x044c, activation(mode)) for mode in (0, 1, 2, 3)))
        baseline = anchor() + snapshot(items=((481, 2000, 2),))
        data = baseline + requests + consume(8)
        before = read_native_inventory([(0, baseline)], [7], include_transitions=True)
        during = read_native_inventory([(0, data)], [7], RecordTime(7), include_transitions=True)
        after = read_native_inventory([(0, data)], [7], include_transitions=True)
        self.assertTrue(during.valid, during.reason)
        self.assertEqual(before.players, during.players)
        self.assertEqual(before.transitions, during.transitions)
        self.assertEqual(values(after), [(481, 2000, 1)])
        self.assertEqual(after.transitions[-1].opcode, 0x044b)
        missing = read_native_inventory([(0, anchor() + requests)], [7])
        self.assertFalse(missing.valid)
        self.assertIsNone(values(missing))
        damaged = baseline + packet(0, 0x044b, b'bad')
        invalid_before = read_native_inventory([(0, damaged)], [7], include_transitions=True)
        invalid_after = read_native_inventory([(0, damaged + requests)], [7], include_transitions=True)
        self.assertFalse(invalid_after.valid)
        self.assertEqual(invalid_before.players, invalid_after.players)
        self.assertEqual(invalid_before.transitions, invalid_after.transitions)

    def test_real_cli_preserves_nonfinite_bits_and_bad_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'activation.0.vgr'
            payload = bytearray(activation(1))
            struct.pack_into('>I', payload, 12, 0x7fc12345)
            path.write_bytes(packet(1, 0x044c, bytes(payload)) + packet(2, 0x044c, activation(0xff)))
            command = [sys.executable, '-B', '-m', 'vg.analysis.event_timeline', str(path)]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            rows = [json.loads(line) for line in completed.stdout.splitlines()]
            self.assertIsNone(rows[0]['native_position'][0])
            self.assertEqual(rows[0]['native_coordinate_bits'][0], 0x7fc12345)
            self.assertEqual(rows[1]['decoding_status'], 'unsupported_mode')
            path.write_bytes(path.read_bytes()[:-1])
            truncated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(truncated.returncode, 0)
            self.assertIn('truncated body', truncated.stderr)


if __name__ == '__main__':
    unittest.main()
