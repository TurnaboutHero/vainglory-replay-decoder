"""Hash-gated static checks for selected sequential-research instruction edges."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED_SHA256 = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
CALLS = {0x52af08: 0x9401f0, 0x52af1a: 0x95dd50, 0x52af26: 0x95dcf0,
         0x52af38: 0x95cf10, 0x52af44: 0x95cd10, 0x95d0ed: 0x956380,
         0x95d127: 0x9613b0, 0x9519e0: 0x95cd10, 0x9519e7: 0x956380,
         0x5ad752: 0x5a40e0, 0x5ad717: 0x5a4070, 0x953a50: 0x92d820,
         0x955bff: 0x112af70, 0x84b5e0: 0x92ea80, 0x8615d3: 0x92e8e0,
         0x94f4cb: 0x95f4d0, 0x8ef067: 0x9604f0}

def verify(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Executable SHA-256 does not match selected LAA build")
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    machine, count = struct.unpack_from("<HH", data, pe + 4)
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    if data[:2] != b"MZ" or data[pe:pe + 4] != b"PE\0\0" or machine != 0x14c:
        raise ValueError("Expected x86 PE")
    base = struct.unpack_from("<I", data, opt + 28)[0]
    def read(va, size):
        for i in range(count):
            at = opt + opt_size + i * 40
            rva, raw_size, raw_offset = struct.unpack_from("<III", data, at + 12)
            delta = va - base - rva
            if 0 <= delta and delta + size <= raw_size:
                return data[raw_offset + delta:raw_offset + delta + size]
        raise ValueError("Selected VA not file-backed")
    edges = []
    for site, expected in CALLS.items():
        instruction = read(site, 5)
        if instruction[0] != 0xe8:
            raise ValueError("Selected instruction is not a direct CALL")
        target = (site + 5 + struct.unpack_from("<i", instruction, 1)[0]) & 0xffffffff
        if target != expected:
            raise ValueError("Selected CALL target differs")
        edges.append({"site": f"{site:08x}", "target": f"{target:08x}"})
    tables = {0x128067c: 0x9519a0, 0x121b3dc: 0x45ecd0, 0x121b3d0: 0x45cd00,
              0x121b0d4: 0x45ecd0, 0x127dba8: 0x861530, 0x127c9f8: 0x94f440,
              0x127c9a8: 0x94f1d0}
    for site, expected in tables.items():
        if struct.unpack("<I", read(site, 4))[0] != expected:
            raise ValueError("Selected vtable target differs")
    if struct.unpack("<I", read(0x953a32, 4))[0] != 0x127c6d0:
        raise ValueError("Inline respawn vtable immediate differs")
    registrations = [(0x44b569,0x1a743e0,0x1a79e68,0x8edc70),
                     (0x44b587,0x1a743ec,0x1a79e80,0x8edcc0),
                     (0x44b6b3,0x1a74534,0x1a79f70,0x8edd90),
                     (0x44b6db,0x1a7455c,0x1a79f90,0x8eefb0),
                     (0x44b6e5,0x1a74570,0x1a79f98,0x8ef000)]
    for site, source, destination, factory in registrations:
        code = read(site, 10)
        if code[0] != 0xa1 or code[5] != 0xa3 or struct.unpack_from("<I", code,1)[0] != source or struct.unpack_from("<I",code,6)[0] != destination:
            raise ValueError("Selected registry name-copy sequence differs")
        if struct.unpack("<I",read(destination+4,4))[0] != factory:
            raise ValueError("Selected registry factory differs")
    return {"schema": "vg.sequential-pe-check.v1", "binary_sha256": digest,
            "calls": edges,
            "vtable_targets": [{"site":f"{a:08x}","target":f"{b:08x}"} for a,b in tables.items()],
            "inline_respawn_vtable": "0127c6d0",
            "item_buff_registry": [{"copy_site":f"{a:08x}","name_source":f"{b:08x}","entry":f"{c:08x}","factory":f"{d:08x}"} for a,b,c,d in registrations], "scope": "Static selected edges only, not execution or full control-flow verification"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    print(json.dumps(verify(parser.parse_args().binary), indent=2))
