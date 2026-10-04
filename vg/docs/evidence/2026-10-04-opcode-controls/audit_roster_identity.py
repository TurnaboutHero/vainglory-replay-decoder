import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
from datetime import datetime

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    return [r.get('payload', r) for r in
            (json.loads(line) for line in path.read_text().splitlines())]


def project(state):
    result = {k: state[k] for k in ('sequence', 'utc_ms', 'pid', 'game_clock',
                                  'replay_reader_before', 'replay_reader_after', 'roster_count')}
    fields = ('native_actor_id', 'display_name', 'definition_id', 'team_raw',
              'kills', 'deaths', 'assists')
    result['players'] = [{k: p[k] for k in fields} for p in state['players']]
    result['native_roster'] = state['native_roster'][:state['roster_count']]
    return result


def float_value(field):
    value = struct.unpack('<f', struct.pack('<I', field['bits']))[0]
    require(math.isfinite(value) and value == field['value'], 'float bits/value mismatch')
    return value


def attribute_value(field):
    raw = sum(float_value(layer) for layer in field['layers'])
    value = min(field['upper'], max(field['lower'], raw))
    require(value == field['value'], 'attribute layers/value mismatch')
    return value


def kda(player):
    return (attribute_value(player['kills']), attribute_value(player['deaths']),
            float_value(player['assists']))


def framed_records(raw):
    offset = 0
    while offset < len(raw):
        require(len(raw) - offset >= 8, 'truncated frame header')
        bits, length = struct.unpack_from('>II', raw, offset)
        value = struct.unpack_from('>f', raw, offset)[0]
        require(math.isfinite(value) and 2 <= length <= len(raw) - offset - 8,
                'invalid frame length/time')
        yield offset, bits, raw[offset + 8:offset + 8 + length].hex()
        offset += 8 + length


def audit(data, workspace=None):
    require(data['schema_version'] == 1 and data['recording'] == 'C08', 'unsupported identity evidence')
    lengths, actor_lengths, skins = {}, {}, {}
    for row in data['controls']:
        source, dispatch = row['source'], row['dispatch']
        record = dispatch['record']
        content = bytes.fromhex(record['content_hex'])
        payload = content[2:]
        require(record['opcode'] == 0x03ee and content[:2] == b'\x03\xee', 'wrong opcode')
        require(len(content) == record['content_length'] and len(payload) in (216, 222), 'wrong payload length')
        require(source['content_hex'] == record['content_hex'] == record['reader']['content_hex'], 'record bytes mismatch')
        require(source['content_length'] == record['reader']['content_length'] == len(content), 'reader length mismatch')
        require(source['section'] == record['reader']['section'] and
                source['time_bits'] == record['reader']['buffered_record_time']['bits'], 'source boundary mismatch')
        actor, definition, skin = (int.from_bytes(payload[o:o + 4], 'big') for o in (160, 164, 168))
        name = payload[:160].split(b'\0', 1)[0].decode('utf8')
        native, wrapper = row['native_roster_row'], row['wrapper']
        require((actor, definition, skin, name) ==
                (native['native_actor_id'], native['definition_id'], native['skin_value'], native['display_name']),
                'source/native roster mismatch')
        require(dispatch['tag'] == 'opcode_dispatch_before' and row['consumer_after']['tag'] == 'opcode_hook_after' and
                row['consumer_after']['hook'] == 'roster_consumer', 'wrong consumer event')
        require(record['dispatch_id'] == row['consumer_after']['dispatch_id'] == wrapper['dispatch_id'], 'dispatch mismatch')
        require(wrapper['tag'] == 'opcode_skin_wrap_return' and wrapper['input_bits'] == wrapper['returned_value'] == skin and
                wrapper['object'] == wrapper['returned_pointer'], 'skin wrapper mismatch')
        require(row['dispatch_line'] < row['wrapper_line'] < row['consumer_after_line'], 'consumer order mismatch')
        lengths[len(payload)] = lengths.get(len(payload), 0) + 1
        actor_lengths.setdefault(actor, set()).add(len(payload))
        previous = skins.setdefault(actor, (definition, skin, name))
        require(previous == (definition, skin, name), 'roster identity changed')
    require(lengths == {216: 40, 222: 10} and len(actor_lengths) == 10 and
            all(v == {216, 222} for v in actor_lengths.values()), 'incomplete 216/222 coverage')

    identities = [data['entry_identity'], data['eof_identity']]
    require(all(i['tag'] == 'identity' for i in identities) and
            all(identities[0][k] == identities[1][k] for k in ('pid', 'create_time', 'sha256')),
            'capture process mismatch')
    require(identities[0]['sha256'] == 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc', 'unsupported client')
    require(all(data[k]['tag'] == 'host_complete' and data[k]['failed'] is False
                for k in ('entry_completion', 'eof_completion')), 'incomplete capture')
    brackets = data['brackets']
    require(len(brackets) == 2, 'missing screenshot bracket')
    first, last = (b['state'] for b in brackets)
    require(all(s['pid'] == identities[0]['pid'] and s['roster_count'] == 10 and len(s['players']) == 10
                for s in (first, last)), 'wrong native player count/process')
    require(all(first[k] == last[k] for k in ('players', 'native_roster', 'game_clock')), 'native identity changed around screenshot')
    frame = data['eof_frame']
    require(data['source_section_count'] == frame['section'] + 1 and
            frame['offset'] + 8 + frame['content_length'] == frame['source_bytes'], 'not final source frame')
    require(len(bytes.fromhex(frame['content_hex'])) == frame['content_length'], 'EOF frame length mismatch')
    for state in (first, last):
        before, after = state['replay_reader_before'], state['replay_reader_after']
        require(before == after and before['kind'] == 'replay' and before['file_open'] is False and
                before['needs_record'] == 1 and before['section'] == frame['section'] + 1, 'reader has not exhausted source')
        require(before['content_hex'] == frame['content_hex'] and before['content_length'] == frame['content_length'] and
                before['buffered_record_time']['bits'] == frame['time_bits'], 'EOF reader/source mismatch')
        float_value(before['buffered_record_time'])
        float_value(state['game_clock'])
    shot = data['screenshot']
    png = HERE / shot['file']
    require(digest(png) == shot['sha256'], 'screenshot hash mismatch')
    raw_png = png.read_bytes()
    require(raw_png[:8] == b'\x89PNG\r\n\x1a\n', 'screenshot is not PNG')
    width, height = struct.unpack_from('>II', raw_png, 16)
    receipt = shot['receipt']['result']['shot']
    require((width, height) == (3094, 1870) and receipt['pid'] == first['pid'] and
            width == receipt['rect'][2] - receipt['rect'][0] and height == receipt['rect'][3] - receipt['rect'][1], 'screenshot dimensions/process mismatch')
    begin, end = (datetime.fromisoformat(receipt[k]).timestamp() * 1000 for k in ('begin_utc', 'end_utc'))
    require(first['utc_ms'] < begin < end < last['utc_ms'], 'screenshot outside native bracket')
    players = first['players']
    tuples = [kda(p) for p in players]
    require(len(set(tuples)) == len(players), 'KDA does not uniquely identify these rows')
    assets = {a['definition_id']: a for a in data['hero_assets']}
    joined = []
    for rendered in data['manual_rows']:
        matches = [p for p in players if kda(p) == tuple(rendered['kda'])]
        require(len(matches) == 1, 'ambiguous rendered row')
        player = matches[0]
        require(rendered['display_name'] == player['display_name'] == 'Guest', 'nickname mismatch')
        asset = assets[player['definition_id']]
        require(asset['native_name'] == asset['hero_label'] == rendered['portrait_hero'] and
                asset['serialized_name'] == '*' + asset['hero_label'] + '*', 'portrait/definition mismatch')
        native = next(p for p in first['native_roster'] if p['native_actor_id'] == player['native_actor_id'])
        require((native['definition_id'], native['skin_value'], native['display_name']) == skins[player['native_actor_id']], 'EOF roster differs from initial native controls')
        joined.append({'actor_id': player['native_actor_id'], 'nickname': player['display_name'],
                       'definition_id': player['definition_id'], 'hero': asset['hero_label'],
                       'raw_skin': native['skin_value'], 'kda': list(kda(player))})
    require({j['actor_id'] for j in joined} == {1501, 1502}, 'missing same-nickname actors')

    if workspace:
        def checked(metadata):
            path = workspace / metadata['path']
            require(digest(path) == metadata['sha256'] and path.stat().st_size == metadata['bytes'], 'external hash/size mismatch: ' + str(path))
            return path
        captures = {key: read_rows(checked(value)) for key, value in data['captures'].items()}
        require(captures['entry'][0] == data['entry_identity'] and captures['eof'][0] == data['eof_identity'] and
                captures['entry'][-1] == data['entry_completion'] and captures['eof'][-1] == data['eof_completion'], 'external identity/completion mismatch')
        sources = json.loads(checked(data['source_manifest']).read_text())
        entry = next(r for r in sources['recordings'] if r['recording_id'] == 'C08')
        require(len(entry['source_files']) == data['source_section_count'], 'source section count mismatch')
        source_root = (workspace / data['source_manifest']['path']).parent
        framed = {}
        for source in entry['source_files']:
            path = source_root / source['path']
            require(digest(path) == source['sha256'], 'corpus hash mismatch')
            framed[source['section']] = (path, list(framed_records(path.read_bytes())))
        for row in data['controls']:
            source, record = row['source'], row['dispatch']['record']
            path, frames = framed[source['section']]
            matches = [f for f in frames if f[1:] == (source['time_bits'], source['content_hex'])]
            require(matches == [(source['offset'], source['time_bits'], source['content_hex'])] and
                    path == workspace / source['source_path'] and digest(path) == source['source_sha256'], 'ambiguous or wrong original source')
            actual = captures['entry'][row['dispatch_line'] - 1]
            require(row['dispatch'] == {k: actual[k] for k in row['dispatch']}, 'external dispatch mismatch')
            after = captures['entry'][row['consumer_after_line'] - 1]
            require(row['consumer_after'] == {k: after[k] for k in row['consumer_after']} and
                    row['native_roster_row'] in after['state']['native_roster'][:after['state']['roster_count']], 'external consumer mismatch')
            require(row['wrapper'] == captures['entry'][row['wrapper_line'] - 1], 'external wrapper mismatch')
        path, frames = framed[frame['section']]
        require(frames[-1] == (frame['offset'], frame['time_bits'], frame['content_hex']) and
                path == workspace / frame['source_path'] and digest(path) == frame['source_sha256'] and
                path.stat().st_size == frame['source_bytes'] and frame['section'] + 1 not in framed, 'external EOF mismatch')
        snapshots = [(i, r['state']) for i, r in enumerate(captures['eof'], 1) if r.get('tag') == 'timed_snapshot']
        stability = data['eof_stability']
        require((len(snapshots), snapshots[0][0], snapshots[-1][0]) ==
                (stability['snapshot_count'], stability['first_line'], stability['last_line']), 'snapshot range mismatch')
        signatures = {json.dumps({k: s[k] for k in ('game_clock', 'players', 'native_roster')}, sort_keys=True)
                      for _, s in snapshots}
        require(len(signatures) == 1 and hashlib.sha256(next(iter(signatures)).encode()).hexdigest() == stability['full_state_signature_sha256'], 'EOF native state was not stable')
        boundary = lambda reader: {k: v for k, v in reader.items() if k != 'playback_time'}
        require(len({json.dumps(boundary(s[k]), sort_keys=True) for _, s in snapshots
                     for k in ('replay_reader_before', 'replay_reader_after')}) == 1, 'EOF reader boundary changed')
        require(sum(s['replay_reader_before'] != s['replay_reader_after'] for _, s in snapshots) ==
                stability['samples_with_playback_time_changing_during_read'], 'reader timing count mismatch')
        for bracket in brackets:
            require(bracket['state'] == project(captures['eof'][bracket['line'] - 1]['state']), 'external screenshot bracket mismatch')
        require(shot['receipt'] in read_rows(checked(shot['receipt_source'])), 'external screenshot receipt mismatch')
        sys.path.insert(0, str(HERE.parents[3]))
        from vg.core.cff_resource import load_cff
        from vg.core.definition_catalog import load_catalog, supported_build_profile
        exe_path, manifest_path, _, localization_path = [checked(s) for s in data['asset_sources']]
        exe = exe_path.read_bytes()
        profile = supported_build_profile(digest(exe_path), digest(manifest_path))
        catalog = load_catalog(manifest_path.read_bytes(), exe, profile)
        labels = dict(re.findall(r'^"([^"]+)"\s*=\s*"([^"]*)";',
                                base64.b64decode(localization_path.read_bytes(), validate=True).decode('utf8'), re.M))
        for asset in assets.values():
            require(catalog.lookup(asset['definition_id']).serialized_name == asset['serialized_name'], 'external definition mapping mismatch')
            path = checked(asset['resource'])
            decoded = load_cff(path.read_bytes(), exe, build_sha256=profile.build_sha256,
                               resource_sha256=digest(path), key_table_va=profile.key_table_va, version=profile.version)
            root = struct.unpack_from('<I', decoded.symbol)[0]
            require(decoded.symbol[8:].split(b'\0')[0].decode('ascii') == asset['serialized_name'], 'external hero symbol mismatch')
            def string(field):
                offset = decoded.relocations[root + field]
                return decoded.inst[offset:decoded.inst.index(b'\0', offset)].decode('utf8')
            require(string(16) == asset['native_name'] and string(20) == asset['localization_key'] and
                    labels[string(20)] == asset['hero_label'], 'external hero label mismatch')
    return {'ok': True, 'roster_controls': len(data['controls']), 'payload_lengths': lengths,
            'same_nickname_rows': joined, 'embedded_screenshot_brackets': len(brackets),
            'external_files_rechecked': workspace is not None,
            'literal_rendered_hero_name_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recheck same-nickname roster identity; literal hero text is outside this proof.')
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads((HERE / 'roster-identity.json').read_text()), args.workspace)))
