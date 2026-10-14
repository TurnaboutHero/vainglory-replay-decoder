"""Offline definition-to-key example. Does not execute or modify game assets."""
from pathlib import Path
import argparse,sys,hashlib,struct,json
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--app',type=Path,required=True);p.add_argument('--replay-dir',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.repo.resolve()))
from vg.core.cff_resource import load_cff
from vg.core.definition_catalog import BuildProfile,load_catalog
from vg.core.vgr_records import iter_records
sha=lambda b:hashlib.sha256(b).hexdigest()
exe=(a.app/'Vainglory.exe').read_bytes();eh=sha(exe)
assert eh=='d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
mn='03A640B504C2B4D7C8CBF3A04E189223';manifest=(a.app/'Data'/mn[:2]/mn).read_bytes();mh=sha(manifest)
assert mh=='7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c'
profile=BuildProfile(eh,mh,0x1e3f978,12,932)
cat=load_catalog(manifest,exe,profile);definition=cat.lookup(487)
assert definition.serialized_name=='*Item_FountainOfRenewal*'
rn='3A4A448F2A4B2A65D84997E8DBC3784A';resource=(a.app/'Data'/rn[:2]/rn).read_bytes();rh=sha(resource)
assert rh=='4f367432f83f947b6446c2f083d0d1de81d0c6ab678bfe3202140088cdb32c37'
d=load_cff(resource,exe,build_sha256=eh,resource_sha256=rh,key_table_va=profile.key_table_va,version=12)
root,typ=struct.unpack_from('<II',d.symbol);assert root==0 and typ==0xfc7583e1
assert d.symbol[8:].split(b'\0')[0].decode()==definition.serialized_name
ptr=lambda at:d.relocations[at]
u32=lambda at:struct.unpack_from('<I',d.inst,at)[0]
f32=lambda at:struct.unpack_from('<f',d.inst,at)[0]
def string(at):
 off=ptr(at);return d.inst[off:d.inst.index(0,off)].decode('ascii')
ability=root+0x40; name=string(ability+4);group=string(ability+0x18)
assert d.inst[root+0x38]==1 and string(root+0x3c)==''
assert name=='Ability__Item__FountainOfRenewal' and group=='' and d.inst[ability+0x6a]==0
prop_array=ptr(ability+0x8c);properties=[];at=prop_array
while u32(at):
 prop=ptr(at);properties.append({'name':string(prop),'offset':prop,'value_at_plus4':f32(prop+4)});at+=4
assert properties[0]['name']=='Cooldown' and properties[0]['value_at_plus4']==75.0
h=0x811c9dc5
for c in name.encode('ascii'):h=((h^c)*0x1000193)&0xffffffff
assert h==0x6f056481
counts=Counter();examples=[];grants=[];hashes={}
for path in sorted(a.replay_dir.glob('*.vgr'),key=lambda p:int(p.name.split('.')[-2])):
 if path.name.startswith('._'):continue
 data=path.read_bytes();hashes[path.name]=sha(data)
 for r in iter_records(data):
  row={'section':int(path.name.split('.')[-2]),'file':path.name,'offset':r.offset,'timestamp':r.timestamp,'opcode':hex(r.opcode),'content_length':r.content_length,'payload_hex':r.payload.hex()}
  if r.opcode in (0x428,0x48a,0x43d):
   expected_payload_length={0x428:14,0x48a:22,0x43d:14}[r.opcode]
   assert len(r.payload)==expected_payload_length and r.content_length==expected_payload_length+2, (path.name,r.offset,r.opcode,r.content_length,len(r.payload))
  if r.opcode in (0x428,0x48a):
   owner,key=struct.unpack_from('>II',r.payload)
   if key==h:
    counts[(r.opcode,owner)]+=1
    if not any(x['opcode']==row['opcode'] and x['owner']==owner for x in examples):examples.append(dict(row,owner=owner,key=key))
  if r.opcode==0x43d:
   owner,defid,instance=struct.unpack_from('>III',r.payload)
   if defid==487:grants.append(dict(row,owner=owner,definition=defid,instance=instance))
assert len(hashes)==168
assert counts==Counter({(0x48a,1500):133,(0x48a,1501):73}), counts
assert [(x['owner'],x['section'],x['offset']) for x in examples]==[(1500,35,3206),(1501,95,4474)]
assert [(x['owner'],x['section'],x['offset'],x['instance']) for x in grants]==[(1500,34,109574,2007),(1501,94,54898,2015)]
for row in examples:
 assert bytes.fromhex(row['payload_hex'])[12:16]==struct.pack('>f',75.0)
# Pin the full historical receipt, not just matching numerical identifiers.
expected=json.loads(Path(__file__).with_name('example.json').read_text())
assert hashes==expected['source_sha256']
assert examples==expected['first_records'] and grants==expected['grant_records']
result={'scope':'One static build-matched item definition -> primary cooldown key, with offline wire corroboration; no instance lifetime or runtime result assertion','input':{'executable_sha256':eh,'manifest_sha256':mh,'resource_name':rn,'resource_sha256':rh},'definition':{'index':487,'serialized_name':definition.serialized_name,'symbol_type':hex(typ),'root':root},'embedded_ability':{'base':ability,'active_flag':d.inst[root+0x38],'external_ref':string(root+0x3c),'name':name,'group':group,'mode6a':d.inst[ability+0x6a],'properties':properties,'relevant_relocations':{hex(x):hex(ptr(x)) for x in [0x3c,0x44,0x58,0xcc,prop_array,properties[0]['offset']]}},'derived_key':{'decimal':h,'hex':hex(h),'branch':'empty group -> name fallback, item initializer passes overrideName=0'},'record_counts':[{'opcode':hex(o),'owner':owner,'count':n} for (o,owner),n in sorted(counts.items())],'first_records':examples,'grant_records':grants,'source_sha256':hashes,'limitations':['Recorded owner/key observations do not prove successful native application','No pointer identity or lifetime is inferred from matching key alone','No 0429 slot mapping is established by this item example','No countdown/state reducer validation']}
print(json.dumps(result,indent=2))
