"""Read-only selected-build checks for Lifespring's pre-notification HP store.

This is static evidence, not game execution or a universal amplification model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
CALLS = {0x83c68e: 0x92e950, 0x92e9ae: 0x92f720,
         0x94f2bc: 0x93ead0, 0x93eb54: 0x95f270,
         0x93eb6b: 0x86f300, 0x93ec29: 0x539400}
SLICES = {
    'producer_missing_hp_and_threshold': (0x83c621, 0x83c647),
    'producer_action_fields': (0x83c647, 0x83c693),
    'clone_amount_and_flags': (0x92e984, 0x92e9b3),
    'apply_hp_gate_and_unchanged_operand': (0x94f294, 0x94f2c3),
    'add_and_post_store_notification': (0x93eb40, 0x93eb70),
    'resource_zero_store_complete_branch': (0x95f270, 0x95f2ec),
}
# Instruction-aligned assertions complement whole-image and bounded slice hashes.
CHECKS = {
    0x83c629: 'f30f5c45f0d95de8f30f5945e8f30f59833c0200000f2f05c4422101764c',
    0x92e993: '8b4318894618',
    0x94f2a1: '8b41200f57c00f2f80f00200007326',
    0x94f2b0: 'f30f10461851f30f11042452',
    0x93eb40: 'f30f1084b1f0020000f30f58c151f30f11042456',
    0x93eb60: '8d450c5056ff355030a701',
    0x95f278: '0f57db8b4508f30f5fc3f30f118481f002000085c0755d',
    0x95f2d4: 'f30f5d81f0020000f30f5fc3f30f1181f00200005dc20800',
}


def inspect(binary):
    blob = Path(binary).read_bytes()
    if hashlib.sha256(blob).hexdigest() != SHA256:
        raise ValueError('Selected executable SHA-256 differs')
    pe = struct.unpack_from('<I', blob, 60)[0]
    count = struct.unpack_from('<H', blob, pe + 6)[0]
    opt, size = pe + 24, struct.unpack_from('<H', blob, pe + 20)[0]
    base = struct.unpack_from('<I', blob, opt + 28)[0]

    def read(va, length):
        for index in range(count):
            rva, raw_size, raw = struct.unpack_from('<III', blob, opt + size + index * 40 + 12)
            delta = va - base - rva
            if 0 <= delta and delta + length <= raw_size:
                return blob[raw + delta:raw + delta + length]
        raise ValueError('Address not file backed')

    for va, expected in CHECKS.items():
        if read(va, len(bytes.fromhex(expected))) != bytes.fromhex(expected):
            raise ValueError(f'Instruction bytes differ at {va:08x}')
    for site, target in CALLS.items():
        code = read(site, 5)
        if code[0] != 0xe8 or site + 5 + struct.unpack_from('<i', code, 1)[0] != target:
            raise ValueError('Direct call differs')
    if struct.unpack('<I', read(0x127c9bc, 4))[0] != 0x94f210:
        raise ValueError('Action apply vtable edge differs')
    if read(0x12142c4, 4) != bytes.fromhex('0000803f'):
        raise ValueError('Threshold/additive identity constant differs')
    return {
        'schema': 'vg.lifespring-hp-boundary.v1', 'binary_sha256': SHA256,
        'scope': 'Static selected path through first HP store; no runtime, callback completion or server claims',
        'calls': [{'site': f'{site:08x}', 'target': f'{target:08x}'} for site, target in CALLS.items()],
        'vtable_apply': {'site': '0127c9bc', 'target': '0094f210'},
        'slices': [{'name': name, 'start': f'{start:08x}', 'end_exclusive': f'{end:08x}',
                    'sha256': hashlib.sha256(read(start, end - start)).hexdigest()}
                   for name, (start, end) in SLICES.items()],
        'instruction_checks': [{'site': f'{va:08x}', 'bytes': raw} for va, raw in CHECKS.items()],
        'notification_operand': 'address of original requested ADD operand, not recomputed stored-minus-old delta',
        'amp_scope': 'No stat33..36 calculation in selected producer, unchanged action-copy/apply, ADD or resource0 setter branch; indirect callbacks and upstream inputs remain outside scope',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.binary), indent=2))
