"""Hash-gated static Capacitor consumer candidates and initialization edges.

Byte-pattern candidates do not establish instruction boundaries or runtime effects.
Pair the output with the REA function/xref receipts in the accompanying report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from vg.core.cff_resource import load_cff

SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
NAMES = {33: 'INCOMING_BARRIER_AMP', 34: 'OUTGOING_BARRIER_AMP',
         35: 'INCOMING_HEAL_AMP', 36: 'OUTGOING_HEAL_AMP'}
HEROES = {
    'Phinn': ('4AB809A4E9DFF0585281C1AB70EAF2BC', '4df3571ea1e7cbd33a95ec068ba82f99c496b9d11beeee3549e76b54a3f0f9cf'),
    'Reim': ('E69FFAF512614E619DEA07FF9CCA56E8', 'daf3c1e1c840ac17fe51a510597e8850d5dfbc92127c83dbc1bb41f84c2839fe'),
}


def inspect(binary, data_root=None):
    blob = Path(binary).read_bytes()
    if hashlib.sha256(blob).hexdigest() != SHA256:
        raise ValueError('Selected executable SHA-256 differs')
    pe = struct.unpack_from('<I', blob, 60)[0]
    count = struct.unpack_from('<H', blob, pe + 6)[0]
    optional = pe + 24
    optional_size = struct.unpack_from('<H', blob, pe + 20)[0]
    image_base = struct.unpack_from('<I', blob, optional + 28)[0]
    sections = []
    for index in range(count):
        at = optional + optional_size + index * 40
        _, rva, length, offset = struct.unpack_from('<IIII', blob, at + 8)
        flags = struct.unpack_from('<I', blob, at + 36)[0]
        sections.append((image_base + rva, blob[offset:offset + length], bool(flags & 0x20000000)))

    def read(va, length):
        for start, data, _ in sections:
            delta = va - start
            if 0 <= delta and delta + length <= len(data):
                return data[delta:delta + length]
        raise ValueError('Selected address is not file-backed')

    def require(va, expected):
        if read(va, len(expected)) != expected:
            raise ValueError(f'Expected selected bytes differ at {va:08x}')

    def literal_sites(value, executable_only=False):
        needle = struct.pack('<I', value)
        rows = []
        for start, data, executable in sections:
            if executable_only and not executable:
                continue
            offset = data.find(needle)
            while offset >= 0:
                rows.append({'site': f'{start + offset:08x}', 'executable_section': executable})
                offset = data.find(needle, offset + 1)
        return rows

    direct_calls = {}
    for target in (0x4b7c00, 0x860cb0, 0x937480):
        rows = []
        for start, data, executable in sections:
            if not executable:
                continue
            offset = data.find(b'\xe8')
            while offset >= 0:
                if offset + 5 <= len(data):
                    resolved = start + offset + 5 + struct.unpack_from('<i', data, offset + 1)[0]
                    if resolved == target:
                        rows.append({'site': f'{start + offset:08x}',
                                     'preceding_24_bytes': data[max(0, offset - 24):offset].hex()})
                offset = data.find(b'\xe8', offset + 1)
        direct_calls[f'{target:08x}'] = rows
    if [x['site'] for x in direct_calls['004b7c00']] != ['00860d1c', '00860d35']:
        raise ValueError('Shared resource calculation candidate calls differ')
    require(0x4b7c00, bytes.fromhex('d9eec3'))
    require(0x44e000, bytes.fromhex('a1bcc08601'))
    require(0x186c0bc, bytes.fromhex('ffff7f7f'))
    require(0x44e16d, bytes.fromhex('0f2805102321010f11051861a701'))
    require(0x44e17b, bytes.fromhex('c7052861a701000080bf'))
    require(0x1212310, bytes.fromhex('00000000000080bf000080bf000080bf'))
    attributes = []
    for stat, name in NAMES.items():
        upper, lower = 0x20e7348 + 4 * stat, 0x1a76098 + 4 * stat
        site = {33: 0x44e0b6, 34: 0x44e0bb, 35: 0x44e0c0, 36: 0x44e0c5}[stat]
        require(site, b'\xa3' + struct.pack('<I', upper))
        attributes.append({'stat_id': stat, 'name': name,
            'actor_component_offsets': {'layer0': f'{0x20 + stat * 4:x}',
                'layer1': f'{0xd4 + stat * 4:x}', 'layer2': f'{0x188 + stat * 4:x}',
                'layer3': f'{0x23c + stat * 4:x}'},
            'upper': {'address': f'{upper:08x}', 'initializer_store': f'{site:08x}',
                      'initialized_bits': '7f7fffff', 'executable_literal_candidates': literal_sites(upper, True)},
            'lower': {'address': f'{lower:08x}', 'file_backed_bits_before_startup': read(lower, 4).hex(),
                      'initialized_bits': 'bf800000',
                      'initializer_source': f'{0x1212310 + 4 * (stat - 32):08x}' if stat < 36 else 'immediate at 0044e181',
                      'executable_literal_candidates': literal_sites(lower, True)}})
    vtables = []
    for name, base in [('ModifyAttribute', 0x121b2e4),
                       ('GrantTemporaryResourceNew', 0x121b134),
                       ('ApplyBuffToSelection', 0x121b428)]:
        targets = struct.unpack('<4I', read(base + 4, 16))
        if targets != (0x45ecd0,) * 4:
            raise ValueError('Selected behavior lifecycle dispatch differs')
        vtables.append({'class_suffix': name, 'vtable': f'{base:08x}',
                        'slots': {f'{index * 4:02x}': f'{target:08x}' for index, target in enumerate(targets, 1)}})
    require(0x45ecd0, bytes.fromhex('c20400'))
    require(0x528fc0, bytes.fromhex('8bc1c20800'))
    require(0x529040, bytes.fromhex('8bc1c20c00'))
    require(0x95775b, bytes.fromhex('8d4f20'))
    constructor_call = read(0x95776a, 5)
    if constructor_call[0] != 0xe8 or 0x95776f + struct.unpack_from('<i', constructor_call, 1)[0] != 0x81c640:
        raise ValueError('Actor attribute initializer call differs')
    require(0x81c640, bytes.fromhex('c78110030000000000008d8168010000c7811403000000000000ba2d00000090'))
    require(0x81c660, bytes.fromhex('c78098feffff000000008d4004c78048ffffff00000000c740fc00000000c780b00000000000000083ea0175d3'))
    require(0x81c68d, bytes.fromhex('0f57c08bc10f1181d00200000f1181e00200000f1181f00200000f118100030000c3'))
    require(0x847620, bytes.fromhex('e90ba6ffff'))
    reim_jump_target = 0x847620 + 5 + struct.unpack('<i', read(0x847621, 4))[0]
    if reim_jump_target != 0x841c30:
        raise ValueError('Reim post-attack jump target differs')
    # A folded-code alias is unrelated to temporary resource semantics.
    require(0x121e9ac, struct.pack('<I', 0x187a61c))
    require(0x187a61c + 12, struct.pack('<I', 0x1e4f2c8))
    alias = read(0x1e4f2c8 + 8, 96).split(b'\0', 1)[0].decode('ascii')
    if alias != '.?AVCKinSetActorRepUniform@Kindred@Nuo@@':
        raise ValueError('Folded alias RTTI differs')
    result = {'schema': 'vg.capacitor-value-paths.v1', 'build_sha256': SHA256,
        'scope': 'Static byte candidates only. REA must corroborate boundaries and semantics; no live stat/effect claims.',
        'direct_E8_candidates': direct_calls,
        'literal_pointer_candidates': {f'{target:08x}': literal_sites(target) for target in (0x4b7c00, 0x860cb0)},
        'attributes': attributes, 'behavior_lifecycle_slots': vtables,
        'shared_calculation_bytes': 'd9eec3',
        'configuration_stubs': [
            {'address': '00528fc0', 'bytes': '8bc1c20800', 'meaning': 'mov eax,ecx; ret 8; no stores'},
            {'address': '00529040', 'bytes': '8bc1c20c00', 'meaning': 'mov eax,ecx; ret 12; no stores'}],
        'reim_post_attack_jump': {'source': '00847620', 'bytes': 'e90ba6ffff', 'target': f'{reim_jump_target:08x}'},
        'actor_attribute_constructor': {'wrapper_vtable_operand_site': '00957760',
            'raw_stat_base': 'actor attribute component +20', 'call_site': '0095776a',
            'initializer': '0081c640', 'body_bytes': 111,
            'body_sha256': hashlib.sha256(read(0x81c640, 111)).hexdigest(),
            'loop_iterations': 45, 'initial_layer0_1_2_3_bits': ['00000000'] * 4,
            'scope': 'Construction only; later definition, action, grant and replicated state writes can differ.'},
        'folded_alias': {'vtable': '0121e9b0', 'slot': '0c', 'rtti': alias},
        'raw_stat_formula': '((layer3 + 1) * layer1 + layer0) * (layer2 + 1)',
        'formula_scope': '00937480 selector -1; this is an un-clamped four-layer getter, not amount amplification or proof of contribution lifetime.'}
    if data_root is not None:
        heroes = []
        for name, (identity, digest) in HEROES.items():
            raw = (Path(data_root) / identity[:2] / identity).read_bytes()
            decoded = load_cff(raw, blob, build_sha256=SHA256, resource_sha256=digest,
                               key_table_va=0x1e3f978, version=12)
            root, kind = struct.unpack_from('<II', decoded.symbol)
            if root != 0 or kind != 0x2419fb6c or decoded.symbol[8:].split(b'\0')[0] != ('*' + name + '*').encode():
                raise ValueError('Actor definition symbol differs')

            def text_pointer(at):
                offset = decoded.relocations[at]
                end = decoded.inst.find(b'\0', offset, min(offset + 257, len(decoded.inst)))
                if end < 0:
                    raise ValueError('Property/name text lacks bounded terminator')
                return decoded.inst[offset:end].decode('ascii')

            def properties(table_at, selected=None):
                table = decoded.relocations[table_at]
                rows = []
                for index in range(128):
                    slot = table + index * 4
                    entry = decoded.relocations.get(slot)
                    if entry is None:
                        if struct.unpack_from('<I', decoded.inst, slot)[0] != 0:
                            raise ValueError('Property table relocation missing')
                        return rows
                    if selected is None or index in selected:
                        rows.append({'index': index, 'entry_offset': f'{entry:x}', 'name': text_pointer(entry),
                            'raw_fields': {f'{offset:02x}': {'bits': f'{struct.unpack_from("<I", decoded.inst, entry + offset)[0]:08x}',
                                                          'float': struct.unpack_from('<f', decoded.inst, entry + offset)[0]}
                                           for offset in (4, 8, 12)}})
                raise ValueError('Property table sentinel missing')

            ability_table = decoded.relocations[root + 0x64]
            ability = decoded.relocations[ability_table + 4]
            ability_name = text_pointer(ability + 4)
            if ability_name != f'Ability__{name}__B':
                raise ValueError('Actor B ability identity differs')
            heroes.append({'name': name, 'resource_id': identity, 'resource_sha256': digest,
                'root_64_ability_pointer_array': f'{ability_table:x}', 'ability_index': 1,
                'ability_offset': f'{ability:x}', 'ability_name': ability_name,
                'B_properties': properties(ability + 0x8c, {5, 6, 7, 8, 9} if name == 'Phinn' else None),
                'perk_properties': properties(root + 0x1a8, set(range(6, 11)) if name == 'Reim' else {0}),
                'raw_field_scope': 'Declaration bytes only; +08/+0c are not assigned rank/overdrive algebra without their native getter.'})
        result['hero_declarations'] = heroes
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--data-root')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect(args.binary, args.data_root)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8', newline='\n')
    else:
        print(text, end='')
