"""Read-only, bounded PE verifier; emits identities and decoded addresses only."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


EXPECTED_SHA256 = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"


def verify(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Executable SHA-256 does not match the selected LAA build")
    if data[:2] != b"MZ":
        raise ValueError("Missing DOS signature")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Missing PE signature")
    machine, count = struct.unpack_from("<HH", data, pe + 4)
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    if machine != 0x14C or struct.unpack_from("<H", data, opt)[0] != 0x10B:
        raise ValueError("Expected x86 PE32")
    base = struct.unpack_from("<I", data, opt + 28)[0]
    sections = []
    for i in range(count):
        at = opt + opt_size + i * 40
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", data, at + 8)
        sections.append((rva, raw_size, raw_offset))

    def read(va, size):
        rva = va - base
        for start, raw_size, raw_offset in sections:
            delta = rva - start
            if 0 <= delta and delta + size <= raw_size:
                offset = raw_offset + delta
                if offset + size <= len(data):
                    return data[offset:offset + size]
        raise ValueError(f"VA span not backed by section bytes: {va:08x}+{size}")

    def word(va):
        return struct.unpack("<I", read(va, 4))[0]

    entries = []
    for opcode, call, constructor, vtable in [
        (0x432, 0x4D25D5, 0x819F70, 0x127C6D0),
        (0x433, 0x4D2651, 0x81C430, 0x127CC30),
        (0x41D, 0x4D2D6D, 0x81B960, 0x127C9B4),
    ]:
        index_va = 0x4D51E4 + opcode - 0x3EA
        index = read(index_va, 1)[0]
        target_va = 0x4D5000 + 4 * index
        instruction = read(call, 5)
        if instruction[0] != 0xE8:
            raise ValueError(f"Expected direct relative call at {call:08x}")
        destination = (call + 5 + struct.unpack("<i", instruction[1:])[0]) & 0xFFFFFFFF
        if destination != constructor:
            raise ValueError("Constructor call target differs")
        entries.append({
            "opcode": f"{opcode:04x}", "index_byte_va": f"{index_va:08x}",
            "index": index, "target_word_va": f"{target_va:08x}",
            "receiver_va": f"{word(target_va):08x}", "call_site_va": f"{call:08x}",
            "relative_call_target_va": f"{destination:08x}",
            "vtable_va": f"{vtable:08x}",
            "vtable_serializer_04_va": f"{word(vtable + 4):08x}",
            "vtable_apply_08_va": f"{word(vtable + 8):08x}",
            "vtable_forward_0c_va": f"{word(vtable + 12):08x}",
            "vtable_16_byte_span_sha256": hashlib.sha256(read(vtable, 16)).hexdigest(),
        })
    return {"schema": "bounded-respawn-pe-verification-v1", "executable_sha256": digest,
            "image_base": f"{base:08x}", "entries": entries,
            "scope": "Static selected PE bytes only; no execution or exhaustive caller claim"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path, nargs="?")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    binary = args.binary or args.executable
    if binary is None:
        parser.error("provide --binary or the positional executable path")
    output = json.dumps(verify(binary), indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8", newline="\n")
    else:
        print(output, end="")
