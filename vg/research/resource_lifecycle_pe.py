"""Selected-build static resource cleanup receipts; never a replay state reducer."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
EDGES = (
    (0x966568, 0x92d6a0, 0xe9),  # ordinary timeout tail
    (0x92d6a8, 0x95f4d0, 0xe8),  # end: zero stacks, notify
    (0x9664e0, 0x95f4d0, 0xe8),  # alternate timeout zero-stacks path
    (0x860d97, 0x858a70, 0xe8),  # zero count, valid handle
    (0x842053, 0x858a70, 0xe8),  # selected state-4 branch
    (0x858aee, 0x92e950, 0xe8),  # clone/enqueue negative remainder
    (0x858af5, 0x112a080, 0xe8), # mark component-pool bit
    (0x92c137, 0x966570, 0xe8), # death state request, not scalar reset
)
SPANS = (
    (0x858a70, 0x858b0a, 'negative-remainder-action'),
    (0x860cb0, 0x860ed7, 'temporary-resource-stack-hook'),
    (0x841f00, 0x8420e6, 'selected-state4-and-decay'),
    (0x95f4d0, 0x95f5a1, 'stack-setter'),
    (0x966410, 0x96656d, 'timeout-contiguous-body'),
    (0x92d6a0, 0x92d777, 'buff-end'),
    (0x112a080, 0x112a0c2, 'pool-bit-mark'),
    (0x92c110, 0x92c237, 'death-state-and-callback'),
    (0x9572b0, 0x95764b, 'respawn-contiguous-span'),
)


def relative_target(read, site, opcode):
    raw = read(site, 5)
    if len(raw) != 5 or raw[0] != opcode:
        raise ValueError(f'Expected relative instruction at {site:08x}')
    return (site + 5 + struct.unpack('<i', raw[1:])[0]) & 0xffffffff


def verify(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Selected executable SHA-256 differs')
    pe = struct.unpack_from('<I', data, 60)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    opt = pe + 24
    size = struct.unpack_from('<H', data, pe + 20)[0]
    base = struct.unpack_from('<I', data, opt + 28)[0]

    def read(va, length):
        for i in range(count):
            rva, raw_size, raw = struct.unpack_from('<III', data, opt + size + i * 40 + 12)
            delta = va - base - rva
            if 0 <= delta and delta + length <= raw_size:
                result = data[raw + delta:raw + delta + length]
                if len(result) == length:
                    return result
        raise ValueError('Address not file backed')

    rows = []
    for site, target, opcode in EDGES:
        if relative_target(read, site, opcode) != target:
            raise ValueError(f'Selected edge differs at {site:08x}')
        rows.append({'site': f'{site:08x}', 'target': f'{target:08x}',
                     'kind': 'call' if opcode == 0xe8 else 'tail-jump'})
    checks = {
        0x127db78: struct.pack('<I', 0x860cb0),
        0x95f566: bytes.fromhex('ff500c'),
        0x858aaa: bytes.fromhex('f30f104620'),
        0x858aaf: bytes.fromhex('0f570500232101'),
        0x1212300: struct.pack('<4I', *([0x80000000] * 4)),
        0x858ac3: bytes.fromhex('c745d4b4c92701'),
        0x858ad5: bytes.fromhex('66c745f00001'),
        0x860d4a: bytes.fromhex('0fb78750020000'),
        0x842049: bytes.fromhex('66837c305004'),
    }
    for site, expected in checks.items():
        if read(site, len(expected)) != expected:
            raise ValueError(f'Selected operand/dispatch differs at {site:08x}')
    return {
        'schema': 'vg.resource-lifecycle-pe.v1', 'binary_sha256': SHA256,
        'edges': rows,
        'selected_checks': [{'site': f'{s:08x}', 'size': len(b),
                             'sha256': hashlib.sha256(b).hexdigest()} for s, b in checks.items()],
        'spans': [{'start': f'{a:08x}', 'end_exclusive': f'{b:08x}', 'purpose': name,
                   'sha256': hashlib.sha256(read(a, b-a)).hexdigest()} for a, b, name in SPANS],
        'scope': 'Selected static bytes only. No native execution, exhaustive writer coverage, '
                 'replay-build match, expiry cause attribution, or current resource reconstruction.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = json.dumps(verify(args.binary), indent=2) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
