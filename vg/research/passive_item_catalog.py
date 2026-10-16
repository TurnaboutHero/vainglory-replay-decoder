"""Read hash-pinned local item declarations; no inventory/effect state inference."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from vg.core.cff_resource import CatalogError, load_cff
from vg.research.verify_sequential_pe import EXPECTED_SHA256

METADATA = Path(__file__).resolve().parents[1] / 'core/native_inventory_definitions.json'
METADATA_SHA256 = 'e40df722ee5eaff7ff63e21403944bbf6de35eb84126f8fe0ce27e7bc66d0783'
CATALOG_BUILD = '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642'


def read_metadata(path):
    data = Path(path).read_bytes().replace(b'\r\n', b'\n')
    if hashlib.sha256(data).hexdigest() != METADATA_SHA256:
        raise CatalogError('Inventory metadata SHA-256 mismatch')
    result = json.loads(data)
    if result['build_sha256'] != CATALOG_BUILD:
        raise CatalogError('Inventory metadata provenance differs')
    return result


def decode_item(resource, executable, row):
    decoded = load_cff(resource, executable, build_sha256=EXPECTED_SHA256,
                       resource_sha256=row['resource_sha256'], key_table_va=0x1e3f978,
                       version=12)
    data, reloc = decoded.inst, decoded.relocations

    def span(at, size):
        if at < 0 or at > len(data) - size:
            raise CatalogError('Item declaration range out of bounds')
        return data[at:at + size]

    def word(at):
        return struct.unpack('<I', span(at, 4))[0]

    def text(at):
        span(at, 1)
        end = data.find(b'\0', at, min(at + 257, len(data)))
        if end < 0:
            raise CatalogError('Unterminated declaration label')
        try:
            return data[at:end].decode('ascii')
        except UnicodeDecodeError as error:
            raise CatalogError('Non-ASCII declaration label') from error

    def pointer(at):
        if at in reloc:
            return reloc[at]
        if word(at) == 0:
            return None
        raise CatalogError('Missing item declaration relocation')

    def string_pointer(at):
        target = pointer(at)
        return '' if target is None else text(target)

    if len(decoded.symbol) < 9:
        raise CatalogError('Short item symbol')
    root, kind = struct.unpack_from('<II', decoded.symbol)
    if kind != 0xfc7583e1 or decoded.symbol[8:].split(b'\0')[0] != ('*' + row['definition_name'] + '*').encode('ascii'):
        raise CatalogError('Item symbol differs from metadata')
    active_byte = span(root + 0x38, 1)[0]
    external = string_pointer(root + 0x3c)
    declared_buffs = []
    buff_table = pointer(root + 0x30)
    if buff_table is not None:
        for index in range(256):
            entry = pointer(buff_table + index * 4)
            if entry is None:
                break
            # The array relocates to entries, whose first word relocates to a
            # name. It is not a direct array of character-string pointers.
            declared_buffs.append({'index': index, 'name': string_pointer(entry)})
        else:
            raise CatalogError('Buff declaration table lacks bounded sentinel')
    properties = []
    table = pointer(root + 0x130)
    if table is not None:
        for index in range(256):
            entry = pointer(table + index * 4)
            if entry is None:
                break
            label = string_pointer(entry)
            raw = span(entry + 4, 4)
            value = struct.unpack('<f', raw)[0]
            properties.append({'index': index, 'name': label,
                               'selector_1_declared_bits': f'{int.from_bytes(raw, "little"):08x}',
                               'selector_1_declared_value': value if math.isfinite(value) else None})
        else:
            raise CatalogError('Property table lacks bounded sentinel')
    return {'active_capability_byte': active_byte,
            'active_capability_declared': active_byte != 0,
            'passive_key_name_declared': string_pointer(root + 0x11c),
            'external_ability_name_declared': external,
            'inline_ability_name_declared': string_pointer(root + 0x44) if active_byte and not external else None,
            'buffs_declared': declared_buffs,
            'properties': properties}


def inspect(binary, data_root, metadata=METADATA):
    executable = Path(binary).read_bytes()
    if hashlib.sha256(executable).hexdigest() != EXPECTED_SHA256:
        raise CatalogError('Executable SHA-256 does not match selected LAA build')
    catalog = read_metadata(metadata)
    rows = []
    for definition, row in sorted(catalog['definitions'].items(), key=lambda pair: int(pair[0])):
        name = row['resource_name']
        resource = (Path(data_root) / name[:2] / name).read_bytes()
        fields = decode_item(resource, executable, row)
        rows.append({'definition_index': int(definition), 'definition_name': row['definition_name'],
                     'resource_name': name, 'resource_sha256': row['resource_sha256'],
                     'presentation_hidden_declared': row['hud_hidden'],
                     'quantity_rules_declared': {key: row[key] for key in ('stackable', 'max_stack', 'grant_skip', 'unique')},
                     **fields})
    return {'schema': 'vg.passive-item-candidates.v1', 'selected_build_sha256': EXPECTED_SHA256,
            'metadata_build_sha256': catalog['build_sha256'], 'metadata_sha256': METADATA_SHA256,
            'metadata_hash_policy': 'UTF-8 bytes with CRLF normalized to LF',
            'manifest_sha256_declared': catalog['manifest_sha256'],
            'scope': 'Local declared candidates only; active capability, passive key and possession do not prove activation, recipients, effective values, timers or cleanup. Original catalog build and selected LAA build remain distinct.',
            'item_count': len(rows), 'items': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--data-root', required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.binary, args.data_root), indent=2, allow_nan=False))
