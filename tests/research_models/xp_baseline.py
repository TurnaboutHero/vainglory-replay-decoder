"""Bounded research model. No production state acceptance or runtime claim."""
import math,struct

def f32(value):
 try:v=struct.unpack('>f',struct.pack('>f',value))[0]
 except OverflowError as exc:raise ValueError('float32 overflow') from exc
 if not math.isfinite(v):raise ValueError('nonfinite value')
 return v

def snapshot_projection(payload):
 if len(payload) not in (746,750):raise ValueError('unsupported snapshot length')
 gate=struct.unpack_from('>I',payload,326)[0]
 if gate:raise ValueError('snapshot baseline skipped by native gate')
 return {'actor_id':struct.unpack_from('>I',payload,8)[0],
  'base_level':f32(struct.unpack_from('>f',payload,294)[0]),
  'xp_progress':f32(struct.unpack_from('>f',payload,318)[0]),
  'base_xp_required':f32(struct.unpack_from('>f',payload,322)[0]),
  'post_snapshot_level_loop':struct.unpack_from('>I',payload,705)[0],
  'effective_level':None,'state_accepted':False}

def layer_operation(layers,layer,value,mode):
 if len(layers)!=4 or not 0<=layer<4:raise ValueError('four native layers required')
 out=list(map(f32,layers));out[layer]=f32(out[layer]+f32(value)) if mode==0 else f32(value)
 return tuple(out)

def effective_unclamped(layers):
 """Finite SSE-like float32 sequence; native per-consumer clamps are separate."""
 b,a,m,n=map(f32,layers)
 return f32(f32(f32(f32(n+1)*a)+b)*f32(m+1))

def xp_operation(current,value,mode):
 return f32(max(0,f32(f32(current)+f32(value)) if mode==0 else f32(value)))

def level_step(level,progress,required,delta):
 if not isinstance(level,int) or isinstance(level,bool) or not 1<=level<=12:raise ValueError('ordinary effective integral level required')
 if not isinstance(delta,int) or isinstance(delta,bool) or not 0<=delta<=0xffffffff:raise ValueError('u32 delta required')
 p,t=f32(progress),f32(required)
 if p<0 or t<0:raise ValueError('nonnegative operands required')
 if level==12:return level,p
 new=level+min(delta,12-level)
 return new,0.0 if new==1 else f32(max(0,f32(p-t)))
