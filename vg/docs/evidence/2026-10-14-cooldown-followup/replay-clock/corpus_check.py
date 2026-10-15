import sys,pathlib,collections,json,struct,hashlib
root=pathlib.Path(__file__).resolve().parent
from vg.core.vgr_records import iter_records
files=sorted(pathlib.Path(sys.argv[1]).glob('*.vgr'),key=lambda p:int(p.name.split('.')[-2]))
counts=collections.Counter(); groups=collections.Counter(); records=[]; anchors=[]
for p in files:
 for r in iter_records(p.read_bytes()):
  counts[f'{r.opcode:04x}']+=1;groups[r.timestamp]+=1
  records.append((int(p.name.split('.')[-2]),r.offset,r.timestamp,r.opcode))
  if r.opcode==0x46f and len(r.payload)>=68: anchors.append({'file_index':int(p.name.split('.')[-2]),'offset':r.offset,'record_time':r.timestamp,'game_time':struct.unpack_from('>f',r.payload,64)[0]})
neg=[(a,b) for a,b in zip(records,records[1:]) if b[2]<a[2]]
selected={k:counts[k] for k in ['0428','0427','0429','042a','042b','048a','0476','0451','046f']}
out={'scope':'Fresh offline H5810 envelope check; no runtime observations','files':len(files),'records':len(records),'unique_timestamps':len(groups),'largest_same_timestamp_group':max(groups.values()),'timestamp_backsteps':len(neg),'first_timestamp':records[0][2],'last_timestamp':records[-1][2],'selected_opcodes':selected,'first_anchor':anchors[0],'last_anchor':anchors[-1],'last_record_interval_after_anchor':records[-1][2]-anchors[-1]['record_time'],'clock_samples_do_not_supply':'Per-update QPC delta, dispatch grouping per playback frame, queue drain boundaries, timer tick states are absent from this envelope check.'}
(root/'corpus-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
