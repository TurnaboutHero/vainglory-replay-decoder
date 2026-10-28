import unittest
from vg.research.stat_stacking_model import effective_layer_value, named_prefix_witness

class StatStackingWitnessTests(unittest.TestCase):
    def test_duplicate_myth_keeps_conditional_marker_coefficient(self):
        rows=[named_prefix_witness(broken_myth=n) for n in range(1,7)]
        self.assertTrue(all(r["shield_prefix_coefficient"]==rows[0]["shield_prefix_coefficient"] for r in rows))
        self.assertEqual([r["ordinary_crystal_strength_declared"] for r in rows],[50,100,150,200,250,300])

    def test_mixed_prefix_does_not_sum_item_tooltip_coefficients(self):
        self.assertAlmostEqual(named_prefix_witness(bonesaw=1,tension_bow=1)["armor_prefix_coefficient"],.3,places=6)
        self.assertAlmostEqual(named_prefix_witness(bonesaw=6)["armor_prefix_coefficient"],.2,places=6)

    def test_target_shred_and_attacker_pen_remain_separate(self):
        self.assertAlmostEqual(effective_layer_value(85,0,-.5,0),42.5)
        self.assertAlmostEqual(named_prefix_witness(bonesaw=1)["armor_prefix_coefficient"],.2,places=6)

    def test_generic_getter_does_not_add_an_invented_clamp(self):
        self.assertEqual(effective_layer_value(0,2,0,0),2)
        self.assertEqual(effective_layer_value(-5,0,0,0),-5)
        self.assertEqual(effective_layer_value(10,20,.5,.5),60)

    def test_invalid_witness_rejected(self):
        for args in ({"bonesaw":-1},{"tension_bow":1.5},{"broken_myth":7}):
            with self.assertRaises(ValueError):named_prefix_witness(**args)
        with self.assertRaises(ValueError):effective_layer_value(float("nan"),0,0,0)
