import struct,unittest
from tests.research_models.hero_xp import level_delta_payload,ordinary_level_transition,xp_target_ratio
class EvidenceModelTests(unittest.TestCase):
 def test_payload(self):
  r=level_delta_payload(struct.pack('>II',1509,1)+b'\0'*6)
  self.assertEqual(r['requested_level_delta'],1);self.assertIsNone(r['absolute_level']);self.assertIsNone(r['applied_delta'])
 def test_trailer(self):self.assertEqual(level_delta_payload(struct.pack('>II',9,0xffffffff)+b'abcdef')['opaque_trailer_hex'],'616263646566')
 def test_bad_lengths(self):
  for n in [0,7,9,13,15]:
   with self.assertRaises(ValueError):level_delta_payload(b'\0'*n)
 def test_cap(self):self.assertEqual(ordinary_level_transition(11,0xffffffff,500,100)['level'],12)
 def test_cap_exit(self):self.assertFalse(ordinary_level_transition(12,1,500,100)['recalculation_path'])
 def test_zero_not_noop(self):
  r=ordinary_level_transition(5,0,500,100);self.assertTrue(r['recalculation_path']);self.assertEqual(r['xp_progress'],400)
 def test_single_threshold(self):self.assertEqual(ordinary_level_transition(5,3,500,100)['xp_progress'],400)
 def test_initial_level(self):self.assertEqual(ordinary_level_transition(0,1,500,100)['xp_progress'],0)
 def test_floor(self):self.assertEqual(ordinary_level_transition(5,1,50,100)['xp_progress'],0)
 def test_ratio(self):self.assertEqual(xp_target_ratio(25,100),.25);self.assertEqual(xp_target_ratio(150,100),1)
 def test_nonfinite(self):
  for v in [float('nan'),float('inf'),-1]:
   with self.assertRaises(ValueError):ordinary_level_transition(5,1,v,100)
 def test_zero_threshold_withheld(self):
  with self.assertRaises(ValueError):xp_target_ratio(0,0)
if __name__=='__main__':unittest.main()
