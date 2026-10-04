import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import struct

REQUIREMENT = 'Capture14-byte record→12-byte native buffer plus resource ADD/SET before/after float32 bits, including6/7/11/14; establish CS visible label and lane-versus-jungle controls.'
FIELDS = ('kills', 'deaths', 'gold_balance', 'net_worth', 'assists', 'resource14')
RESOURCE_FIELDS = {6: 'gold_balance', 7: 'net_worth', 11: 'assists', 14: 'resource14'}
PLAYER_FIELDS = ('native_actor_id', 'display_name', 'definition_id', 'actor', 'component') + FIELDS


def bits(value):
    return struct.unpack('>I', struct.pack('>f', value))[0]


def f32(value):
    return struct.unpack('>f', struct.pack('>f', value))[0]


def project_event(outer, actor):
    payload = outer.get('payload', outer)
    result = {'event': {key: value for key, value in payload.items() if key != 'state'}}
    if 'state' in payload:
        state = payload['state']
        player = next(p for p in state['players'] if p['native_actor_id'] == actor)
        result['sample'] = {key: state[key] for key in ('game_clock', 'atomic_record_boundary', 'replay_reader_before', 'replay_reader_after', 'replay_reader_unchanged')}
        result['sample']['player'] = {key: player[key] for key in PLAYER_FIELDS}
    return result


def project_sample(outer, actor):
    payload = outer['payload']
    player = next(p for p in payload['players'] if p['native_actor_id'] == actor)
    return {'host_utc': outer['host_utc'], 'sample': {key: payload[key] for key in ('sequence', 'utc_ms', 'pid', 'game_clock', 'record_clock_unverified', 'record_index_before', 'record_index_after', 'replay_reader_before', 'replay_reader_after', 'atomic_record_boundary')}, 'player': {key: player[key] for key in PLAYER_FIELDS}}


def dispatch_id(event):
    return event.get('dispatch_id', event.get('context', event.get('record', {})).get('dispatch_id'))


def values(player):
    for field in FIELDS:
        cell = player[field]
        if 'bits' in cell:
            assert bits(cell['value']) == cell['bits']
        else:
            for layer in cell['layers']:
                assert bits(layer['value']) == layer['bits']
    return {field: player[field]['value'] for field in FIELDS}


def audit(data, folder, workspace=None):
    assert data['original_requirement'] == REQUIREMENT
    assert data['raw_receiver_buffer_captured'] is True
    assert len(data['raw_receiver_buffer_controls']) == 50
    assert data['whole_event_semantics_verified'] is False
    raw_files, lines_cache = {}, {}

    def raw(ref):
        key = (ref['path'], ref['sha256'])
        if key not in raw_files:
            content = (workspace / ref['path']).read_bytes()
            assert hashlib.sha256(content).hexdigest() == ref['sha256'], ref['path']
            raw_files[key] = content
        return raw_files[key]

    def line(ref, number):
        key = (ref['path'], ref['sha256'])
        if key not in lines_cache:
            lines_cache[key] = [json.loads(value) for value in raw(ref).splitlines()]
        rows = lines_cache[key]
        assert type(number) is int and 1 <= number <= len(rows)
        return rows[number - 1]

    def source(record):
        content = bytes.fromhex(record['content_hex'])
        assert content[:2] == b'\x04\x1d' and len(content) == record['content_length'] == 16
        assert record['offset'] >= 0 and type(record['offset']) is int
        assert int(Path(record['file']['path']).stem.rsplit('.', 1)[1]) == record['section']
        if workspace:
            file = raw(record['file'])
            offset = record['offset']
            assert file[offset:offset + 8] == struct.pack('>II', record['time_bits'], len(content))
            assert file[offset + 8:offset + 8 + len(content)] == content
        return content[2:]

    for image in data['images']:
        file = (folder / image['path']).read_bytes()
        assert hashlib.sha256(file).hexdigest() == image['sha256']
        assert file[:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II', file[16:24]) == tuple(image['dimensions'])
        if workspace:
            assert raw(image['original']) == file
    for ref in (data['static_receiver_copy'], data['related_scoreboard_evidence']):
        assert hashlib.sha256((folder / ref['path']).read_bytes()).hexdigest() == ref['sha256']
    assert data['static_receiver_copy']['runtime_stack_capture'] is True
    raw_indices = Counter()
    raw_ids = set()
    for control in data['raw_receiver_buffer_controls']:
        candidates = control['source_candidates']
        assert len(candidates) > 1 and control['source_offset_unique'] is False
        candidate = candidates[0]
        payload = source(candidate)
        assert len({row['offset'] for row in candidates}) == len(candidates)
        for row in candidates:
            assert source(row) == payload
            assert all(row[key] == candidate[key] for key in ('file', 'section', 'time_bits', 'content_hex'))
        if workspace:
            blob = raw(candidate['file'])
            needle = struct.pack('>II', candidate['time_bits'], 16) + bytes.fromhex(candidate['content_hex'])
            offsets, start = [], 0
            while (found := blob.find(needle, start)) >= 0:
                offsets.append(found)
                start = found + 1
            assert sorted(row['offset'] for row in candidates) == offsets
        raw_indices[payload[8]] += 1
        assert control['dispatch_id'] not in raw_ids
        raw_ids.add(control['dispatch_id'])
        assert len(control['events']) == 3
        events = {row['event']['tag']: row['event'] for row in control['events']}
        dispatch, copied, ctor = (events[tag] for tag in ('opcode_dispatch_before', 'opcode_resource_buffer_copy', 'opcode_hook_before'))
        for row in control['events']:
            assert dispatch_id(row['event']) == control['dispatch_id']
            if workspace:
                assert {key: value for key, value in row.items() if key != 'line'} == project_event(line(data['raw_buffer_capture'], row['line']), control['actor_id'])
        assert dispatch['event_sequence'] < copied['event_sequence'] < ctor['event_sequence']
        assert dispatch['thread'] == copied['thread'] == ctor['thread']
        assert copied['hook_va'] == '004d2d18' and copied['phase'] == 'after_memmove_before_endian_conversion'
        assert copied['length'] == 12 and copied['content_length'] == 16
        assert copied['buffer_hex'] == copied['source_prefix_hex'] == payload[:12].hex()
        assert int(copied['destination'], 16) == int(copied['caller_ebp'], 16) - 0xe40
        record = dispatch['record']
        assert int(copied['source'], 16) == int(record['packet_pointer'], 16) + 2
        assert copied['content_hex'] == record['content_hex'] == candidate['content_hex']
        assert copied['reader'] == record['reader']
        ctor_sample = next(row['sample'] for row in control['events'] if row['event']['tag'] == 'opcode_hook_before')
        assert ctor_sample['replay_reader_unchanged'] is True
        assert ctor_sample['replay_reader_before'] == ctor_sample['replay_reader_after'] == copied['reader']
        assert copied['reader']['section'] == candidate['section']
        assert copied['reader']['buffered_record_time']['bits'] == candidate['time_bits']
        assert copied['reader']['kind'] == 'replay' and copied['reader']['file_open'] is True
        assert copied['reader']['content_hex'] == candidate['content_hex']
        assert bits(copied['reader']['buffered_record_time']['value']) == candidate['time_bits']
        actor, operand = struct.unpack('>If', payload[:8])
        assert actor == control['actor_id']
        assert ctor['hook'] == 'resource_ctor' and ctor['arg_bits'] == [actor, payload[8], bits(operand), int(payload[9] != 0)]
    assert raw_indices == Counter({2: 35, 3: 15})
    if workspace:
        probe = data['raw_buffer_probe']
        sampler, guards, observer = (raw(ref).decode() for ref in probe['files'])
        guard_doc = json.loads(guards)
        combined = sampler + '\nconst OPCODE_GUARDS = ' + json.dumps(guard_doc['guards']) + ';\n' + observer
        assert hashlib.sha256(combined.encode()).hexdigest() == probe['script_sha256']
        assert probe['guard'] in guard_doc['guards']
        captured = [json.loads(value) for value in raw(data['raw_buffer_capture']).splitlines()]
        assert next(row['sha256'] for row in captured if row.get('tag') == 'probe_source') == probe['script_sha256']
        for tag in ('host_complete', 'observation_end'):
            matching = [row for row in captured if row.get('tag') == tag]
            assert len(matching) == 1 and matching[0]['failed'] is False
        assert not any(row.get('payload', row).get('tag') in ('opcode_error', 'runner_error', 'script_error', 'unexpected_detach') for row in captured)
    if workspace:
        for ref in data['source_files']:
            raw(ref)
        manifest = json.loads(raw(data['synthetic_manifest']))
        section = raw(data['synthetic_section'])
        offset, count = manifest['insertion_offset'], manifest['inserted_bytes']
        assert hashlib.sha256(section[:offset] + section[offset + count:]).hexdigest() == manifest['source_sha256'][manifest['modified_section']]
        captured = [json.loads(value) for value in raw(data['synthetic_capture']).splitlines()]
        payloads = [row.get('payload', row) for row in captured]
        assert not any(row.get('tag') in ('opcode_error', 'runner_error', 'script_error', 'unexpected_detach') for row in payloads)
        for tag in ('host_complete', 'observation_end'):
            matching = [row for row in payloads if row.get('tag') == tag]
            assert len(matching) == 1 and matching[0]['failed'] is False
        stopped = [row for row in payloads if row.get('tag') == 'rpc_stopped']
        assert len(stopped) == 1 and stopped[0]['result']['pending_actions'] == 0
    coverage = Counter()
    ids = set()
    for control in data['synthetic_controls']:
        actor = control['actor_id']
        assert actor == 1509 and control['synthetic'] is True
        payload = source(control['source'])
        owner, operand = struct.unpack('>If', payload[:8])
        index, mode = payload[8:10]
        assert owner == actor and index in RESOURCE_FIELDS
        assert control['native_prefix_hex'] == payload[:12].hex()
        assert control['native_prefix_origin'] == 'derived_from_dispatch_payload_not_captured_stack'
        coverage[(index, bool(mode), operand)] += 1
        assert control['dispatch_id'] not in ids
        ids.add(control['dispatch_id'])
        events = control['events']
        for row in events:
            assert dispatch_id(row['event']) == control['dispatch_id']
            if workspace:
                assert {key: value for key, value in row.items() if key != 'line'} == project_event(line(data['synthetic_capture'], row['line']), actor)

        def one(tag, hook=None):
            matching = [row for row in events if row['event']['tag'] == tag and (hook is None or row['event'].get('hook') == hook)]
            assert len(matching) == 1, (tag, hook)
            return matching[0]

        dispatch = one('opcode_dispatch_before')['event']['record']
        assert dispatch['content_hex'] == dispatch['reader']['content_hex'] == control['source']['content_hex']
        assert dispatch['content_length'] == dispatch['reader']['content_length'] == 16
        assert dispatch['reader']['section'] == control['source']['section']
        assert dispatch['reader']['buffered_record_time']['bits'] == control['source']['time_bits']
        assert bits(dispatch['reader']['buffered_record_time']['value']) == control['source']['time_bits']
        assert dispatch['reader']['kind'] == 'replay' and dispatch['reader']['file_open'] is True
        ctor = one('opcode_hook_before', 'resource_ctor')
        mapped, queue, submit = (one(tag) for tag in ('opcode_action_mapped', 'opcode_queue_copy', 'opcode_queue_submit_return'))
        fingerprint = struct.pack('<IIfB', actor, index, operand, int(mode != 0)).hex()
        assert ctor['event']['arg_bits'] == [actor, index, bits(operand), int(mode != 0)]
        assert mapped['event']['action_pointer'] == ctor['event']['object'] == queue['event']['source_action'] == submit['event']['source_action']
        assert queue['event']['heap_action'] == submit['event']['heap_action']
        assert all(row['event']['fingerprint'] == fingerprint for row in (mapped, queue, submit))
        before, after = (one(tag, 'resource_apply') for tag in ('opcode_hook_before', 'opcode_hook_after'))
        deferred_before, deferred_after = (one(tag) for tag in ('opcode_deferred_before', 'opcode_deferred_after'))
        order = [one('opcode_dispatch_before'), ctor, mapped, one('opcode_hook_after', 'resource_ctor'), one('opcode_enqueue_enter'), queue, submit, deferred_before, before, after, deferred_after]
        seq = [row['event']['event_sequence'] for row in order]
        assert seq == sorted(set(seq)) and len({row['event']['thread'] for row in order}) == 1
        for row in (before, after):
            assert row['event']['object'] == queue['event']['heap_action']
            assert row['event']['action_hex'][32:32 + len(fingerprint)] == fingerprint
            assert row['sample']['replay_reader_unchanged'] is True
        for row in (deferred_before, deferred_after):
            context = row['event']['context']
            assert context['dispatch_id'] == control['dispatch_id']
            assert context['action_pointer'] == queue['event']['heap_action']
            assert context['constructor_fingerprint'] == fingerprint
            assert context['content_hex'] == control['source']['content_hex'] == context['reader']['content_hex']
            assert context['reader']['section'] == control['source']['section']
            assert context['reader']['buffered_record_time']['bits'] == control['source']['time_bits']
            assert context['queue_copy_proof']['source_action'] == queue['event']['source_action']
            assert context['queue_copy_proof']['heap_action'] == queue['event']['heap_action']
        b, a = before['sample']['player'], after['sample']['player']
        assert b['actor'] == a['actor'] and b['component'] == a['component']
        assert any(row['event']['tag'] == 'opcode_actor_resolve' and row['event']['present'] is True and row['event']['native_actor_id'] == actor and row['event']['actor'] == b['actor'] and row['event']['active_hook']['name'] == 'resource_apply' and row['event']['active_hook']['object'] == queue['event']['heap_action'] for row in events)
        observed_before, observed_after = values(b), values(a)
        assert values(deferred_before['sample']['player']) == observed_before
        assert values(deferred_after['sample']['player']) == observed_after
        expected = dict(observed_before)
        field = RESOURCE_FIELDS[index]
        expected[field] = max(0.0, f32(operand if mode else observed_before[field] + operand))
        if index == 6 and not mode and operand > 0:
            expected['net_worth'] = f32(observed_before['net_worth'] + operand)
        assert all(bits(expected[key]) == bits(observed_after[key]) for key in FIELDS)
    assert len(data['synthetic_controls']) == 48
    for index in RESOURCE_FIELDS:
        assert coverage[(index, True, 10.0)] == 6
        for mode in (False, True):
            for operand in (3.0, 0.0, -20.0):
                assert coverage[(index, mode, operand)] == 1
    for natural in data['natural_controls']:
        assert natural['kind'] in ('lane', 'jungle')
        assert len(natural['transitions']) == {'lane': 10, 'jungle': 3}[natural['kind']]
        if workspace:
            captured = [json.loads(value) for value in raw(natural['capture']).splitlines()]
            matching = [row for row in captured if row.get('tag') == 'observation_end']
            assert len(matching) == 1 and matching[0]['failed'] is False
            sampled = [dict(line=number, **project_sample(row, 1500)) for number, row in enumerate(captured, 1) if row.get('payload', {}).get('tag') == 'player_state_sample']
            assert len(sampled) == natural['sample_count'] == {'lane': 691, 'jungle': 269}[natural['kind']]
            assert [row['sample']['sequence'] for row in sampled] == list(range(1, len(sampled) + 1))
            assert all([row['player'][key]['value'] for key in ('kills', 'deaths', 'assists')] == natural['kda'] for row in sampled)
            changing_lines = [(before['line'], after['line']) for before, after in zip(sampled, sampled[1:]) if before['player']['resource14']['bits'] != after['player']['resource14']['bits']]
            assert changing_lines == [(row['before']['line'], row['after']['line']) for row in natural['transitions']]
        for transition in natural['transitions']:
            before, after = transition['before'], transition['after']
            assert after['sample']['sequence'] == before['sample']['sequence'] + 1
            assert values(after['player'])['resource14'] - values(before['player'])['resource14'] == 1
            assert [before['player'][key]['value'] for key in ('kills', 'deaths', 'assists')] == natural['kda'] == [after['player'][key]['value'] for key in ('kills', 'deaths', 'assists')]
            assert before['sample']['record_clock_unverified']['value'] < f32(struct.unpack('>f', transition['source']['time_bits'].to_bytes(4, 'big'))[0]) <= after['sample']['record_clock_unverified']['value']
            assert source(transition['source']).hex() == '000005dc3f8000000e0001000000'
            for sample in (before, after):
                assert sample['sample']['replay_reader_before']['kind'] == 'not_replay' and sample['sample']['atomic_record_boundary'] is False
                assert sample['player']['native_actor_id'] == 1500 and sample['player']['definition_id'] == 285
                if workspace:
                    assert {key: value for key, value in sample.items() if key != 'line'} == project_sample(line(natural['capture'], sample['line']), 1500)
        for phase, count in (('before', 0), ('after', 1)):
            image = natural['visual'][phase]
            samples = image['bracket']
            assert datetime.fromisoformat(samples[0]['host_utc']) < datetime.fromisoformat(image['shot']['begin_utc'])
            assert datetime.fromisoformat(samples[-1]['host_utc']) > datetime.fromisoformat(image['shot']['end_utc'])
            assert [sample['sample']['sequence'] for sample in samples] == list(range(samples[0]['sample']['sequence'], samples[-1]['sample']['sequence'] + 1))
            assert all(values(sample['player'])['resource14'] == image['manually_viewed_icon_count'] == count for sample in samples)
            assert image['image'] in {entry['path'] for entry in data['images']}
            original = next(entry['original'] for entry in data['images'] if entry['path'] == image['image'])
            assert Path(original['path']).name == image['shot']['path'].rsplit('\\', 1)[-1]
            if workspace:
                assert line(natural['image_manifest'], image['manifest_line']) == image['shot']
                for sample in samples:
                    assert {key: value for key, value in sample.items() if key != 'line'} == project_sample(line(natural['capture'], sample['line']), 1500)
    assert {control['kind'] for control in data['natural_controls']} == {'lane', 'jungle'}
    return {'ok': True, 'synthetic_resource_controls': 48, 'indices': [6, 7, 11, 14], 'natural_unit_increments': 13, 'isolated_visual_controls': 2, 'primary_pngs': 4, 'raw_receiver_buffer_controls': 50, 'raw_buffer_indices': [2, 3], 'raw_receiver_buffer_captured': True, 'strict_requirement_complete': True, 'whole_event_semantics_verified': False, 'external_files_rechecked': workspace is not None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    print(json.dumps(audit(json.loads((folder / 'controls.json').read_text()), folder, args.workspace)))
