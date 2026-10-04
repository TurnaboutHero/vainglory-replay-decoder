"""Validate research evidence integrity; these tests do not prove gameplay accuracy."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'vg/docs/evidence/2026-10-04-inventory'


def validate_manifest(manifest):
    """Reject unsupported certainty, missing evidence, and ambiguous variant reuse."""
    if manifest['schema_version'] != 'native-inventory-semantics.v1':
        raise ValueError('schema')
    if manifest['client_sha256'] != '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642':
        raise ValueError('build')
    observations = {row['observation_id'] for row in manifest['runtime_observations']}
    opcodes = set()
    for operation in manifest['operations']:
        if operation['opcode'] in opcodes:
            raise ValueError('duplicate opcode')
        opcodes.add(operation['opcode'])
        if not operation['evidence']:
            raise ValueError('missing evidence')
        for name in operation['evidence']:
            path = EVIDENCE / name
            if path.parent != EVIDENCE or not path.is_file() or not path.stat().st_size:
                raise ValueError('invalid evidence reference')
        lengths = set()
        for variant in operation['variants']:
            if variant['length'] in lengths:
                raise ValueError('duplicate variant')
            lengths.add(variant['length'])
            if variant['status'] not in {'static_native', 'observed_unproved', 'runtime_verified'}:
                raise ValueError('variant status')
            if variant['status'] == 'runtime_verified' and variant['runtime_observation'] not in observations:
                raise ValueError('runtime reference missing')
        if operation['native_payload_length'] not in lengths:
            raise ValueError('native variant lost')
        for field in operation['fields']:
            if field['width'] not in {1, 2, 4} or field['endian'] not in {'big', 'none'}:
                raise ValueError('field encoding')
            end = field['offset'] + field['width'] + (field.get('count', 1) - 1) * field.get('stride', 0)
            if field['offset'] < 0 or end > operation['native_payload_length']:
                raise ValueError('field outside native variant')
        if operation['reducer_support'] and operation['runtime_status'] != 'verified':
            raise ValueError('static evidence promoted to runtime support')
    return True


def supported_variant(manifest, opcode, payload):
    """A negative research selection preserves raw input without borrowing offsets."""
    operation = next((row for row in manifest['operations'] if row['opcode'] == opcode), None)
    variant = next((row for row in operation['variants'] if row['length'] == len(payload)), None) if operation else None
    if not variant or variant['status'] != 'runtime_verified':
        return {'supported': False, 'raw_hex': payload.hex(), 'fields': None}
    return {'supported': True, 'raw_hex': payload.hex(), 'fields': operation['fields']}


class InventoryManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((EVIDENCE / 'operations.json').read_text())

    def test_manifest_and_evidence_integrity(self):
        self.assertTrue(validate_manifest(self.manifest))
        for entry in json.loads((EVIDENCE / 'evidence-index.json').read_text()):
            data = (EVIDENCE / entry['path']).read_bytes()
            self.assertTrue(data, entry['path'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'], entry['path'])

    def test_required_operations_present(self):
        self.assertEqual({row['opcode'] for row in self.manifest['operations']},
                         {'03f3', '0437', '0438', '0439', '043d', '0444', '0448', '0449', '044a', '044b', '044c', '044d', '048f'})

    def test_unknown_variant_cannot_inherit_semantics(self):
        raw = bytes.fromhex('000005dc000001ca000007d300001122')
        result = supported_variant(self.manifest, '043d', raw)
        self.assertFalse(result['supported'])
        self.assertIsNone(result['fields'])
        self.assertEqual(result['raw_hex'], raw.hex())

    def test_observed_variants_retained_separately(self):
        expected = {'03f3': {746, 750}, '043d': {12, 14}, '044b': {10, 14}, '044c': {21, 22}, '0448': {4, 6}, '044d': {8, 14}}
        rows = {row['opcode']: row for row in self.manifest['operations']}
        for opcode, lengths in expected.items():
            self.assertTrue(lengths <= {v['length'] for v in rows[opcode]['variants']})

    def test_static_evidence_cannot_enable_reducer(self):
        modified = copy.deepcopy(self.manifest)
        row = next(x for x in modified['operations'] if x['runtime_status'] != 'verified')
        row['reducer_support'] = True
        with self.assertRaisesRegex(ValueError, 'promoted'):
            validate_manifest(modified)

    def test_runtime_variant_requires_actual_reference(self):
        modified = copy.deepcopy(self.manifest)
        modified['operations'][0]['variants'][0].update(status='runtime_verified', runtime_observation='missing')
        with self.assertRaisesRegex(ValueError, 'runtime reference'):
            validate_manifest(modified)

    def test_definition_515_is_original_symbol_not_display_guess(self):
        evidence = json.loads((EVIDENCE / 'definition-515.json').read_text())
        row = next(x for x in evidence['definitions'] if x['index'] == 515)
        self.assertEqual(row['serialized_name'], '*Item_LevelCandy*')
        self.assertEqual(evidence['profile']['build_sha256'], self.manifest['client_sha256'])
        self.assertEqual(evidence['profile']['manifest_sha256'], '7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c')

    def test_c33_raw_examples_are_framed_variants(self):
        examples = json.loads((EVIDENCE / 'c33-minimal-records.json').read_text())
        operations = {row['opcode']: row for row in self.manifest['operations']}
        for row in examples['samples']:
            raw = bytes.fromhex(row['payload_hex'])
            self.assertEqual(len(raw), row['payload_length'])
            self.assertIn(len(raw), {v['length'] for v in operations[row['opcode']]['variants']})
            self.assertGreaterEqual(row['record_offset'], 0)
            self.assertEqual(len(row['source_sha256']), 64)

    def test_instruction_guards_are_complete_relocations(self):
        for guard in json.loads((EVIDENCE / 'guards.json').read_text()):
            data = bytes.fromhex(guard['bytes'])
            self.assertGreaterEqual(len(data), 16)
            for offset in guard['relocations']:
                self.assertLessEqual(offset + 4, len(data))


if __name__ == '__main__':
    unittest.main()
