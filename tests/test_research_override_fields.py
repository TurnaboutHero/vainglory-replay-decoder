import unittest,struct
from tests.research_models.override_fields import *
class TestOverrides(unittest.TestCase):
 def test_prefix(self):
  p=struct.pack('>III',1505,8,2)+b'\x02';d=decode(0x41a,p)
  self.assertEqual((d['actor_raw'],d['original_slot_raw'],d['replacement_slot_raw']),(1505,8,2));self.assertTrue(d['control_nonzero']);self.assertIsNone(d['applied'])
 def test_suffix_and_length(self):
  p=struct.pack('>II',1505,8)+b'123456';self.assertEqual(decode(0x41b,p,'h5810_observed')['opaque_suffix_hex'],b'123456'.hex())
  self.assertEqual(decode(0x41b,p)['status'],'unsupported_layout');self.assertEqual(decode(0x41b,p+b'1','h5810_observed')['status'],'unsupported_layout')
 def test_first_free_first_match_clear_all(self):
  e=[(0,0)]*20;self.assertEqual(insert(e,8,2),0);self.assertEqual(insert(e,8,3),1);self.assertEqual(resolve(e,8),2);clear(e,8);self.assertEqual(resolve(e,8),8);self.assertFalse(e[0][1]&3);self.assertFalse(e[1][1]&3)
 def test_preserve_and_capacity(self):
  e=[(0xc0000000,0xa0)]*20;insert(e,1,2);self.assertEqual(e[0],(0xc0010001,0xa1))
  for i in range(1,20):insert(e,i+1,i+2)
  before=e.copy();self.assertIsNone(insert(e,99,100));self.assertEqual(e,before)
 def test_not_recursive_or_masked_lookup(self):
  e=[(0,0)]*20;insert(e,1,2);insert(e,2,3);self.assertEqual(resolve(e,1),2)
  e=[(0,0)]*20;insert(e,32769,32770);self.assertEqual(resolve(e,32769),32769);self.assertEqual(resolve(e,1),2);clear(e,32769);self.assertEqual(resolve(e,1),2)
if __name__=='__main__':unittest.main()
