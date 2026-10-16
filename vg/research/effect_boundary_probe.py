"""Static, hash-gated boundary checks; does not launch or emulate the game."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SELECTED="d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
ORIGINAL="659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642"


def verify(selected_path, original_path):
    selected,original=Path(selected_path).read_bytes(),Path(original_path).read_bytes()
    if hashlib.sha256(selected).hexdigest()!=SELECTED or hashlib.sha256(original).hexdigest()!=ORIGINAL:
        raise ValueError("Expected selected and installed original hashes")
    if len(selected)!=len(original):
        raise ValueError("Images differ in size")
    diffs=[i for i,(a,b) in enumerate(zip(selected,original)) if a!=b]
    pe=struct.unpack_from("<I",selected,60)[0]
    if diffs!=[pe+22] or selected[pe+22]^original[pe+22]!=0x20:
        raise ValueError("Expected only LAA characteristic bit difference")
    count=struct.unpack_from("<H",selected,pe+6)[0]
    opt=pe+24
    size=struct.unpack_from("<H",selected,pe+20)[0]
    base=struct.unpack_from("<I",selected,opt+28)[0]
    def read(address,length):
        for i in range(count):
            rva,raw_size,raw=struct.unpack_from("<III",selected,opt+size+i*40+12)
            delta=address-base-rva
            if 0<=delta and delta+length<=raw_size:
                return selected[raw+delta:raw+delta+length]
        raise ValueError("Not file backed")
    stubs={0x4b7c00:bytes.fromhex("d9eec3"),0x450910:bytes.fromhex("c3"),0x45ecd0:bytes.fromhex("c20400")}
    for a,b in stubs.items():
        if read(a,len(b))!=b:raise ValueError("Stub bytes differ")
    calls={0x860d1c:0x4b7c00,0x860d35:0x4b7c00,0x839cd2:0x450910,0x83886c:0x450910}
    for site,target in calls.items():
        code=read(site,5)
        if code[0]!=0xe8 or site+5+struct.unpack_from("<i",code,1)[0]!=target:
            raise ValueError("Selected direct call differs")
    tables={0x121b138:0x45ecd0,0x121b42c:0x45ecd0,0x121b2e8:0x45ecd0,0x121b694:0x45ecd0,0x127db78:0x860cb0}
    for site,target in tables.items():
        if struct.unpack("<I",read(site,4))[0]!=target:raise ValueError("Selected virtual edge differs")
    return {"schema":"vg.effect-boundary-pe.v1","selected_sha256":SELECTED,"original_sha256":ORIGINAL,
            "bytes":len(selected),"only_difference":{"file_offset":f"{diffs[0]:x}","characteristic":"IMAGE_FILE_LARGE_ADDRESS_AWARE","xor":"20"},
            "stubs":[{"address":f"{a:08x}","bytes":b.hex()} for a,b in stubs.items()],
            "calls":[{"site":f"{a:08x}","target":f"{b:08x}"} for a,b in calls.items()],
            "vtable_edges":[{"site":f"{a:08x}","target":f"{b:08x}"} for a,b in tables.items()],
            "scope":"Selected static paths have identical code in installed original; no runtime gameplay, server absence or universal support claim"}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected",required=True)
    parser.add_argument("--original",required=True)
    args=parser.parse_args()
    print(json.dumps(verify(args.selected,args.original),indent=2))
