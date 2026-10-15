"""Bounded native algebra, not a replay reducer or execution emulator."""
def rank(word): return (word >> 10) & 7
def set_rank(word,value): return (word & ~0x1c00) | ((value << 10) & 0x1c00)
def requirement(raw_rank,base_rank,alternate=False,first_requires_2=False):
 n=raw_rank-base_rank
 seq=(6,9,12) if alternate else (2 if first_requires_2 else 1,2,4,6,8)
 return seq[n] if 0 <= n < len(seq) else 255
def overdrive_resolved(raw_rank,base_rank,alternate=False):return raw_rank==base_rank+(3 if alternate else 5)
def overdrive_missing_slot_after_successful_lookup(): return True
def apply_grant_gate(points,hero_level,raw_rank,base_rank,alternate=False,first_requires_2=False):
 # Requires resolved actor/component/ability and already computed/clamped finite stats.
 return points>0 and hero_level>=requirement(raw_rank,base_rank,alternate,first_requires_2)
def property_value(raw_rank,base,increment,bonus):
 # Learned-rank algebra only; this does not emulate native float32 rounding.
 if not 1 <= raw_rank <= 7: raise ValueError("Only learned ranks1..7 are modeled")
 return base+(raw_rank-1)*increment+(bonus if raw_rank==5 else 0)
