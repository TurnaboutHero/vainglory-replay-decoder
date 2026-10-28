"""Research trace provenance and publication boundaries, using synthetic inputs."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tests.test_event_timeline import packet
from vg.core.replay_output import ReplayOutputError
from vg.core.vgr_records import VGRRecordError
from vg.research.resource_wire_evidence import audit, main


def resource(timestamp, index, bits, mode=0):
    return packet(timestamp, 0x041d,
                  struct.pack('>IIBBBB', 0x80001234, bits, index, mode, 2, 3) + b'\xaa\x55')


class ResourceWireEvidenceTests(unittest.TestCase):
    def test_only_owning_records_have_hashed_raw_witnesses(self):
        hidden = resource(0.5, 5, 0x42c80000)
        prefix = packet(0.0, 0x9999, hidden)
        positive = resource(1.0, 4, 0x42c80000)
        negative = resource(2.0, 4, 0xc2c80000)
        nonfinite = resource(3.0, 5, 0x7fc12345, 255)
        # Serialized content14 is a separate layout, not an observed content16.
        unsupported = packet(4.0, 0x041d, bytes(12))
        data = prefix + positive + positive + negative + nonfinite + unsupported
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.0.vgr'
            path.write_bytes(data)
            result = audit(path)
        self.assertEqual(result['record_count'], 6)
        self.assertEqual(result['sources'][0]['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(result['sources'][0]['bytes'], len(data))
        self.assertEqual(result['resource_layouts'], [
            {'content_length': 14, 'decoding_status': 'unexpected_content_length', 'count': 1},
            {'content_length': 16, 'decoding_status': 'decoded', 'count': 4}])
        self.assertEqual(sum(row['count'] for row in result['counts']), 4)
        self.assertEqual(result['witness_classes'], 3)
        first, _, last = result['witnesses']
        self.assertEqual(first['record_offset'], len(prefix))
        self.assertEqual(first['record_sha256'], hashlib.sha256(positive).hexdigest())
        self.assertEqual(first['actor_ref_raw'], 0x80001234)
        self.assertEqual(first['flags_raw'], [2, 3])
        self.assertEqual(first['opaque_suffix_hex'], 'aa55')
        self.assertEqual(last['operand_bits'], 0x7fc12345)
        self.assertIsNone(last['operand'])
        self.assertIsNone(last['temporary_resource_instance'])
        self.assertIsNone(last['source_actor'])
        self.assertEqual(last['effect_status'], 'unverified')
        json.dumps(result, allow_nan=False)

    def test_later_framing_error_cannot_publish_partial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, output = root / 'synthetic.0.vgr', root / 'result.json'
            path.write_bytes(resource(1.0, 4, 0x42c80000))
            (root / 'synthetic.1.vgr').write_bytes(resource(2.0, 5, 0x42c80000) + b'\0')
            output.write_bytes(b'previous result')
            with self.assertRaises(VGRRecordError):
                main([str(path), '--output', str(output)])
            self.assertEqual(output.read_bytes(), b'previous result')

    def test_output_alias_cannot_replace_replay_or_future_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'synthetic.0.vgr'
            data = resource(1.0, 5, 0x42c80000)
            path.write_bytes(data)
            for output in (path, root / 'synthetic.1.vgr'):
                with self.subTest(output=output.name), self.assertRaises(ReplayOutputError):
                    main([str(path), '--output', str(output)])
            self.assertEqual(path.read_bytes(), data)
            self.assertFalse((root / 'synthetic.1.vgr').exists())


if __name__ == '__main__':
    unittest.main()
