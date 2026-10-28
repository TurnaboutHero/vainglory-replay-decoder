"""Static-anchor and experimental-identifiability tests, never gameplay tests."""
from fractions import Fraction as F
from pathlib import Path
import struct
import tempfile
import unittest
from vg.research.damage_order_native import ANCHORS, check_anchors, verify


class NativeAnchors(unittest.TestCase):
    def test_all_anchors_match(self):
        self.assertEqual(len(check_anchors(lambda a, n: bytes.fromhex(ANCHORS[a]))), 9)

    def test_each_changed_anchor_rejected(self):
        for address in ANCHORS:
            with self.subTest(address=hex(address)):
                def read(a, n):
                    b = bytes.fromhex(ANCHORS[a])
                    return bytes([b[0] ^ 1]) + b[1:] if a == address else b
                with self.assertRaisesRegex(ValueError, f'{address:08x}'):
                    check_anchors(read)

    def test_handoff_and_execution_are_separate_stubs(self):
        table = struct.unpack('<9I', bytes.fromhex(ANCHORS[0x121b690]))
        self.assertEqual(table[5:8], (0x45cd00,) * 3)
        self.assertEqual(table[1:5], (0x45ecd0,) * 4)
        self.assertEqual(bytes.fromhex(ANCHORS[0x45cd00]), b'\x8b\xc1\xc2\x04\x00')

    def test_other_binary_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'different.exe'
            path.write_bytes(b'MZ')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify(path)


class ExperimentIdentifiability(unittest.TestCase):
    """Exact rational hypotheses only. No native/server formula implementation."""
    def test_zero_defense_cannot_separate_two_penetration_hypotheses(self):
        d, a, p = F(100), F(0), F(3, 10)
        self.assertEqual(d / (1 + a * (1-p)/100), d*p + d*(1-p)/(1+a/100))

    def test_positive_defense_separates_two_penetration_hypotheses(self):
        d, a, p = F(100), F(100), F(3, 10)
        reduction = d / (1 + a * (1-p)/100)
        bypass = d*p + d*(1-p)/(1+a/100)
        self.assertEqual(reduction, F(1000, 17))
        self.assertEqual(bypass, F(65))
        self.assertEqual(bypass - reduction, F(105, 17))

    def test_downstream_nonlinearity_does_not_reveal_commuting_order(self):
        for d in (F(1), F(100), F(1000)):
            a, g = F(1, 2), F(13, 20)
            left, right = d*a*g, d*g*a
            self.assertEqual(left, right)
            # An identical later absorption/nonlethal cap cannot separate equal inputs.
            for barrier in (0, 10, 100):
                for cap in (1, 20, 99):
                    self.assertEqual(min(cap, max(0, left-barrier)), min(cap, max(0, right-barrier)))

    def test_intermediate_observation_or_between_stage_clip_can_separate(self):
        d, a, g = F(100), F(1, 2), F(13, 20)
        self.assertNotEqual(d*a, d*g)
        # Hypothetical clip location, NOT a discovered native operation.
        self.assertEqual(min(d*a, 60)*g, F(65, 2))
        self.assertEqual(min(d*g, 60)*a, F(30))


if __name__ == '__main__':
    unittest.main()
