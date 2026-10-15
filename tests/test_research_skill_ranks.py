import unittest,json
from pathlib import Path
from tests.research_models.skill_ranks import *
class Models(unittest.TestCase):
 def test_rank_preservation(self):
  for r in range(8):
   w=set_rank(0xa5a5a5a5,r);self.assertEqual(rank(w),r);self.assertEqual(w&~0x1c00,0xa5a5a5a5&~0x1c00)
 def test_no_saturation(self): self.assertEqual(rank(set_rank(0,8)),0)
 def test_normal_requirements(self):self.assertEqual([requirement(r,0) for r in range(6)],[1,2,4,6,8,255])
 def test_alternate_requirements(self):self.assertEqual([requirement(r,0,True) for r in range(4)],[6,9,12,255])
 def test_base_and_first_flag(self):self.assertEqual(requirement(1,1,False,True),2);self.assertEqual(requirement(0,1),255)
 def test_overdrive(self):self.assertTrue(overdrive_resolved(3,0,True));self.assertFalse(overdrive_resolved(5,0,True));self.assertTrue(overdrive_resolved(6,1))
 def test_missing_slot_edge(self):self.assertTrue(overdrive_missing_slot_after_successful_lookup())
 def test_gate(self):self.assertFalse(apply_grant_gate(0,12,0,0));self.assertFalse(apply_grant_gate(1,5,0,0,True));self.assertTrue(apply_grant_gate(1,6,0,0,True))
 def test_property(self):
  self.assertEqual(property_value(3,90,-10,4),70);self.assertEqual(property_value(5,90,-10,4),54)
  with self.assertRaises(ValueError):property_value(0,0,1,0)
 def test_resource_mapping(self):
  fixture=json.loads((Path(__file__).resolve().parents[1]/'vg/docs/re_dictionary/progression_rewards/skill-fixtures.json').read_text());rows=fixture['selected_heroes'];self.assertEqual(fixture['hero_count'],57);self.assertEqual(fixture['embedded_ability_count'],255)
  r={x['hero']:x for x in rows};self.assertEqual(r['Catherine']['ui_indices'],[1,2,3]);self.assertEqual(r['Ringo']['ui_indices'],[0,1,2]);self.assertEqual(r['Ozo']['ui_indices'][2],8);self.assertEqual(r['Varya']['ui_indices'][2],8)
  self.assertEqual(r['Catherine']['alternate_tier_flags'][3],1)
 def test_corpus_limit(self):
  j=json.loads((Path(__file__).resolve().parents[1]/'vg/docs/re_dictionary/progression_rewards/skill-fixtures.json').read_text())['corpus'];self.assertFalse(j['build_match']);self.assertEqual(j['numeric_concatenation_sha256'],'ae8e37a0eb42f8d323311b20ceee2a1314fe97ae330be24cf30e3ffeca4870f0');self.assertEqual([r['count'] for r in j['counts'] if r['opcode']=='0x43a'],[120])
if __name__=='__main__':unittest.main()
