"""Bounded synthetic branch models, not native execution or replay decoding."""
import unittest

def expand(mask):
    if mask&1:mask|=2
    if mask&4:mask|=0x2000
    if mask&8:mask|=0x20
    return mask

def aggregate(children):
    assert len(children)<=128
    r=0
    for m in children:r|=m
    return r

def status_reasons(mask,d):
    """Only status branches of00936490; omits other blockers intentionally."""
    r=0
    if mask&0x80 and not d.get(0x3c,0):r|=0x40
    if mask&0x1e==0x1e and not d.get(0x3d,0) and not(d.get(0x34,0) and d.get(0x36,0)):r|=0x80
    if not d.get(0x6c,0):
        if mask&8 and not d.get(0x3e,0) and not(d.get(0x34,0) and d.get(0x38,0)):r|=0x100
        if mask&0x20 and not d.get(0x3f,0) and not(d.get(0x34,0) and d.get(0x39,0)):r|=0x200
    elif mask&0x10:r|=0x100
    if mask&0x51f==0x51f:r|=0x400
    return r

def move_outer(mask,state5=False,override=False):return override or (not state5 and not mask&2)
def slow_bucket(values,cap=1):return min(max([0]+values),max(0,min(1,cap)))
def cleanse_candidates(mode,definition_flags):return [i for i,x in enumerate(definition_flags) if x] if mode else []

class Models(unittest.TestCase):
    def test_expansion(self):self.assertEqual([expand(x) for x in [1,0x23,0x18,0x10,0x1f]],[3,0x23,0x38,0x10,0x203f])
    def test_overlap_survives_removal(self):self.assertEqual(aggregate([expand(0x18),expand(0x10)]),0x38);self.assertEqual(aggregate([expand(0x10)]),0x10)
    def test_last_source_clears(self):self.assertEqual(aggregate([]),0)
    def test_silence_item_split(self):self.assertEqual(status_reasons(8,{0x6c:1}),0);self.assertEqual(status_reasons(0x10,{0x6c:1}),0x100)
    def test_skill_bypass(self):self.assertEqual(status_reasons(8,{0x3e:1}),0);self.assertEqual(status_reasons(8,{0x34:1,0x38:1}),0)
    def test_item_branch_ignores_skill_bypass(self):self.assertEqual(status_reasons(0x10,{0x6c:1,0x3e:1,0x34:1,0x38:1}),0x100)
    def test_root_examples(self):self.assertEqual(status_reasons(expand(1),{}),0);self.assertEqual(status_reasons(0x23,{}),0x200);self.assertEqual(status_reasons(0x23,{0x3f:1}),0)
    def test_stun_composite(self):self.assertEqual(status_reasons(0x1e,{0x6c:1}),0x180);self.assertEqual(status_reasons(0x1c,{0x6c:1}),0x100)
    def test_move_override(self):self.assertFalse(move_outer(3));self.assertTrue(move_outer(3,override=True));self.assertFalse(move_outer(0,state5=True))
    def test_slow_max_not_sum(self):self.assertEqual(slow_bucket([.2,.5]),.5);self.assertEqual(slow_bucket([.5,.5]),.5);self.assertEqual(slow_bucket([.5],.3),.3)
    def test_cleanse_mode_and_metadata(self):self.assertEqual(cleanse_candidates(True,[0,1,0,1]),[1,3]);self.assertEqual(cleanse_candidates(False,[1,1]),[])
if __name__=='__main__':unittest.main(verbosity=2)
