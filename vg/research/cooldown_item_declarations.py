"""Extract hash-pinned item stat 15/25 declarations and inline cooldown flags.

Raw declaration values only: no operation-code interpretation or runtime state.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from vg.core.cff_resource import CatalogError, load_cff
from vg.research.passive_item_catalog import read_metadata, decode_item, METADATA, METADATA_SHA256
from vg.research.verify_sequential_pe import EXPECTED_SHA256


def finite_duration(base, additive=0, multiplier=1, override=-1, *,
                    reduction=None, speed=None, reduction_bounds=(0, .3499999940395355),
                    speed_bounds=None):
    """Finite float32 instruction-order witness, not a running-timer reducer.

    Bounds are explicit scenario inputs. Defaults reflect the selected startup
    hypothesis; neither the defaults nor this model measure a runtime actor.
    Reject nonfinite inputs rather than approximate native SSE unordered cases.
    """
    if speed is not None and speed_bounds is None:
        raise ValueError('Explicit speed bounds required')
    values = [base, additive, multiplier, override, *reduction_bounds, *(speed_bounds or ())]
    values += [value for value in (reduction, speed) if value is not None]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Finite witness inputs required')
    def f32(value):
        return struct.unpack('<f', struct.pack('<f', value))[0]
    base, additive, multiplier, override = map(f32, (base, additive, multiplier, override))
    duration = override if override >= 0 else f32(f32(additive + base) * multiplier)
    if reduction is not None:
        lower, upper = map(f32, reduction_bounds)
        factor = max(lower, min(upper, f32(reduction)))
        duration = f32(duration * f32(1 - factor))
    if speed is not None:
        lower, upper = map(f32, speed_bounds)
        divisor = max(1, max(lower, min(upper, f32(speed))))
        duration = f32(duration / divisor)
    return duration


def fields(decoded):
    data, reloc = decoded.inst, decoded.relocations
    root = struct.unpack_from('<I', decoded.symbol)[0]

    def word(at):
        if at < 0 or at + 4 > len(data):
            raise CatalogError('Declaration out of bounds')
        return struct.unpack_from('<I', data, at)[0]

    def pointer(at):
        if at in reloc:
            return reloc[at]
        if word(at) == 0:
            return None
        raise CatalogError('Missing declaration relocation')

    attributes = []
    table = pointer(root + 0x2c)
    if table is not None:
        for index in range(256):
            entry = pointer(table + 4 * index)
            if entry is None:
                break
            stat = word(entry)
            if stat in (15, 25):
                bits = word(entry + 4)
                value = struct.unpack('<f', struct.pack('<I', bits))[0]
                attributes.append({'index': index, 'stat_id': stat,
                    'value_bits': f'{bits:08x}',
                    'value': value if math.isfinite(value) else None,
                    'secondary_bits': f'{word(entry + 8):08x}',
                    'operation_raw': word(entry + 12)})
        else:
            raise CatalogError('Attribute array lacks bounded sentinel')
    active = data[root + 0x38]
    external = pointer(root + 0x3c)
    # An allocated empty string has the same native branch as a null string.
    if external is not None and not 0 <= external < len(data):
        raise CatalogError('External name out of bounds')
    inline = bool(active and (external is None or data[external] == 0))
    flags = {f'ability_0x{offset:x}': data[root + 0x40 + offset]
             for offset in (0x24, 0x25, 0x6d)} if inline else None
    return {'selected_attributes': attributes, 'inline_ability_flags_raw': flags}


def inspect(binary, data_root):
    executable = Path(binary).read_bytes()
    if hashlib.sha256(executable).hexdigest() != EXPECTED_SHA256:
        raise CatalogError('Executable SHA-256 mismatch')
    catalog = read_metadata(METADATA)
    rows = []
    for identity, row in sorted(catalog['definitions'].items(), key=lambda x: int(x[0])):
        name = row['resource_name']
        resource = (Path(data_root) / name[:2] / name).read_bytes()
        # Reuse exact symbol/name validation, not just a root pointer guess.
        base = decode_item(resource, executable, row)
        decoded = load_cff(resource, executable, build_sha256=EXPECTED_SHA256,
            resource_sha256=row['resource_sha256'], key_table_va=0x1e3f978, version=12)
        rows.append({'definition_index': int(identity), 'definition_name': row['definition_name'],
            'resource_name': name, 'resource_sha256': row['resource_sha256'],
            'quantity_rules_declared': {k: row[k] for k in ('stackable', 'max_stack', 'grant_skip', 'unique')},
            'active_capability_byte': base['active_capability_byte'],
            'external_ability_name_declared': base['external_ability_name_declared'], **fields(decoded)})
    return {'schema': 'vg.cooldown-item-declarations.v1', 'build_sha256': EXPECTED_SHA256,
        'metadata_sha256': METADATA_SHA256, 'item_count': len(rows),
        'scope': 'Raw local declarations; operation codes, effective stats and runtime item ownership are not inferred.',
        'items': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--data-root', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.binary, args.data_root), indent=2, allow_nan=False))
