"""Optional private-corpus check: PYTHONPATH=. python this_file.py H5810_DIR.

Reads only; prints JSON. No client execution or inferred state validation.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

from vg.analysis.native_event_fields import decode_fields
from vg.core.vgr_records import iter_records


def audit(root):
    counts, modes, charges = Counter(), Counter(), Counter()
    configs = defaultdict(set)
    hashes = {}
    records = 0
    for path in sorted(Path(root).glob('*.vgr')):
        if path.name.startswith('._'):
            continue
        data = path.read_bytes()
        hashes[path.name] = hashlib.sha256(data).hexdigest()
        for record in iter_records(data):
            records += 1
            if record.opcode not in (0x0428, 0x0429, 0x048a):
                continue
            fields = decode_fields(record)
            assert fields['decoding_status'] == 'decoded'
            json.dumps(fields, allow_nan=False)
            counts[f'{record.opcode:04x}'] += 1
            if record.opcode == 0x0428:
                modes[fields['native_operation']] += 1
            elif record.opcode == 0x0429:
                charges[(fields['ref0'], fields['native_ability_slot_index'],
                         fields['native_operand_raw'], fields['native_mode_raw'])] += 1
            else:
                configs[(fields['ref0'], fields['native_lookup_key'])].add((
                    fields['native_config_value_bits'],
                    *[fields[f'native_byte{i}_raw'] for i in range(17, 22)]))
    assert counts == {'0428': 1859, '0429': 109, '048a': 21001}, counts
    assert records == 663517, records
    assert modes == {'relative': 645, 'direct': 1214}, modes
    assert charges == {(1504, 0, 4, 1): 109}, charges
    assert len(configs) == 148 and sum(len(v) > 1 for v in configs.values()) == 31
    return {
        'files': len(hashes), 'records': records, 'counts': dict(counts),
        '0428_modes': dict(modes), '0429_tuples': [[*k, v] for k, v in charges.items()],
        '048a_owner_key_pairs': len(configs),
        '048a_pairs_with_config_changes': sum(len(v) > 1 for v in configs.values()),
        'framing_errors': 0, 'source_sha256': hashes,
    }


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), indent=2))
