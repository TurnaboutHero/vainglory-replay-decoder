import struct,json,pathlib,sys
p=pathlib.Path(__file__).parent
b=pathlib.Path(sys.argv[1]).read_bytes()
pe=struct.unpack_from('<I',b,0x3c)[0]; n=struct.unpack_from('<H',b,pe+6)[0]; size=struct.unpack_from('<H',b,pe+20)[0]; base=struct.unpack_from('<I',b,pe+24+28)[0]
sects=[]
for i in range(n):
 o=pe+24+size+i*40
 name=b[o:o+8].rstrip(b'\0').decode(); vs,va,rs,rp=struct.unpack_from('<4I',b,o+8)
 sects.append((name,base+va,rp,rs))
def va(off):
 for _,a,r,s in sects:
  if r<=off<r+s:return a+off-r
def off(a):
 for _,v,r,s in sects:
  if v<=a<v+s:return r+a-v
out={}
for a in [0x121d898,0x121d8a8,0x121d8bc,0x128ec04]:
 o=off(a); val=b[o:b.index(0,o)]
 refs=[]; pos=0
 while (pos:=b.find(struct.pack('<I',a),pos))>=0:
  refs.append(hex(va(pos) or 0));pos+=1
 out[hex(a)]={'string':val.decode(errors='replace'),'absolute_refs':refs}
for target in [0x95cf10,0x95cd10,0x9613b0,0x956380,0x93d4a0]:
 refs=[]
 for name,a,r,s in sects:
  if name!='.text':continue
  for i in range(r,r+s-5):
   if b[i]==0xe8 and (va(i)+5+struct.unpack_from('<i',b,i+1)[0])==target:refs.append(hex(va(i)))
 out[hex(target)]={'raw_e8_candidates':refs}
(p/'raw-refs.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
