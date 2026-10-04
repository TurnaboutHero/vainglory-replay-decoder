import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct


def bits(value):
    return struct.unpack('>I', struct.pack('>f', value))[0]


def audit(data, folder, workspace=None):
    assert hashlib.sha256((folder / data['screenshot']['path']).read_bytes()).hexdigest() == data['screenshot']['sha256']
    assert data['synthetic'] is True and data['source_native_emit_verified'] is False
    command = data['command_receipt']
    assert command['result']['shot'] == data['shot']
    assert command['result']['state']['foreground_pid'] == data['shot']['pid'] == data['pid_identity']['pid']
    before, after = data['before'], data['after']
    strip = lambda row: {k: v for k, v in row.items() if k not in ('sequence', 'utc_ms')}
    assert strip(before['payload']) == strip(after['payload'])
    assert datetime.fromisoformat(before['host_utc']) < datetime.fromisoformat(data['shot']['begin_utc'])
    assert datetime.fromisoformat(after['host_utc']) > datetime.fromisoformat(data['shot']['end_utc'])
    reader = before['payload']['replay_reader_before']
    assert reader == before['payload']['replay_reader_after']
    assert reader['needs_record'] == 0 and reader['playback_time']['value'] < reader['buffered_record_time']['value']
    for row in data['ui_comparisons']:
        player = next(p for p in before['payload']['players'] if p['native_actor_id'] == row['actor'])
        assert player['display_name'] == row['screen_name']
        assert [player[k]['value'] for k in ('kills', 'deaths', 'assists', 'resource14')] == row['screen_kda_icon_count']
    for control in data['attribute_controls']:
        raw = bytes.fromhex(control['source_frame_hex'])
        assert int.from_bytes(raw[4:8], 'big') == 24 and raw[8:10] == b'\x04\x1c'
        payload = raw[10:]
        actor, reference, value = struct.unpack_from('>IIf', payload)
        index, layer, mode = payload[12:15]
        assert actor == 1509 and index in (41, 42) and layer == 0
        events = control['native_events']
        def one(tag, hook=None):
            selected = [e['payload'] for e in events if e['payload']['tag'] == tag and (hook is None or e['payload'].get('hook') == hook)]
            assert len(selected) == 1
            return selected[0]
        dispatch = one('opcode_dispatch_before')['record']
        assert dispatch['content_hex'] == raw[8:].hex() == dispatch['reader']['content_hex']
        assert dispatch['reader']['section'] == 1 and dispatch['reader']['buffered_record_time']['bits'] == int.from_bytes(raw[:4], 'big')
        constructor = one('opcode_hook_before', 'counter_ctor')
        assert constructor['arg_bits'] == [actor, index, layer, bits(value), int(mode != 0), reference]
        fingerprint = struct.pack('<IIIIfB', actor, reference, index, layer, value, int(mode != 0)).hex()
        queue = one('opcode_queue_copy')
        assert queue['fingerprint'] == fingerprint
        mapped = one('opcode_action_mapped')
        submit = one('opcode_queue_submit_return')
        assert mapped['action_pointer'] == constructor['object'] == queue['source_action'] == submit['source_action']
        assert mapped['fingerprint'] == submit['fingerprint'] == fingerprint
        assert submit['heap_action'] == queue['heap_action']
        for tag in ('opcode_hook_before', 'opcode_hook_after'):
            apply = one(tag, 'counter_apply')
            assert apply['object'] == queue['heap_action']
            assert apply['action_hex'][32:32 + len(fingerprint)] == fingerprint
        native_before, native_after = control['actual_before'], control['actual_after']
        assert native_before['actor_pointer'] == native_after['actor_pointer']
        assert native_before['component_pointer'] == native_after['component_pointer']
        assert any(e['payload']['tag'] == 'opcode_actor_resolve' and e['payload'].get('present') is True and e['payload'].get('native_actor_id') == actor and e['payload'].get('actor') == native_before['actor_pointer'] for e in events)
        field = 'kills' if index == 41 else 'deaths'
        store_before, store_after = one('opcode_counter_set_before'), one('opcode_counter_set_after')
        assert store_before['index'] == index and store_before['layer'] == 0
        assert int(store_before['address'], 16) == int(native_before['component_pointer'], 16) + 0x20 + index * 4
        assert store_after['address'] == store_before['address']
        assert store_before['cell']['bits'] == native_before['layers'][field]['layers'][0]['bits']
        assert store_after['cell']['bits'] == native_after['layers'][field]['layers'][0]['bits']
        expected = value if mode else native_before['values'][field] + value
        assert bits(expected) == native_after['layers'][field]['layers'][0]['bits'] == native_after['bits'][field]
        assert all(native_before['bits'][k] == native_after['bits'][k] for k in native_before['bits'] if k != field)
    assert len(data['attribute_controls']) == 8
    if workspace:
        for ref in data['files'] + data['source_files']:
            assert hashlib.sha256((workspace / ref['path']).read_bytes()).hexdigest() == ref['sha256']
        frames = []
        for ref in sorted(data['source_files'], key=lambda r: r['section']):
            raw = (workspace / ref['path']).read_bytes()
            offset = 0
            while offset < len(raw):
                time, length = struct.unpack_from('>II', raw, offset)
                assert length >= 2 and offset + 8 + length <= len(raw)
                frames.append((ref['section'], offset, time, raw[offset + 8:offset + 8 + length]))
                offset += 8 + length
        pending = [i for i, (section, offset, time, content) in enumerate(frames) if section == reader['section'] and time == reader['buffered_record_time']['bits'] and content.hex() == reader['content_hex']]
        assert len(pending) == 1
        boundary = frames[pending[0] - 1]
        assert list(boundary[:2]) == [data['applied_predecessor']['section'], data['applied_predecessor']['offset']]
        for section, offset, time, content in frames[:pending[0]]:
            if section < 1:
                continue
            payload = content[2:]
            if content[:2] == b'\x04\x1c' and int.from_bytes(payload[:4], 'big') == 1509 and payload[12] in (41, 42):
                assert section == 1 and offset <= data['last_synthetic_kd_sets'][str(payload[12])]
    return {'ok': True, 'attribute_controls': 8, 'rendered_kda_and_icon_numbers': 40, 'external_source_files_rechecked': workspace is not None, 'natural_kill_semantics_claimed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    print(json.dumps(audit(json.loads((folder / 'counter-ui.json').read_text()), folder, args.workspace)))
