"""Finite normal-range models of selected arithmetic, not game execution."""
import unittest

def charge_delta(base,mod,current,delta):
 assert -128<=mod+delta<=127 and 0<=base+mod+delta<=255
 mod+=delta
 if delta>0:current=min(current+delta,base+mod)
 elif current>base+mod:current=base+mod
 return mod,current

def duration(base,add=0,mul=1,override=-1,cdr=None,speed=None):
 d=override if override>=0 else (base+add)*mul
 if cdr is not None:d*=1-min(cdr,0.3499999940395355)
 if speed is not None:d/=max(speed,1)
 return d
class Checks(unittest.TestCase):
 def test_charge_apply_remove(self):
  self.assertEqual(charge_delta(2,0,2,1),(1,3));self.assertEqual(charge_delta(2,1,3,-1),(0,2))
 def test_capacity_remove_preserves_spent(self):self.assertEqual(charge_delta(2,1,1,-1),(0,1))
 def test_scout_conditional(self):
  self.assertEqual(charge_delta(2,0,2,1),(1,3));self.assertEqual(duration(150,add=-30),120)
  self.assertEqual(charge_delta(2,1,3,2),(3,5));self.assertEqual(duration(150,add=-60),90)
 def test_3v3_conditional(self):
  self.assertEqual(charge_delta(2,0,2,-1),(-1,1));self.assertEqual(duration(150,add=-10),140)
 def test_modifier_update(self):
  add=-30;old=-30;new=-40;self.assertEqual(duration(150,add=add+new-old),110)
  mul=.5;old=.5;new=.8;self.assertAlmostEqual(duration(100,mul=mul*new/old),80)
 def test_override_remove_not_restore(self):
  self.assertEqual(duration(150,add=-30,override=50),50);self.assertEqual(duration(150,add=-30,override=-1),120)
 def test_two_state_blocking_selector(self):
  states=[(1,100),(0,20)];self.assertEqual(max((t if c==0 else 0 for c,t in states)),20)
 def test_ringo_cdr_condition(self):self.assertAlmostEqual(duration(90,cdr=.2),72)
if __name__=='__main__':unittest.main(verbosity=2)
