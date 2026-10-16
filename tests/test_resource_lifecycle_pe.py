"""Static receipt/control tests, not native gameplay execution."""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from vg.research.resource_lifecycle_pe import EDGES, SHA256, SPANS, relative_target, verify


class ResourceLifecyclePETests(unittest.TestCase):
    def test_relative_call_and_tail_jump(self):
        for site, target, opcode in EDGES:
            raw = bytes([opcode]) + struct.pack('<i', target-site-5)
            self.assertEqual(relative_target(lambda a, n: raw, site, opcode), target)

    def test_relative_target_wraps_x86(self):
        raw = b'\xe8' + struct.pack('<i', -32)
        self.assertEqual(relative_target(lambda a, n: raw, 0, 0xe8), 0xffffffe5)

    def test_wrong_instruction_and_truncation_rejected(self):
        for raw in (b'', b'\xe8\x00', b'\x90' + b'\x00'*4):
            with self.assertRaises(ValueError):
                relative_target(lambda a, n: raw, 0x858aee, 0xe8)

    def test_unknown_build_rejected_before_pe_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'unrecognised.bin'
            p.write_bytes(b'not the selected build')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify(p)

    def test_committed_receipt_tracks_selected_edges_and_scope(self):
        path = Path(__file__).parents[1] / 'vg/docs/resource_wire_2026-10-16/LIFECYCLE_PE.json'
        receipt = json.loads(path.read_text())
        self.assertEqual(receipt['binary_sha256'], SHA256)
        self.assertEqual(receipt['edges'], [
            {'site': f'{a:08x}', 'target': f'{b:08x}',
             'kind': 'call' if op == 0xe8 else 'tail-jump'} for a, b, op in EDGES])
        self.assertEqual([(r['start'], r['end_exclusive']) for r in receipt['spans']],
                         [(f'{a:08x}', f'{b:08x}') for a, b, _ in SPANS])
        self.assertIn('No native execution', receipt['scope'])
        for row in receipt['spans'] + receipt['selected_checks']:
            self.assertEqual(len(bytes.fromhex(row['sha256'])), 32)


if __name__ == '__main__':
    unittest.main()
