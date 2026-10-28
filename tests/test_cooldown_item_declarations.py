import struct
import unittest
from types import SimpleNamespace

from vg.core.cff_resource import CatalogError
from vg.research.cooldown_item_declarations import fields, finite_duration


class CooldownDeclarationsTests(unittest.TestCase):
    def fixture(self):
        data = bytearray(512)
        data[0x38] = 1
        data[0x64], data[0x65], data[0xad] = 1, 0, 1
        struct.pack_into('<IIII', data, 0x160, 25, 0x7fc00001, 0x80000000, 2)
        return SimpleNamespace(inst=data, relocations={0x2c: 0x140, 0x140: 0x160},
                               symbol=struct.pack('<I', 0))

    def test_preserves_nonfinite_bits_and_raw_operation(self):
        result = fields(self.fixture())
        row = result['selected_attributes'][0]
        self.assertEqual(row['value_bits'], '7fc00001')
        self.assertIsNone(row['value'])
        self.assertEqual(row['secondary_bits'], '80000000')
        self.assertEqual(row['operation_raw'], 2)
        self.assertNotIn('effective_cooldown', result)

    def test_allocated_empty_external_string_selects_inline_flags(self):
        decoded = self.fixture()
        decoded.relocations[0x3c] = 0x180
        self.assertEqual(fields(decoded)['inline_ability_flags_raw'],
                         {'ability_0x24': 1, 'ability_0x25': 0, 'ability_0x6d': 1})

    def test_named_external_ability_has_no_inline_claim(self):
        decoded = self.fixture()
        decoded.relocations[0x3c] = 0x180
        decoded.inst[0x180:0x182] = b'X\0'
        self.assertIsNone(fields(decoded)['inline_ability_flags_raw'])

    def test_missing_relocation_rejected(self):
        decoded = self.fixture()
        decoded.relocations.pop(0x140)
        struct.pack_into('<I', decoded.inst, 0x140, 123)
        with self.assertRaises(CatalogError):
            fields(decoded)

    def test_nonactive_definition_not_inline_ability(self):
        decoded = self.fixture()
        decoded.inst[0x38] = 0
        self.assertIsNone(fields(decoded)['inline_ability_flags_raw'])

    def test_fraction_is_duration_reduction_not_haste_points(self):
        self.assertEqual(finite_duration(90, reduction=.2), 72)
        self.assertNotEqual(finite_duration(90, reduction=.2), 90 / 1.2)

    def test_conditional_duplicate_fraction_saturates_only_with_supplied_bounds(self):
        # SUBSS(1, float32(.35)) rounds before MULSS: one ULP below58.5.
        result = finite_duration(90, reduction=.2 + .2)
        self.assertEqual(struct.pack('<f', result).hex(), 'ffff6942')
        self.assertAlmostEqual(finite_duration(90, reduction=.4,
                              reduction_bounds=(0, .5)), 54, places=5)
        self.assertEqual(finite_duration(90, reduction=-.1), 90)

    def test_override_still_precedes_flagged_factors(self):
        self.assertEqual(finite_duration(150, -30, .5), 60)
        self.assertEqual(finite_duration(150, -30, .5, 50, reduction=.2), 40)
        self.assertEqual(finite_duration(100, reduction=.2, speed=1.25,
                                        speed_bounds=(.5, 5)), 64)
        self.assertEqual(finite_duration(100, speed=.5, speed_bounds=(.5, 5)), 100)

    def test_nonfinite_witness_rejected_without_altering_extractor(self):
        with self.assertRaises(ValueError):
            finite_duration(90, reduction=float('nan'))
