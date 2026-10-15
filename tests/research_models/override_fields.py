"""Research-only compact native prefix reader. Never applies events to a replay state."""
import struct
NATIVE_LENGTHS={0x41a:13,0x41b:8}
def decode(opcode,payload,domain='native'):
 if opcode not in NATIVE_LENGTHS:return {'status':'unknown_opcode'}
 expected=NATIVE_LENGTHS[opcode] if domain=='native' else 14 if domain=='h5810_observed' else None
 if expected is None or len(payload)!=expected:return {'status':'unsupported_layout'}
 actor,source=struct.unpack_from('>II',payload)
 d={'status':'decoded_prefix','actor_raw':actor,'original_slot_raw':source,'native_prefix_bytes':NATIVE_LENGTHS[opcode],
    'opaque_suffix_hex':payload[NATIVE_LENGTHS[opcode]:].hex(),'applied':None,'request_response_pairing':None,
    'native_apply_guard':'actor resolves and global 0209e204 != 0','source_packed_15bit':source&0x7fff}
 if opcode==0x41a:d.update(replacement_slot_raw=struct.unpack_from('>I',payload,8)[0],control_raw=payload[12],control_nonzero=payload[12]!=0)
 return d
# Small models of precisely bounded helper behavior, not network/server or replay simulation.
def insert(entries,source,replacement):
 for i,(word,flags) in enumerate(entries):
  if flags&3==0:
   entries[i]=((word&0xc0000000)|(source&0x7fff)|((replacement&0x7fff)<<15),(flags&0xfd)|1)
   return i
 return None
def resolve(entries,source):
 for word,flags in entries:
  if flags&3 and word&0x7fff==source:return word>>15&0x7fff
 return source
def clear(entries,source):
 for i,(word,flags) in enumerate(entries):
  if flags&3 and word&0x7fff==source:entries[i]=(word,flags&0xfc)
