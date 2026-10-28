"""Bounded wire-field tests; no replayed timer/charge state claims."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from vg.analysis.event_timeline import decode_fields, iter_timeline
from vg.core.vgr_records import VGRRecord, iter_records
from tests.test_native_inventory import anchor, packet, snapshot
from vg.core.native_inventory import read_native_inventory

SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'


def record(opcode, payload):
    return next(iter_records(packet(1, opcode, payload)))


def change(mode=0, operand=0x3f800000):
    return struct.pack('>IIIBB', 0xf1234567, 0xe2345678, operand, mode, 0xa5)


def sync(raw=0, value=0x3f800000, config=0x40000000):
    return struct.pack('>IIII6B', 0xf1234567, 0xe2345678, value, config,
                       raw, raw, raw, raw, raw, raw)


class CooldownEventTimelineTests(unittest.TestCase):
    def test_change_modes_namespaces_unsigned_and_suffix(self):
        for opcode in (0x0428, 0x0429):
            for mode in (0, 1, 2, 255):
                fields = decode_fields(record(opcode, change(mode, 0xffffffff)))
                self.assertEqual(fields['ref0'], 0xf1234567)
                self.assertEqual(fields['native_mode_raw'], mode)
                self.assertEqual(fields['native_operation'], 'relative' if mode == 0 else 'direct')
                self.assertEqual(fields['remaining_hex'], 'a5')
                self.assertEqual(fields['native_evidence_sha256'], SHA256)
                self.assertEqual(fields['native_semantic_scope'], 'static_event_fields')
                self.assertNotIn('ref1', fields)
                if opcode == 0x0428:
                    self.assertEqual(fields['native_lookup_key'], 0xe2345678)
                    self.assertNotIn('native_ability_slot_index', fields)
                    self.assertEqual(fields['value_bits'], 0xffffffff)
                    self.assertIsNone(fields['value'])
                else:
                    self.assertEqual(fields['native_ability_slot_index'], 0xe2345678)
                    self.assertNotIn('native_lookup_key', fields)
                    self.assertEqual(fields['native_operand_raw'], 0xffffffff)
                    self.assertNotIn('value', fields)
                json.dumps(fields, allow_nan=False)

    def test_sync_individual_bytes_masks_and_equality_not_truthiness(self):
        for raw in (0, 1, 2, 255):
            fields = decode_fields(record(0x048a, sync(raw)))
            self.assertEqual(fields['value'], 1.0)
            self.assertEqual(fields['native_config_value'], 2.0)
            self.assertEqual(fields['native_lookup_key'], 0xe2345678)
            self.assertEqual(fields['native_evidence_sha256'], SHA256)
            self.assertNotIn('ref1', fields)
            for offset in range(16, 22):
                self.assertEqual(fields[f'native_byte{offset}_raw'], raw)
            self.assertEqual(fields['native_byte18_masked'], raw & 3)
            for offset in (19, 20, 21):
                self.assertEqual(fields[f'native_byte{offset}_equals_one'], raw == 1)
            for unsupported in ('remaining_seconds', 'resulting_charges', 'ability_name',
                                'native_item_instance_id', 'success'):
                self.assertNotIn(unsupported, fields)

    def test_sync_offsets_are_independent(self):
        payload = sync()[:16] + bytes((5, 17, 254, 1, 2, 255))
        fields = decode_fields(record(0x048a, payload))
        self.assertEqual([fields[f'native_byte{i}_raw'] for i in range(16, 22)],
                         [5, 17, 254, 1, 2, 255])
        self.assertEqual(fields['native_byte18_masked'], 2)
        self.assertEqual([fields[f'native_byte{i}_equals_one'] for i in (19, 20, 21)],
                         [True, False, False])
        self.assertEqual(fields['native_charge_setter_input'], 5)
        self.assertEqual(fields['native_base_charge_creation_input'], 17)

    def test_sync_input_roles_do_not_determine_application_or_retained_state(self):
        first = sync(value=0, config=0x42960000)[:16] + bytes((3, 4, 2, 1, 0, 1))
        later = sync(value=0, config=0x42a00000)[:16] + bytes((2, 7, 1, 0, 1, 0))
        for payload, config_bits, charge, base in (
            (first, 0x42960000, 3, 4), (later, 0x42a00000, 2, 7),
        ):
            fields = decode_fields(record(0x048a, payload))
            self.assertEqual(fields['native_config_value_bits'], config_bits)
            self.assertEqual(fields['native_charge_setter_input'], charge)
            self.assertEqual(fields['native_base_charge_creation_input'], base)
            self.assertEqual(fields['native_config_apply_scope'], 'new_state_only')
            self.assertEqual(fields['native_charge_apply_scope'], 'existing_or_new_state')
            self.assertEqual(fields['native_input_apply_order'],
                             ['timer_input', 'charge_setter_input'])
            self.assertEqual(fields['native_semantic_scope'], 'static_event_fields')
            for unsupported in ('state_created', 'applied_config', 'remaining_seconds',
                                'resulting_charges', 'ready', 'success'):
                self.assertNotIn(unsupported, fields)
            self.assertEqual(fields['value_bits'], 0)
            json.dumps(fields, allow_nan=False)

    def test_all_float_bits_preserved_and_nonfinite_json_null(self):
        for bits in (0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000,
                     0xff800000, 0x7fc12345, 0x7f812345):
            for opcode, payload in ((0x0428, change(operand=bits)),
                                    (0x048a, sync(value=bits, config=bits))):
                fields = decode_fields(record(opcode, payload))
                self.assertEqual(fields['value_bits'], bits)
                if bits & 0x7f800000 == 0x7f800000:
                    self.assertIsNone(fields['value'])
                if opcode == 0x048a:
                    self.assertEqual(fields['native_config_value_bits'], bits)
                    self.assertEqual(fields['native_config_value'], fields['value'])
                json.dumps(fields, allow_nan=False)

    def test_exact_content_and_actual_payload_lengths(self):
        for opcode, size in ((0x0428, 14), (0x0429, 14), (0x048a, 22)):
            for length in (*range(size), size + 1, size + 8):
                self.assertEqual(decode_fields(record(opcode, bytes(length))), {
                    'decoding_status': 'unexpected_content_length',
                    'expected_content_length': size + 2})
                supplied = VGRRecord(0, 1.0, size + 2, opcode, memoryview(bytes(length)))
                self.assertEqual(decode_fields(supplied), {
                    'decoding_status': 'unexpected_payload_length',
                    'expected_payload_length': size})

    def test_default_api_cli_order_owner_filter_and_truncation(self):
        payloads = [(0x0428, change()), (0x0429, change(1, 4)), (0x048a, sync(255))]
        data = b''.join(packet(i, op, payload) for i, (op, payload) in enumerate(payloads))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'match.0.vgr'
            path.write_bytes(data)
            rows = list(iter_timeline(path))
            self.assertEqual([r['opcode'] for r in rows], [op for op, _ in payloads])
            self.assertEqual([r['payload_hex'] for r in rows], [p.hex() for _, p in payloads])
            self.assertEqual(rows, list(iter_timeline(path, entity_ids={0xf1234567})))
            self.assertEqual([], list(iter_timeline(path, entity_ids={0xe2345678})))
            command = [sys.executable, '-B', '-m', 'vg.analysis.event_timeline', str(path)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([json.loads(line) for line in result.stdout.splitlines()], rows)
            path.write_bytes(data[:-1])
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('truncated body', result.stderr)

    def test_event_observations_do_not_mutate_inventory(self):
        baseline = anchor() + snapshot()
        events = packet(1, 0x0428, change()) + packet(2, 0x0429, change()) + packet(3, 0x048a, sync())
        before = read_native_inventory([(0, baseline)], [7], include_transitions=True)
        after = read_native_inventory([(0, baseline + events)], [7], include_transitions=True)
        self.assertEqual(before.players, after.players)
        self.assertEqual(before.transitions, after.transitions)


if __name__ == '__main__':
    unittest.main()
