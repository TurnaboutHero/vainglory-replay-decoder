import unittest
from tests.research_models.structure_boundaries import kind_flags,requests_actor_dead,regeneration_gate,observations_die
class Boundaries(unittest.TestCase):
 def test_node_is_not_armory_turret(self):
  self.assertEqual(kind_flags(3,'VainNode'),0x5000)
  self.assertEqual(kind_flags(3,'ArmoryTurret5v5'),0x3000)
 def test_crystal_helper_is_not_crystal(self):
  self.assertEqual(kind_flags(2,'VainCrystal_Home_5v5'),0x9000)
  self.assertEqual(kind_flags(8,'VainCrystal_LightWall'),0)
 def test_unknown_korean_alias_not_inferred(self):self.assertNotEqual(kind_flags(3,'무쇠마루'),0x5000)
 def test_dead_requires_state_three(self):
  for s in (None,0,1,2,4):self.assertFalse(requests_actor_dead(s))
  self.assertTrue(requests_actor_dead(3))
 def test_dead_gates(self):
  self.assertFalse(requests_actor_dead(3,False));self.assertFalse(requests_actor_dead(3,True,False))
 def test_regen_strict_five(self):
  self.assertFalse(regeneration_gate(10,5,True,False,10,100));self.assertTrue(regeneration_gate(10.001,5,True,False,10,100))
 def test_regen_mode_and_health(self):
  for args in [(10,0,False,False,1,100),(10,0,True,True,1,100),(10,0,True,False,100,100)]:self.assertFalse(regeneration_gate(*args))
 def test_raw_source_no_award(self):
  for source in (0,1,0xffffffff,0x80000001):
   row=observations_die(source);self.assertEqual(row['source_raw'],source)
   for k in ('awarded_killer','awarded_team','winner','cleanup_completed'):self.assertIsNone(row[k])
if __name__=='__main__':unittest.main()
