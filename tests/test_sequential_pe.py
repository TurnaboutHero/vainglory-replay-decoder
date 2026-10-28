"""The native verifier must reject a different build before decoding offsets."""
import tempfile
from pathlib import Path
import unittest
from vg.research.verify_sequential_pe import verify

class SequentialPEChecks(unittest.TestCase):
    def test_wrong_hash_rejected_before_pe_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "different-build.bin"
            path.write_bytes(b"MZ")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify(path)

    def test_item_inspector_rejects_build_before_resource_access(self):
        from vg.core.cff_resource import CatalogError
        from vg.research.inspect_stack_items import inspect
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "different-build.bin"
            path.write_bytes(b"MZ")
            with self.assertRaisesRegex(CatalogError, "SHA-256"):
                inspect(path, Path(directory) / "absent-assets")
