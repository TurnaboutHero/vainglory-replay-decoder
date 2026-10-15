"""Synthetic arithmetic witnesses, not client runtime observations."""
import struct,json,pathlib
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
def ticks(initial,deltas):
 x=f32(initial)
 for d in deltas:x=f32(x-f32(d))
 return {'remaining':x,'bits':struct.pack('>f',x).hex()}
out={'scope':'Synthetic witnesses only; no game execution', 'dispatch_boundary':{'record_timestamp':0.125,'previous_published_delta':0.25,'cursor_before':0.0,'cursor_after':0.25,'set_remaining':1.0,'trace_a_current_delta':0.125,'trace_b_current_delta':0.25,'trace_a_after_tick':ticks(1,[0.125]),'trace_b_after_tick':ticks(1,[0.25]),'interpretation':'Both frames admit the same record, because pump uses previous published delta. The existing, unpaused timer, set to 1 by an admitted action before stage 4, then sees different current delta. Record timestamp and record order alone cannot select the post-tick remaining value.'},'equal_total_float32':{'initial':1.0,'trace_a_deltas':[2**-25]*4,'trace_b_deltas':[2**-23],'sum_a':sum([2**-25]*4),'sum_b':2**-23,'trace_a':ticks(1,[2**-25]*4),'trace_b':ticks(1,[2**-23]),'interpretation':'Even an exact known summed delta does not encode the number and partition of float32 stores. Tiny dyadic values deliberately isolate rounding, not typical frame timing.'}}
p=pathlib.Path(__file__).with_name('partition-counterexample.json');p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
