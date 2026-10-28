"""Read-only, SHA-gated checks for selected passive/active research edges."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA256 = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
TABLES = {0x127d3c0:0x85a890, 0x127d500:0x85db70,
          0x121a2e0:0x45e8a0, 0x121a680:0x85a750,
          0x121a658:0x85b440, 0x127d1ac:0x92cbb0}

def verify(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Selected executable SHA-256 differs")
    pe = struct.unpack_from("<I", data, 60)[0]
    count = struct.unpack_from("<H", data, pe+6)[0]
    opt = pe+24
    size = struct.unpack_from("<H", data, pe+20)[0]
    base = struct.unpack_from("<I", data, opt+28)[0]
    def read(va, length):
        for i in range(count):
            rva, raw_size, raw = struct.unpack_from("<III",data,opt+size+i*40+12)
            delta = va-base-rva
            if 0 <= delta and delta+length <= raw_size:
                return data[raw+delta:raw+delta+length]
        raise ValueError("Address not file backed")
    for address, expected in TABLES.items():
        if struct.unpack("<I",read(address,4))[0] != expected:
            raise ValueError("Vtable edge differs")
    # Identical-code-folded empty virtual dispatch, independently checked bytes.
    if read(0x45e8a0,3) != bytes.fromhex("c20800"):
        raise ValueError("Expected ret 8 leaf differs")
    pointer = struct.unpack("<I",read(0x1a73e48,4))[0]
    symbol = read(pointer,64).split(b"\0",1)[0].decode("ascii")
    if symbol != "*Item_SeraphicShell*":
        raise ValueError("Shell property thunk global differs")
    return {"schema":"vg.passive-pe-check.v1","binary_sha256":SHA256,
            "vtable_edges":[{"site":f"{a:08x}","target":f"{b:08x}"} for a,b in TABLES.items()],
            "apply_to_myself_dispatch_bytes":"c20800",
            "shell_property_global":{"address":"01a73e48","pointee":f"{pointer:08x}","symbol":symbol},
            "scope":"Static selected edges only; no execution or complete control-flow proof"}

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary",required=True)
    print(json.dumps(verify(parser.parse_args().binary),indent=2))
