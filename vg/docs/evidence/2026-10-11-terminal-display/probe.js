'use strict';
const mod=Process.getModuleByName('Vainglory.exe'),base=mod.base,guards=GUARDS;
if(Process.arch!=='ia32')throw Error('Wrong architecture');
const va=a=>base.add(a-0x400000),delta=base.sub(ptr('0x400000')).toUInt32();
for(const g of guards){
 const a=new Uint8Array(g.bytes.match(/../g).map(x=>parseInt(x,16))),d=new DataView(a.buffer);
 for(const o of g.relocations)d.setUint32(o,(d.getUint32(o,true)+delta)>>>0,true);
 const b=new Uint8Array(base.add(g.rva).readByteArray(a.length));
 if(b.some((x,i)=>x!==a[i]))throw Error('Guard rejected: '+g.name);
}
const fp=p=>({value:p.readFloat(),bits:p.readU32()});
const str=p=>{
 const n=p.readU32(),cap=p.add(4).readU32(),data=p.add(8).readPointer();
 if(n>64||n>cap||(n&&data.isNull()))throw Error('String header rejected');
 return n?data.readUtf16String(n):'';
};
const state=()=>{
 const p=va(0x2091c24).readPointer();
 return {clock:p.isNull()?null:fp(p.add(0x194)),gate:p.isNull()?null:p.add(0x19d).readU8(),
 primary:p.isNull()?null:p.add(0x20).readU32(),index:va(0x1ef0b38).readU32(),
 record_clock:fp(va(0x1ef0b30)),file_open:!va(0x1eb09d8).readPointer().isNull(),
 delta:fp(va(0x20ec6d0)),multiplier:va(0x1a761b0).readDouble()};
};
let seq=0,failed=false;const rowMap=new Map(),uiMap=new Map(),lastGold=new Map();
function emit(tag,value){if(seq>=120000){fail('limit','Event limit');return;}send(Object.assign({tag,seq:++seq,utc_ms:Date.now(),thread:Process.getCurrentThreadId(),state:state()},value));}
function fail(name,e){if(!failed){failed=true;send({tag:'trace_error',hook:name,message:String(e).slice(0,300)});}}
function row(r){
 const h=r.add(12).readPointer(),gen=r.add(16).readU32(),d=r.add(4).readPointer();
 if(h.isNull()||d.isNull()||h.add(4).readU32()!==gen)return null;
 const method=h.readPointer().add(8).readPointer();
 if(!method.equals(va(0x541fa0)))return {row:r.toString(),unresolved_method:method.toString()};
 const bytes=new Uint8Array(method.readByteArray(10));
 if(Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('')!=='8d41ecf7d91bc923c1c3')throw Error('Resolver guard rejected');
 const a=h.sub(20),b=a.add(32).readPointer();
 const data={row:r.toString(),display:d.toString(),handle:h.toString(),generation:gen,actor:a.toString(),resource:b.toString(),
 actor_ref_178:a.add(0x178).readU32(),native7:fp(b.add(0x30c)),cache:r.add(0xf4).readS32(),display_raw:fp(d.add(0x75a8))};
 if(!r.add(12).readPointer().equals(h)||r.add(16).readU32()!==gen)return null;
 return data;
}
for(const g of guards){
 if(g.name==='resolver')continue;
 Interceptor.attach(base.add(g.rva),{onEnter(args){
  if(failed)return;
  try{
   const ecx=this.context.ecx,esp=this.context.esp,caller=this.returnAddress;
   if(g.name==='label'){
    if(!caller.equals(va(0x7403cf)))return;
    const d=ecx.sub(0x13d8),s=esp.add(4).readPointer();
    if(!s.equals(d.add(0x758c)))throw Error('Label argument mismatch');
    emit('gold_label',{display:d.toString(),text:str(s)});
   }else if(g.name==='gold_row'){
    rowMap.set(ecx.toString(),ecx);
    const v=row(ecx);if(v){const key=JSON.stringify(v);if(lastGold.get(v.row)!==key){lastGold.set(v.row,key);emit('gold_row',v);}}
   }else if(g.name==='time_format'||g.name==='gold_format'){
    if(g.name==='time_format')uiMap.set(ecx.toString(),ecx);
    emit(g.name,{object:ecx.toString(),input:fp(esp.add(4)),caller_rva:caller.sub(base).toString()});
   }else if(g.name==='anchor')emit(g.name,{object:ecx.toString(),input:fp(esp.add(8)),flag:esp.add(12).readU32()});
   else if(g.name==='setter')emit(g.name,{object:ecx.toString(),input:fp(esp.add(4)),caller_rva:caller.sub(base).toString()});
   else if(g.name==='tick')emit(g.name,{object:ecx.toString()});
   else emit(g.name,{object:ecx.toString(),arg0:args[0].toUInt32(),caller_rva:caller.sub(base).toString()});
  }catch(e){fail(g.name,e);}
 }});
}
setInterval(()=>{
 if(failed)return;
 try{
  emit('sample',{});
 }catch(e){fail('sample',e);}
},100);
emit('hooks_installed',{base:base.toString(),pid:Process.id,count:guards.length-1,entry_only:true});
