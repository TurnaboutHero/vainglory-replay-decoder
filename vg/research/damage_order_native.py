"""Selected-client provider handoff audit. Static bytes, never server execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
ANCHORS = {
    0x530b25: 'c7400400000000c70090b62101',
    0x8e5bd0: 'c745f8f0238400c745fc04000000',
    0x8e5bef: 'e8dcaec4ff8bd08d4a04',
    0x8e5c12: '8d4df8ff46108b02518bcaff5014',
    0x121b690: 'd02f5300d0ec4500d0ec4500d0ec4500d0ec450000cd450000cd450000cd450060964500',
    0x45cd00: '8bc1c20400',
    0x45ecd0: 'c20400',
    0x459660: '8bc1c3',
    0x532fda: 'c70694b02101',
}


def check_anchors(read):
    """Check instruction windows, not decompiler symbol guesses."""
    for address, expected in ANCHORS.items():
        code = bytes.fromhex(expected)
        if read(address, len(code)) != code:
            raise ValueError(f'Native anchor differs at {address:08x}')
    return [{'address': f'{a:08x}', 'hex': b} for a, b in ANCHORS.items()]


def verify(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Selected executable SHA-256 differs')
    pe = struct.unpack_from('<I', data, 60)[0]
    count, size = struct.unpack_from('<H', data, pe + 6)[0], struct.unpack_from('<H', data, pe + 20)[0]
    base = struct.unpack_from('<I', data, pe + 52)[0]
    sections = []
    for i in range(count):
        o = pe + 24 + size + i * 40
        rva, raw_size, raw = struct.unpack_from('<III', data, o + 12)
        sections.append((base + rva, raw, raw_size))

    def read(address, length):
        for va, raw, size in sections:
            if 0 <= address - va and address - va + length <= size:
                return data[raw + address - va:raw + address - va + length]
        raise ValueError('Address not file backed')

    def cstr(address):
        out = bytearray()
        while len(out) < 256:
            v = read(address + len(out), 1)
            if v == b'\0':
                return out.decode('ascii')
            out.extend(v)
        raise ValueError('Unterminated RTTI name')

    names = []
    for slot, expected in [(0x121b68c, '.?AVBuffBehavior_MultiplyDamage@Kindred@Nuo@@'),
                           (0x121b6b4, '.?AV?$BehaviorHelper_Heal@UBuffBehaviorContext@Kindred@Nuo@@@Kindred@Nuo@@')]:
        col = struct.unpack('<I', read(slot, 4))[0]
        td = struct.unpack('<I', read(col + 12, 4))[0]
        name = cstr(td + 8)
        if name != expected:
            raise ValueError('Vtable boundary RTTI differs')
        names.append({'locator_slot': f'{slot:08x}', 'name': name})

    occurrences = {}
    for address in (0x20e736c, 0x20e7370, 0x20e7374, 0x20e7378,
                    0x1a760bc, 0x1a760c0, 0x1a760c4, 0x1a760c8, 0x8423f0):
        hits, cursor = [], 0
        needle = struct.pack('<I', address)
        while (cursor := data.find(needle, cursor)) >= 0:
            mapped = next((va + cursor - raw for va, raw, size in sections if raw <= cursor < raw + size), None)
            hits.append({'file_offset': cursor, 'va': None if mapped is None else f'{mapped:08x}'})
            cursor += 1
        occurrences[f'{address:08x}'] = hits
    return {'schema': 'vg.damage-order-native.v1', 'binary_sha256': SHA256,
            'anchors': check_anchors(read), 'rtti_boundaries': names,
            'literal_occurrences': occurrences,
            'scope': 'Exact static client bytes; literal hits are not exhaustive semantic xrefs; no server execution'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True)
    print(json.dumps(verify(p.parse_args().binary), indent=2))
