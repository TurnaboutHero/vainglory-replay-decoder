import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

def differences(before, after, path=''):
    if type(before) is not type(after):
        return [{'path': path, 'before': before, 'after': after}]
    if isinstance(before, dict):
        output = []
        for key in sorted(set(before) | set(after)):
            output.extend(differences(before.get(key), after.get(key), path + '.' + str(key)))
        return output
    if isinstance(before, list):
        if len(before) != len(after):
            return [{'path': path, 'before': before, 'after': after}]
        return [difference for index, pair in enumerate(zip(before, after))
                for difference in differences(*pair, path + '[' + str(index) + ']')]
    return [] if before == after else [{'path': path, 'before': before, 'after': after}]


def inspect_transition(opcode, actor_present, first, second, before, after):
    predicted = deepcopy(before)
    evidence = {'kind': None}
    if not actor_present:
        evidence['kind'] = 'missing_actor_noop'
    elif opcode == 0x0444:
        candidates = [row for row in predicted['live'] if row['item'] and row['item']['instance_id'] == first]
        if len(candidates) != 1:
            raise ValueError('Resolved SET target is absent or ambiguous')
        candidates[0]['item']['quantity'] = second & 0xffff
        evidence.update(kind='set_low16_retains_pointer', pointer=candidates[0]['item']['pointer'])
    elif opcode == 0x044b:
        candidates = [row for row in predicted['live'] if row['item'] and row['item']['instance_id'] == first]
        if not candidates:
            evidence['kind'] = 'missing_instance_consume_noop'
        elif len(candidates) != 1:
            raise ValueError('Consume instance is ambiguous')
        else:
            row = candidates[0]
            item = row['item']
            evidence['pointer'] = item['pointer']
            if item['definition']['stackable'] and item['quantity']:
                item['quantity'] -= 1
            if item['definition']['stackable'] and item['quantity']:
                evidence['kind'] = 'consume_decrement_retains_pointer'
            else:
                evidence['kind'] = 'consume_live_to_deferred'
                item['item_flags'] |= 1
                vacant = next((r for r in predicted['deferred'] if r['item'] is None), None)
                if vacant is None:
                    raise ValueError('Deferred capacity exhausted; retention behavior unproved')
                vacant['item'] = item
                evidence['deferred_index'] = vacant['array_index']
                row['item'] = None
                predicted['occupied'] -= 1
                predicted['flags'] |= 0x80
                predicted['dirty'] = True
    elif opcode == 0x043d:
        if second == 0xffffffff:
            hit = next((r for r in predicted['live'] if r['item'] and r['item']['definition_id'] == first
                        and r['item']['quantity'] < r['item']['definition']['max_stack']), None)
            if hit:
                hit['item']['quantity'] = (hit['item']['quantity'] + 1) & 0xffff
                evidence.update(kind='sentinel_first_nonfull_merge', pointer=hit['item']['pointer'], array_index=hit['array_index'])
            else:
                evidence['kind'] = 'sentinel_no_eligible_stack_noop'
        else:
            matching = [r['item'] for r in before['live'] if r['item'] and r['item']['definition_id'] == first]
            full = before['occupied'] == before['capacity']
            can_stack = any(item['quantity'] < item['definition']['max_stack'] for item in matching)
            unique = any(item['definition']['unique'] for item in matching)
            if unique or (full and not can_stack):
                evidence.update(kind='grant_rejected_unique_or_full', full=full, unique=unique, eligible_nonfull_stack=can_stack)
            else:
                vacant = next((r for r in predicted['live'] if r['item'] is None), None)
                actual = [r for r in after['live'] if r['item'] and r['item']['instance_id'] == second]
                if vacant is None or len(actual) != 1:
                    raise ValueError('Grant did not produce exactly one inspectable new instance')
                new = actual[0]
                item = new['item']
                previous_pointers = {r['item']['pointer'] for array in ('live', 'deferred') for r in before[array] if r['item']}
                if (new['array_index'] != vacant['array_index'] or item['definition_id'] != first
                        or item['quantity'] != 1 or item['pointer'] in previous_pointers
                        or int(item['pointer'], 16) == 0 or item['definition']['grant_skip_flag']):
                    raise ValueError('New grant instance fields, pointer, or first-vacancy placement mismatch')
                vacant['item'] = deepcopy(item)
                predicted['occupied'] += 1
                predicted['flags'] |= 0x80
                predicted['dirty'] = True
                evidence.update(kind='grant_new_first_vacant', pointer=item['pointer'], array_index=new['array_index'],
                                native_definition=item['definition'], newly_allocated_pointer_observed_not_predicted=True)
    else:
        raise ValueError('Unsupported inventory operation')
    evidence['native_transition_discrepancies'] = differences(predicted, after, 'inventory')
    return evidence


def digest(value):
    return hashlib.sha256(value).hexdigest()


def record_key(record):
    return [record['reader']['section'], record['reader']['buffered_record_time']['bits'], record['content_hex']]


def audit(data, workspace=None):
    assert data['synthetic'] and not data['source_native_emit_verified']
    counts = {}
    for run in data['runs']:
        counts[run['name']] = len(run['frames'])
        rows = None
        if workspace:
            capture = workspace / run['capture_path']
            assert digest(capture.read_bytes()) == run['capture_sha256']
            rows = [json.loads(line).get('payload', json.loads(line)) for line in capture.read_text().splitlines()]
            source = workspace / run['source_path']
            assert digest((source / 'synthetic-manifest.json').read_bytes()) == run['manifest_sha256']
            for name, expected in run['source_hashes'].items():
                assert Path(name).name == name and digest((source / name).read_bytes()) == expected
            raw = (source / run['modified_section']).read_bytes()
            start, length = run['insertion_offset'], run['inserted_bytes']
            assert digest(raw[:start] + raw[start + length:]) == run['original_hashes'][run['modified_section']]
        previous = None
        dispatches = set()
        for frame in run['frames']:
            assert frame['dispatch_id'] not in dispatches
            dispatches.add(frame['dispatch_id'])
            key = frame['source_record_key']
            content = bytes.fromhex(key[2])
            opcode = int.from_bytes(content[:2], 'big')
            actor, first = struct.unpack_from('>II', content, 2)
            second = int.from_bytes(content[10:12], 'big') != 0 if opcode == 0x044b else int.from_bytes(content[10:14], 'big')
            args = [actor, first, int(second)]
            fingerprint = (struct.pack('<III', first, second, actor) if opcode == 0x043d else
                           struct.pack('<IIB', actor, first, second) if opcode == 0x044b else
                           struct.pack('<III', actor, first, second)).hex()
            assert args == frame['constructor_args'] and fingerprint == frame['fingerprint']
            chain = [entry['payload'] for entry in frame['observations'][:11]]
            dispatch, ctor, mapped, ctor_after, enqueue, queue, submitted, deferred_pre, before, after, deferred_post = chain
            seqs = [p['event_sequence'] for p in chain]
            assert seqs == sorted(set(seqs)) and len({p['thread'] for p in chain}) == 1
            assert record_key(dispatch['record']) == key and dispatch['record']['dispatch_id'] == frame['dispatch_id']
            for event in chain[1:]:
                assert event.get('dispatch_id', event.get('context', {}).get('dispatch_id')) == frame['dispatch_id']
            stack, heap = frame['stack_action'], frame['heap_action']
            assert ctor['arg_bits'] == args and ctor['object'] == ctor_after['object'] == mapped['action_pointer'] == stack
            for event in (mapped, queue, submitted):
                assert event['fingerprint'] == fingerprint
            for event in (enqueue, queue, submitted):
                assert event['source_action'] == stack
            assert queue['heap_action'] == submitted['heap_action'] == heap
            for event in (before, after):
                assert event['object'] == heap and bytes.fromhex(event['action_hex'])[16:16 + len(bytes.fromhex(fingerprint))].hex() == fingerprint
            for event in (deferred_pre, deferred_post):
                context = event['context']
                assert record_key(context) == key and context['action_pointer'] == heap
                assert context['queue_copy_proof']['source_action'] == stack and context['queue_copy_proof']['heap_action'] == heap
                assert context['constructor_fingerprint'] == fingerprint
            old, new = frame['actual_before'], frame['actual_after']
            for inventory in (old, new):
                assert inventory['capacity'] == len(inventory['live']) == len(inventory['deferred'])
                assert inventory['occupied'] == sum(slot['item'] is not None for slot in inventory['live'])
                assert inventory['dirty'] == bool(inventory['flags'] & 128)
                assert inventory['capacity'] == inventory['flags'] & 127
            result = inspect_transition(opcode, frame['resolution']['present'], first, second, old, new)
            assert result == frame['transition'] and not result['native_transition_discrepancies']
            assert previous is None or previous == old
            previous = new
            left, right = frame['snapshots']
            assert {k:v for k,v in left.items() if k != 'line'} == {k:v for k,v in right.items() if k != 'line'}
            assert frame['resolution']['native_actor_id'] == actor
            assert frame['resolution']['present'] == (actor in frame['captured_player_ids'])
            resolution = frame['resolution']
            assert resolution['dispatch_id'] == frame['dispatch_id']
            assert resolution['active_hook']['object'] == heap
            handler = {0x043d: 'item_grant_apply', 0x0444: 'item_set_apply', 0x044b: 'item_consume_apply'}[opcode]
            assert resolution['active_hook']['name'] == before['hook'] == after['hook'] == handler
            if resolution['present']:
                assert resolution['native_actor_id'] == left['primary_fields']['native_actor_id']
                assert resolution['actor'] == left['primary_fields']['actor']
            else:
                assert int(resolution['actor'], 16) == 0
            for index, observation in enumerate(frame['observations'][11:]):
                assert observation['payload']['inventory_component'] == (old if index == 0 else new)
            if workspace:
                offset = frame['source_offset']
                assert int.from_bytes(raw[offset:offset + 4], 'big') == key[1]
                assert int.from_bytes(raw[offset + 4:offset + 8], 'big') == len(content)
                assert raw[offset + 8:offset + 8 + len(content)] == content
                for observation in frame['observations']:
                    native = rows[observation['line'] - 1]
                    assert observation['payload'] == {k:v for k,v in native.items() if k not in ('state','players')}
                for snapshot, inventory in zip(frame['snapshots'], (old, new)):
                    state = rows[snapshot['line'] - 1]['state']
                    primary = next(p for p in state['players'] if p['native_actor_id'] == 1509)
                    others = [p for p in state['players'] if p['native_actor_id'] != 1509]
                    assert primary['inventory_detail'] == inventory
                    assert snapshot['primary_fields'] == {k:v for k,v in primary.items() if k not in ('inventory','inventory_detail')}
                    assert snapshot['other_players_sha256'] == digest(json.dumps(others, sort_keys=True).encode())
                    assert snapshot['sampled_globals'] == {k:state.get(k) for k in snapshot['sampled_globals']}
                assert frame['resolution'] in rows
    assert counts == {'safe22': 22, 'set3': 3}
    return {'ok': True, 'controls': 25, 'runs': counts, 'external_files_rechecked': workspace is not None,
            'source_native_emit_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(Path(__file__).with_name('controls.json').read_text()), args.workspace)))
