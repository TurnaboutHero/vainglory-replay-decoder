"""SHA-gated selected PE checks for stat stacking research (no execution)."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA256 = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
REGISTRY = (("Buff_Item_BrokenMyth_Pen",0x44b63b,0x1a744b0,0x1a79f10,0x8ee190),
            ("Buff_Item_TensionBow_Pen",0x44b6a9,0x1a74528,0x1a79f68,0x8f3190),
            ("Buff_Item_Bonesaw_Pen",0x44b6b3,0x1a74534,0x1a79f70,0x8edd90),
            ("Buff_Grumpjaw_Perk_Armor",0x44cbdf,0x1a73310,0x1a7b060,0x8e5b60))

def verify(path):
    data=Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA256:
        raise ValueError("Selected executable SHA-256 differs")
    pe=struct.unpack_from("<I",data,60)[0]
    count=struct.unpack_from("<H",data,pe+6)[0]
    opt=pe+24
    size=struct.unpack_from("<H",data,pe+20)[0]
    base=struct.unpack_from("<I",data,opt+28)[0]
    def read(address,length):
        for i in range(count):
            rva,raw_size,raw=struct.unpack_from("<III",data,opt+size+i*40+12)
            delta=address-base-rva
            if 0<=delta and delta+length<=raw_size:
                return data[raw+delta:raw+delta+length]
        raise ValueError("Address not file backed")
    expected=bytes.fromhex("c705ac730e023333b33e")
    if read(0x44e081,10)!=expected:
        raise ValueError("CDR initialization instruction differs")
    lower={0x1a760fc:0x00000000,0x1a760d4:0x3f000000}
    for address,bits in lower.items():
        if struct.unpack("<I",read(address,4))[0]!=bits:
            raise ValueError("Selected lower-bound initializer differs")
    stubs={0x450910:bytes.fromhex("c3"),0x45ecd0:bytes.fromhex("c20400"),0x4b7c00:bytes.fromhex("d9eec3")}
    for address,code in stubs.items():
        if read(address,len(code))!=code:
            raise ValueError("Selected folded stub differs")
    rows=[]
    for name,site,source,entry,factory in REGISTRY:
        if read(site,10)!=b"\xa1"+struct.pack("<I",source)+b"\xa3"+struct.pack("<I",entry):
            raise ValueError("Registry copy differs")
        pointer=struct.unpack("<I",read(source,4))[0]
        if read(pointer,len(name)+1)!=name.encode()+b"\0" or struct.unpack("<I",read(entry+4,4))[0]!=factory:
            raise ValueError("Registry name/factory differs")
        rows.append({"name":name,"copy_site":f"{site:08x}","name_global":f"{source:08x}","entry":f"{entry:08x}","factory":f"{factory:08x}"})
    return {"schema":"vg.stat-stacking-pe.v1","binary_sha256":SHA256,
            "cdr_initialization":{"site":"0044e081","destination":"020e73ac","instruction_hex":expected.hex(),"float_bits":"3eb33333","float_value":struct.unpack("<f",expected[6:])[0],"scope":"Static initialization store; not an immutable runtime cap"},
            "lower_bound_initializers":[{"address":f"{a:08x}","bits":f"{b:08x}"} for a,b in lower.items()],
            "folded_stubs":[{"address":f"{a:08x}","bytes":b.hex()} for a,b in stubs.items()],
            "registrations":rows,"scope":"Selected static bytes only, not gameplay execution"}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary",required=True)
    print(json.dumps(verify(parser.parse_args().binary),indent=2))
