import struct
import unittest

from vg.research.windows_client_xrefs import (
    code_xrefs, occurrence_vs, parse_literal_spec,
)


class WindowsClientXrefTests(unittest.TestCase):
    def test_prefix_match_requires_string_boundaries(self):
        prefix = b"%s/%s.%d.vgr"
        data = b"pad\x00" + prefix + b"\x00%s/%s\x00"
        expected = len(b"pad\x00") + len(prefix) + 1
        rows = [{"name": ".rdata", "rva": 0x1000, "vsize": len(data),
                 "offset": 0, "raw_size": len(data)}]
        found = occurrence_vs(data, rows, 0x400000, "%s/%s")
        self.assertEqual([row["file_offset"] for row in found], [expected])

    def test_code_xrefs_returns_reference_site_va(self):
        target = 0x1215EEC
        data = b"\x90" * 4 + struct.pack("<I", target) + b"\x90" * 4
        rows = [{"name": ".text", "rva": 0x1000, "vsize": len(data),
                 "offset": 0, "raw_size": len(data)}]
        self.assertEqual(code_xrefs(data, rows, 0x400000, target), [0x401004])

    def test_literal_spec_parses_optional_va(self):
        self.assertEqual(parse_literal_spec("%s/%s"), ("%s/%s", None))
        self.assertEqual(parse_literal_spec("w@0x1215ea8"), ("w", 0x1215EA8))


if __name__ == "__main__":
    unittest.main()
