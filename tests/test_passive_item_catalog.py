import hashlib
from pathlib import Path
import tempfile
import struct
import unittest
from unittest.mock import patch

from vg.core.cff_resource import CatalogError, CFFResource
from vg.research.passive_item_catalog import decode_item, inspect, read_metadata


class PassiveItemCatalogTests(unittest.TestCase):
    def test_wrong_build_rejected_before_metadata_or_resource_access(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'wrong.bin'
            binary.write_bytes(b'MZ')
            with self.assertRaisesRegex(CatalogError, 'Executable SHA-256'):
                inspect(binary, Path(directory) / 'absent-data', Path(directory) / 'absent-metadata')

    def test_metadata_content_hash_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'metadata.json'
            path.write_bytes(b'{"definitions": {}}')
            with self.assertRaisesRegex(CatalogError, 'metadata SHA-256'):
                read_metadata(path)

    def test_resource_hash_rejected_before_cff_or_executable_parsing(self):
        row = {'resource_sha256': hashlib.sha256(b'expected resource').hexdigest()}
        with self.assertRaisesRegex(CatalogError, 'resource SHA-256 mismatch'):
            decode_item(b'changed resource', b'not a PE', row)

    def test_decoded_declarations_preserve_nonfinite_bits_without_state_claims(self):
        data = bytearray(0x300)
        data[0x38] = 1
        for at, value in ((0x200, b'PassiveKey\0'), (0x220, b'AbilityName\0'), (0x1a0, b'DURATION\0')):
            data[at:at + len(value)] = value
        buff_name = b'Buff_Item_Test\0'
        data[0x240:0x240 + len(buff_name)] = buff_name
        struct.pack_into('<I', data, 0x184, 0x7fc00001)
        decoded = CFFResource(bytes(data), {0x30: 0x140, 0x140: 0x150, 0x150: 0x240,
                              0x11c: 0x200, 0x44: 0x220,
                              0x130: 0x160, 0x160: 0x180, 0x180: 0x1a0},
                              struct.pack('<II', 0, 0xfc7583e1) + b'*Item_Test*\0')
        with patch('vg.research.passive_item_catalog.load_cff', return_value=decoded):
            result = decode_item(b'', b'', {'definition_name': 'Item_Test', 'resource_sha256': '0' * 64})
        self.assertEqual(result['passive_key_name_declared'], 'PassiveKey')
        self.assertEqual(result['inline_ability_name_declared'], 'AbilityName')
        self.assertEqual(result['buffs_declared'], [{'index': 0, 'name': 'Buff_Item_Test'}])
        self.assertEqual(result['properties'][0]['selector_1_declared_bits'], '7fc00001')
        self.assertIsNone(result['properties'][0]['selector_1_declared_value'])
        self.assertNotIn('active_effect', result)


if __name__ == '__main__':
    unittest.main()
