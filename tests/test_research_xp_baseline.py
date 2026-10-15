import struct,unittest
from tests.research_models.xp_baseline import *
class BoundedTests(unittest.TestCase):
 def payload(self):
  p=bytearray(746)
  for o,v in [(294,1.),(318,10.5),(322,68.)]:struct.pack_into('>f',p,o,v)
  struct.pack_into('>I',p,8,1500);struct.pack_into('>I',p,705,1);return p
 def test_offsets(self):
  q=snapshot_projection(self.payload());self.assertEqual((q['base_level'],q['xp_progress'],q['base_xp_required']),(1,10.5,68));self.assertFalse(q['state_accepted']);self.assertIsNone(q['effective_level'])
 def test_gate(self):
  p=self.payload();struct.pack_into('>I',p,326,1)
  with self.assertRaises(ValueError):snapshot_projection(p)
 def test_loop_retained(self):
  p=self.payload();struct.pack_into('>I',p,705,4);self.assertEqual(snapshot_projection(p)['post_snapshot_level_loop'],4)
 def test_length(self):
  with self.assertRaises(ValueError):snapshot_projection(b'\0'*745)
 def test_four_layers(self):self.assertEqual(effective_unclamped((100,10,.5,1)),180)
 def test_add_set(self):
  a=layer_operation((100,0,0,0),0,16,0);self.assertEqual(a[0],116);self.assertEqual(layer_operation(a,0,84,2)[0],84)
 def test_float32_add(self):self.assertEqual(xp_operation(16777216,1,0),16777216)
 def test_float32_vs_double(self):self.assertNotEqual(xp_operation(0.1,0.2,0),0.1+0.2)
 def test_negative_floor(self):self.assertEqual(xp_operation(5,-10,0),0)
 def test_delta_once(self):self.assertEqual(level_step(5,500,100,3),(8,400))
 def test_cap_progress_retained(self):self.assertEqual(level_step(12,500,100,1),(12,500))
 def test_zero_recalculation(self):self.assertEqual(level_step(5,500,100,0),(5,400))
 def test_nonfinite(self):
  for v in [float('nan'),float('inf'),1e100]:
   with self.assertRaises(ValueError):f32(v)
if __name__=='__main__':unittest.main()
