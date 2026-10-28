"""Synthetic evidence-boundary checks; these never run a client or prove effects."""
from pathlib import Path
import tempfile
import unittest

from tests.test_player_state_capture import IDENTITY, fixture
from vg.tools.player_state_capture.evidence import export_reference, import_capture
from vg.tools.player_state_capture.guards import CaptureError, require_process, require_session


class ResearchValidationBoundaries(unittest.TestCase):
    def test_active_session_is_not_necessarily_unlocked(self):
        # WTSActive=0 describes connection state, independently of lock flags.
        row = dict(level=1, session_id=1, session_state=0, session_flags=0,
                   bytes=232, expected_bytes=232, os_version=[10, 0, 22631])
        with self.assertRaises(CaptureError) as caught:
            require_session(row)
        self.assertEqual(caught.exception.code, 'session_unavailable')
        require_session(dict(row, session_flags=1))

    def test_unlocked_session_cannot_replace_absent_owned_process(self):
        require_session(dict(level=1, session_id=1, session_state=0, session_flags=1,
                             bytes=232, expected_bytes=232, os_version=[10, 0, 22631]))
        with self.assertRaises(CaptureError) as caught:
            require_process(IDENTITY, IDENTITY, [])
        self.assertEqual(caught.exception.code, 'foreign_process')

    def test_hash_valid_synthetic_capture_is_not_exportable_truth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec_path, _, _ = fixture(root)
            capture = root / 'capture'
            result = import_capture(spec_path, capture)
            self.assertTrue(result['ok'], result)
            self.assertEqual(result['status'], 'observation_only')
            self.assertFalse(result['alignment_verified'])
            with self.assertRaises(CaptureError) as caught:
                export_reference(capture, root / 'unused-manifest.json', root / 'reference')
            # Export first requires restoration evidence, then alignment proof.
            self.assertEqual(caught.exception.code, 'capture_invalid')
            self.assertIn('cleanup_missing', str(caught.exception))
            self.assertFalse((root / 'reference').exists())


if __name__ == '__main__':
    unittest.main()
