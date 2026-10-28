"""Portable rejection tests plus opt-in exact-client reproduction (no execution)."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from vg.research.lifespring_hp_boundary import CALLS, CHECKS, SHA256, SLICES, inspect

RECEIPT = Path(__file__).resolve().parents[1] / 'vg/docs/amplification_consumers_2026-10-16/LIFESPRING_HP_BOUNDARY.json'


class LifespringBoundaryTests(unittest.TestCase):
    def test_hash_gate_precedes_pe_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'wrong.exe'
            for contents in (b'', b'MZ', bytes(512), b'not the selected client'):
                with self.subTest(contents=contents[:20]):
                    binary.write_bytes(contents)
                    with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
                        inspect(binary)

    def test_published_receipt_tracks_checked_edges(self):
        receipt = json.loads(RECEIPT.read_text())
        self.assertEqual(receipt['binary_sha256'], SHA256)
        self.assertEqual({int(row['site'], 16): int(row['target'], 16)
                          for row in receipt['calls']}, CALLS)
        self.assertEqual({int(row['site'], 16): row['bytes']
                          for row in receipt['instruction_checks']}, CHECKS)
        self.assertEqual({row['name']: (int(row['start'], 16), int(row['end_exclusive'], 16))
                          for row in receipt['slices']}, SLICES)
        self.assertEqual(receipt['vtable_apply'], {'site': '0127c9bc', 'target': '0094f210'})

    def selected_client(self):
        path = os.environ.get('VG_SELECTED_CLIENT')
        if not path:
            self.skipTest('Set VG_SELECTED_CLIENT to the authorized cached exact-build client')
        return Path(path)

    def test_selected_client_reproduces_receipt(self):
        self.assertEqual(inspect(self.selected_client()), json.loads(RECEIPT.read_text()))

    def test_selected_client_one_byte_mutation_rejected(self):
        blob = bytearray(self.selected_client().read_bytes())
        blob[-1] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'mutated.exe'
            changed.write_bytes(blob)
            with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
                inspect(changed)
