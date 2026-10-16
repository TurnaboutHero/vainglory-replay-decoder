"""Read selected local names, item declarations and bounded native registry edges.

No game execution, asset modification, shop-availability or effect-state inference.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct

from vg.core.cff_resource import CatalogError, load_cff
from vg.core.definition_catalog import BuildProfile, load_catalog
from vg.research.passive_item_catalog import read_metadata, decode_item, METADATA
from vg.research.verify_sequential_pe import EXPECTED_SHA256

MANIFEST = ('03A640B504C2B4D7C8CBF3A04E189223',
            '7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c')
LOCALES = {
    'ko': ('AE9CB5A29032FAFA098A4BBE22C79B84', '610d2d6a3a543a11ffa555284ddcc3ce90af2aa1b7b54afb99a6dcf98b469a5e'),
    'en': ('7ED4F1146624D2D991A07272993B26C4', '209df4c745201dec58bd5ef2497f1835298b21cbc8f23bd1bb1669589462d8d4'),
}
REGISTRY_NAMES = (
    'Ability__Item__NullwaveGauntlet', 'Buff_Item_EMP_Countdown',
    'Buff_Item_EMP_ItemSilence', 'Buff_Item_CapacitorPlate_Control',
    'Buff_Item_CapacitorPlate_SpeedBoost', 'Buff_Item_CapacitorPlate_Lockout',
    'Buff_Phinn_PoliteCompany_FortifiedHealth', 'Ability__Phinn__B',
    'Ability__Reim__B', 'Buff_Reim_Perk_Frost', 'Ability__Lyra__A',
)


def inspect(binary, data_root):
    executable = Path(binary).read_bytes()
    if hashlib.sha256(executable).hexdigest() != EXPECTED_SHA256:
        raise CatalogError('Executable SHA-256 mismatch')
    data_root = Path(data_root)

    def resource(identity, digest):
        data = (data_root / identity[:2] / identity).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise CatalogError('Resource SHA-256 mismatch')
        return data

    locales = {}
    for language, (identity, digest) in LOCALES.items():
        text = base64.b64decode(resource(identity, digest), validate=True).decode('utf-8')
        pairs = re.findall(r'^"([^"\r\n]+)"\s*=\s*"((?:\\.|[^"\\])*)";', text, re.M)
        entries = dict(pairs)
        if len(entries) != 7322 or len(entries) != len(pairs):
            raise CatalogError('Localization count or unique keys differs')
        selected = {k: v for k, v in entries.items() if
                    k.startswith(('STORE_ITEM_NULLWAVE_GAUNTLET_', 'STORE_ITEM_CAPACITOR_PLATE_')) or
                    k in ('CHAR_INFO_REIM_NAME', 'CHAR_INFO_PHINN_NAME', 'CHAR_INFO_LYRA_NAME') or
                    k.startswith(('HERO_ABILITY_REIM_B_', 'HERO_ABILITY_PHINN_B_', 'HERO_ABILITY_LYRA_A_'))}
        locales[language] = {'resource_id': identity, 'sha256': digest, 'entry_count': len(entries),
                             'selected_entries': selected,
                             'echo_item_key_matches': [k for k in entries if k.startswith('STORE_ITEM_') and 'ECHO' in k],
                             'exact_echo_name_matches': [k for k, v in entries.items() if v in ('메아리', 'Echo')]}

    profile = BuildProfile(EXPECTED_SHA256, MANIFEST[1], 0x1e3f978, 12, 932)
    catalog = load_catalog(resource(*MANIFEST), executable, profile)
    item_names = [x.serialized_name for x in catalog.definitions if x.name.startswith('Item_')]
    metadata = read_metadata(METADATA)
    items = []
    for identity in ('521', '534'):
        row = metadata['definitions'][identity]
        raw = resource(row['resource_name'], row['resource_sha256'])
        base = decode_item(raw, executable, row)
        decoded = load_cff(raw, executable, build_sha256=EXPECTED_SHA256,
                           resource_sha256=row['resource_sha256'], key_table_va=0x1e3f978, version=12)
        root = struct.unpack_from('<I', decoded.symbol)[0]

        def string_pointer(at):
            ptr = decoded.relocations[at]
            return decoded.inst[ptr:decoded.inst.index(0, ptr)].decode('ascii')

        inline_properties = []
        if base['active_capability_byte'] and not base['external_ability_name_declared']:
            table = decoded.relocations[root + 0xcc]
            for index in range(128):
                slot = table + index * 4
                if struct.unpack_from('<I', decoded.inst, slot)[0] == 0:
                    break
                at = decoded.relocations[slot]
                bits = struct.unpack_from('<I', decoded.inst, at + 4)[0]
                inline_properties.append({'index': index, 'name': string_pointer(at),
                    'selector_1_bits': f'{bits:08x}',
                    'selector_1_value': struct.unpack_from('<f', decoded.inst, at + 4)[0]})
            else:
                raise CatalogError('Inline property sentinel missing')
        items.append({'definition_index': int(identity), 'definition_name': row['definition_name'],
            'resource_id': row['resource_name'], 'resource_sha256': row['resource_sha256'],
            'localization_key_at_root_08': string_pointer(root + 8),
            'presentation_hidden_declared': row['hud_hidden'],
            'inline_ability_properties': inline_properties, **base})

    pe = struct.unpack_from('<I', executable, 60)[0]
    count = struct.unpack_from('<H', executable, pe + 6)[0]
    optional = pe + 24
    size = struct.unpack_from('<H', executable, pe + 20)[0]
    image_base = struct.unpack_from('<I', executable, optional + 28)[0]
    sections = [struct.unpack_from('<IIII', executable, optional + size + i * 40 + 8) for i in range(count)]

    def offset_to_va(offset):
        for _, rva, raw_size, raw in sections:
            if raw <= offset < raw + raw_size:
                return image_base + rva + offset - raw
        raise CatalogError('File offset is not section-backed')

    def read(va, length):
        for _, rva, raw_size, raw in sections:
            delta = va - image_base - rva
            if 0 <= delta and delta + length <= raw_size:
                return executable[raw + delta:raw + delta + length]
        raise CatalogError('VA is not file-backed')

    registry = []
    for name in REGISTRY_NAMES:
        matches = list(re.finditer(re.escape(name.encode('ascii') + b'\0'), executable))
        if len(matches) != 1:
            raise CatalogError('Selected name is not unique')
        string_va = offset_to_va(matches[0].start())
        rows = []
        for pointer in re.finditer(re.escape(struct.pack('<I', string_va)), executable):
            name_global = offset_to_va(pointer.start())
            pattern = b'\xa1' + re.escape(struct.pack('<I', name_global)) + b'\xa3(.{4})'
            for code in re.finditer(pattern, executable, re.S):
                entry = struct.unpack('<I', code.group(1))[0]
                target = struct.unpack('<I', read(entry + 4, 4))[0]
                read(target, 1)
                rows.append({'name': name, 'string_va': f'{string_va:08x}',
                    'name_global': f'{name_global:08x}', 'copy_site': f'{offset_to_va(code.start()):08x}',
                    'entry': f'{entry:08x}', 'factory_candidate': f'{target:08x}'})
        if len(rows) != 1:
            raise CatalogError('Selected registry pair is not unique')
        registry.extend(rows)

    thunk_rows = []
    for va, expected_index in ((0x8676a0, 1), (0x8676d0, 0), (0x867700, 4), (0x867730, 3), (0x867760, 2)):
        code = read(va, 36)
        if code[:4] != bytes.fromhex('6a00ff35') or code[8:10] != bytes.fromhex('6a00') or code[22:26] != bytes((0x6a, 1, 0x6a, expected_index)) or code[32:] != bytes.fromhex('83c40cc3'):
            raise CatalogError('Capacitor property thunk differs')
        name_pointer = struct.unpack_from('<I', code, 4)[0]
        symbol_pointer = struct.unpack('<I', read(name_pointer, 4))[0]
        if read(symbol_pointer, 22).split(b'\0')[0] != b'*Item_CapacitorPlate*':
            raise CatalogError('Capacitor property symbol differs')
        calls = []
        for delta in (10, 17, 27):
            if code[delta] != 0xe8:
                raise CatalogError('Property thunk direct call missing')
            target = va + delta + 5 + struct.unpack_from('<i', code, delta + 1)[0]
            calls.append(f'{target:08x}')
        thunk_rows.append({'va': f'{va:08x}', 'selector': 1, 'property_index': expected_index, 'direct_call_targets': calls})
    edges = {0x127ba4c: 0x949520, 0x121b810: 0x8627f0,
             0x121b428 + 4: 0x45ecd0, 0x121b134 + 4: 0x45ecd0,
             0x121b2e4 + 4: 0x45ecd0, 0x127db6c + 0xc: 0x860cb0}
    for site, target in edges.items():
        if struct.unpack('<I', read(site, 4))[0] != target:
            raise CatalogError('Selected vtable edge differs')
    if read(0x45ecd0, 3) != bytes.fromhex('c20400'):
        raise CatalogError('Folded ret 4 dispatch differs')
    if read(0x4b7c00, 3) != bytes.fromhex('d9eec3'):
        raise CatalogError('Shared resource calculation stub differs')
    return {'schema': 'vg.capacitor-retired-evidence.v1', 'build_sha256': EXPECTED_SHA256,
        'scope': 'Selected local static evidence; no runtime, shop purchase, hit acceptance or cleanup claims.',
        'localization': locales, 'manifest': {'resource_id': MANIFEST[0], 'sha256': MANIFEST[1],
            'definition_count': 932, 'item_definition_count': len(item_names),
            'echo_item_name_matches': [x for x in item_names if 'echo' in x.lower()]},
        'items': items, 'registry_candidates': registry, 'capacitor_property_thunks': thunk_rows,
        'selected_vtable_edges': [{'site': f'{site:08x}', 'target': f'{target:08x}'}
                                 for site, target in edges.items()],
        'folded_dispatch': {'address': '0045ecd0', 'bytes': 'c20400', 'operation': 'ret 4'},
        'shared_resource_calculation_stub': {'address': '004b7c00', 'bytes': 'd9eec3',
            'operation': 'fldz; ret', 'meaning': 'Returns x87 zero on this selected file-backed path.'},
        'bounded_native_echo_search': {'tokens': ['Item_Echo', 'Ability__Item__Echo', 'Buff_Item_Echo'],
            'present_tokens': [x for x in ('Item_Echo', 'Ability__Item__Echo', 'Buff_Item_Echo') if x.encode() in executable],
            'meaning': 'Exact token absence only; renamed, inlined, unused resource or older-build implementations remain outside this proof.'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--output', type=Path, help='Optional UTF-8 research JSON output path')
    args = parser.parse_args()
    result = inspect(args.binary, args.data_root)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    else:
        # ASCII JSON escapes remain lossless on Windows legacy console encodings.
        print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
