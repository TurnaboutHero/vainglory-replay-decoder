"""Bounded synthetic declaration/refresh models; no native execution."""
import json
from pathlib import Path
import unittest


def refresh_duration(remaining, original, flags):
    return original, (flags | 16) if original < 0 else (flags & ~16)


def expand_duration(remaining, original, incoming):
    if incoming > remaining:
        return incoming, max(original, incoming)
    return remaining, original


class JungleInfusionModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'vg/docs/re_dictionary/buff_status/jungle-candidates.json'
        cls.candidates = json.loads(path.read_text())['entries']

    def test_candidate_indices_are_not_production_decoders(self):
        self.assertEqual(len(self.candidates), 15)
        self.assertTrue(all(not e['production_ready'] for e in self.candidates))
        self.assertEqual(len({e['definition_index'] for e in self.candidates}), 15)

    def test_resource_scoped_capacity_is_not_cooldown_charge(self):
        entries = {e['definition_index']: e for e in self.candidates}
        for index in (220, 1066, 1069):
            self.assertEqual(entries[index]['max_stacks'], 1)
        for index in (283, 284):
            self.assertEqual(entries[index]['max_stacks'], 12)

    def test_refresh_restores_original_and_preserves_other_flags(self):
        self.assertEqual(refresh_duration(20, 150, 0x50), (150, 0x40))
        self.assertEqual(refresh_duration(20, -1, 0x40), (-1, 0x50))

    def test_expand_is_not_refresh(self):
        self.assertEqual(expand_duration(20, 150, 10), (20, 150))
        self.assertEqual(expand_duration(20, 150, 40), (40, 150))
        self.assertEqual(expand_duration(20, 150, 160), (160, 160))
        self.assertEqual(expand_duration(20, 150, 20), (20, 150))

    def test_conditional_real_number_interpolation_endpoints(self):
        # Algebra only: not full IEEE-754/native stat aggregation equivalence.
        for low, high in ((20, 40), (30, 60), (.15, .35), (.075, .15), (10, 20)):
            delta = (high - low) / 11
            intercept = low - delta
            self.assertAlmostEqual(intercept + delta, low)
            self.assertAlmostEqual(intercept + delta * 12, high)


if __name__ == '__main__':
    unittest.main()
