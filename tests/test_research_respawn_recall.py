import unittest,json,hashlib,struct,os
from pathlib import Path
from tests.research_models.respawn_recall import *
BASE=Path(__file__).resolve().parent
class Boundaries(unittest.TestCase):
 def test_teleport(self):
  for state in (1,2,3,4,None):
   self.assertEqual(teleport_gate(True,state),state not in (3,4))
   self.assertTrue(teleport_gate(True,state,True));self.assertFalse(teleport_gate(False,state,True))
 def test_timer_preserves_aux(self):
  self.assertEqual(timer_write({'remaining':2,'aux':99},8,0),{'remaining':8,'aux':99})
  self.assertEqual(timer_write(None,8,0),{'remaining':8,'aux':0})
  self.assertIsNone(timer_write(None,8,1))
 def test_missing_recall(self):
  self.assertEqual(recall_slot([1,2,3],4),0xffffffff)
  self.assertEqual(recall_slot([1,2,3,4],4),3)
  self.assertEqual(recall_slot([1,2,3,4,5],5),4)
 def test_state_gate(self):
  self.assertTrue(state_edge(31,1,0));self.assertFalse(state_edge(1,1,2));self.assertFalse(state_edge(3,1,0));self.assertTrue(state_edge(3,1,2))

 def test_catalog_boundaries(self):
  root=Path(__file__).resolve().parents[1]
  c=json.loads((root/'vg/docs/re_dictionary/catalog.json').read_text())
  entries=[e for e in c['entries'] if 'reviewed-respawn-recall' in e['tags']]
  self.assertEqual(len(entries),8)
  for e in entries:
   self.assertEqual(e['proof']['status'],'bounded')
   self.assertFalse(e['proof']['native_or_server_execution_performed_for_this_catalog'])
   self.assertEqual(e['scope']['recording_build_match'],'unverified')
   self.assertIn('independent_review',e['proof']['validation_kinds'])
 def test_source_manifest(self):
  root=Path(__file__).resolve().parents[1]
  c=json.loads((root/'vg/docs/re_dictionary/catalog.json').read_text())
  m=json.loads((root/'vg/docs/re_dictionary/respawn_recall/SOURCE_MANIFEST.json').read_text())
  self.assertFalse(m['native_execution']);self.assertFalse(m['raw_exports_distributed'])
  self.assertEqual(m['sources'],[s for s in c['sources'] if s['id'].startswith('src-revival-') or s['id']=='src-respawn-recall-report'])
  for s in m['sources']:
   if s['location']['namespace']=='repo':self.assertEqual(hashlib.sha256((root/s['location']['path']).read_bytes()).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
