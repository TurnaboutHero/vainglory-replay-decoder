"""Inspect three hash-pinned item declarations and their separate named buff caps."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from vg.core.cff_resource import CatalogError, load_cff
from vg.research.verify_sequential_pe import EXPECTED_SHA256

ITEMS = (
    ("Item_Bonesaw", "BBB2B75EDB5B7BF1903527D074EA4414", "9ebd8b1a6e0ec873e3f5e2477086f56857bb1f2d90b273b924d62677dcbaa8bc"),
    ("Item_PiercingSpear", "66D56F1624A8244CF0D292B7FA17ABD1", "ba5671f3c0df64e7fd3b62ddddfdb29f3e5abd33110af0f0ceee2381dd9262b2"),
    ("Item_DragonsEye", "21C204A34AAEF1A634F9D2430A7F820A", "d3edad89a9234cd21408a0c3a5fbc2b3fcaa7041754ba305a9bf6e5141649bf6"),
)

def inspect(binary, data_root):
    executable = Path(binary).read_bytes()
    digest = hashlib.sha256(executable).hexdigest()
    if digest != EXPECTED_SHA256:
        raise CatalogError("Executable SHA-256 does not match selected LAA build")
    rows = []
    for name, resource_name, resource_hash in ITEMS:
        resource = (Path(data_root) / resource_name[:2] / resource_name).read_bytes()
        decoded = load_cff(resource, executable, build_sha256=digest,
                           resource_sha256=resource_hash, key_table_va=0x1e3f978, version=12)
        root, symbol_type = struct.unpack_from("<II", decoded.symbol)
        if symbol_type != 0xfc7583e1 or decoded.symbol[8:].split(b"\0")[0] != ("*"+name+"*").encode("ascii"):
            raise CatalogError("Item symbol does not match pinned declaration")
        table = decoded.relocations[root+0x130]
        properties = []
        for index in range(32):
            slot = table+index*4
            if slot+4 > len(decoded.inst):
                raise CatalogError("Property table is out of bounds")
            pointer = decoded.relocations.get(slot)
            if pointer is None:
                if struct.unpack_from("<I", decoded.inst, slot)[0] != 0:
                    raise CatalogError("Missing property relocation")
                break
            name_at = decoded.relocations[pointer]
            end = decoded.inst.find(b"\0", name_at, name_at+257)
            if end < name_at:
                raise CatalogError("Invalid property name")
            label = decoded.inst[name_at:end].decode("ascii")
            bits = struct.unpack_from("<I", decoded.inst, pointer+4)[0]
            value = struct.unpack_from("<f", decoded.inst, pointer+4)[0]
            properties.append({"index": index, "name": label,
                               "selector_1_declared_value": value, "value_bits": f"{bits:08x}"})
        else:
            raise CatalogError("Property table lacks bounded sentinel")
        rows.append({"definition_name": name, "resource_name": resource_name,
                     "resource_sha256": resource_hash, "properties": properties})
    buff_name = "551BCB541D80053BACD0A897B7993A77"
    buff_hash = "e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79"
    resource = (Path(data_root)/buff_name[:2]/buff_name).read_bytes()
    decoded = load_cff(resource, executable, build_sha256=digest, resource_sha256=buff_hash,
                       key_table_va=0x1e3f978, version=12)
    root, symbol_type = struct.unpack_from("<II", decoded.symbol)
    if symbol_type != 0x69bb0cf9 or decoded.symbol[8:].split(b"\0")[0] != b"*KindredBuffs*":
        raise CatalogError("Buff table symbol differs")
    table = decoded.relocations[root]
    selected = {"Buff_Item_Bonesaw", "Buff_Item_BonesawDebuff", "Buff_Item_Bonesaw_Pen",
                "Buff_Item_DragonsEye_Control", "Buff_Item_DragonsEye_CrystalBonus"}
    buffs = []
    for index in range(4096):
        slot = table+index*4
        if slot+4 > len(decoded.inst):
            raise CatalogError("Buff table out of bounds")
        entry = decoded.relocations.get(slot)
        if entry is None:
            if struct.unpack_from("<I",decoded.inst,slot)[0] != 0:
                raise CatalogError("Missing buff relocation")
            break
        at = decoded.relocations[entry]
        end = decoded.inst.find(b"\0",at,at+257)
        if end < at:
            raise CatalogError("Invalid buff name")
        name = decoded.inst[at:end].decode("ascii")
        if name in selected:
            buffs.append({"definition_index":index, "name":name,
                          "definition_cap_u16_at_24":struct.unpack_from("<H",decoded.inst,entry+0x24)[0]})
    else:
        raise CatalogError("Buff table lacks bounded sentinel")
    if len(buffs)!=len(selected) or {b["name"] for b in buffs}!=selected:
        raise CatalogError("Named buff definitions missing or duplicated")
    return {"schema": "vg.named-stack-item-declarations.v1", "build_sha256": digest,
            "scope": "Selected local resource declarations only; not inherited effective runtime values or observed stack state",
            "items": rows, "buff_table": {"resource_name":buff_name,"resource_sha256":buff_hash,
            "symbol_type":"69bb0cf9","definition_count":index,"selected":buffs}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.binary, args.data_root), indent=2, allow_nan=False))
