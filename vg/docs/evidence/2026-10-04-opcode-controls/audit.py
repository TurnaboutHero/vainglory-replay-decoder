"""Recompute selected native controls; optionally recheck original external files."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(data, workspace=None):
    captures = {}
    if workspace:
        for capture in data['captures']:
            path = workspace / capture['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == capture['sha256']
            captures[path.name] = [json.loads(line).get('payload', json.loads(line)) for line in path.read_text().splitlines()]
    for kind in ('spawn', 'baseline', 'clock'):
        for row in data[kind]:
            source = row['source']
            record = row['native_dispatch_record']
            assert row['dispatch_id'] == record['dispatch_id']
            assert source['content_hex'] == record['content_hex'] == record['reader']['content_hex']
            assert source['time_bits'] == record['reader']['buffered_record_time']['bits']
            assert source['section'] == record['reader']['section']
            assert source['content_length'] == len(bytes.fromhex(source['content_hex']))
            if workspace:
                capture_rows = captures[row['capture']]
                for field, value in row.items():
                    lines = value if field == 'resolver_lines' else [value] if field.endswith('_line') else []
                    for line in lines:
                        assert type(line) is int and 1 <= line <= len(capture_rows)
                        event = capture_rows[line - 1]
                        dispatch_id = event.get('dispatch_id', event.get('context', event.get('record', {})).get('dispatch_id'))
                        assert dispatch_id == row['dispatch_id'], (kind, field, line, dispatch_id)
                assert record == capture_rows[row['dispatch_line'] - 1]['record']
                raw = (workspace / source['source_path']).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == source['source_sha256']
                offset = source['offset']
                assert int.from_bytes(raw[offset:offset + 4], 'big') == source['time_bits']
                assert int.from_bytes(raw[offset + 4:offset + 8], 'big') == source['content_length']
                assert raw[offset + 8:offset + 8 + source['content_length']].hex() == source['content_hex']
            if kind == 'clock':
                payload = bytes.fromhex(source['content_hex'])[2:]
                assert len(payload) == 69
                assert int.from_bytes(payload[64:68], 'big') == row['argument_clock_bits'] == row['manager_after']['bits']
                if workspace:
                    assert row['argument_clock_bits'] == capture_rows[row['before_line'] - 1]['arg_bits'][1]
                    assert row['manager_after'] == capture_rows[row['after_line'] - 1]['manager_clock']
                continue
            action = bytes.fromhex(row['action_hex'])
            u = lambda offset: int.from_bytes(action[offset:offset + 4], 'little')
            assert row['heap_action'] == row['queue_copy_observation']['heap_action'] == row['apply_after_observation']['object']
            assert row['apply_after_observation']['tag'] == 'opcode_hook_after'
            assert row['apply_after_observation']['hook'] == kind + '_apply'
            assert row['apply_after_observation']['dispatch_id'] == row['queue_copy_observation']['dispatch_id'] == row['dispatch_id']
            assert all(event['dispatch_id'] == row['dispatch_id'] for event in row['resolver_observations'])
            assert row['queue_copy_observation']['fingerprint'] == row['action_hex'][0x10 * 2:]
            assert u(0x18) == row['actor_id'] == row['resolver_observations'][0]['native_actor_id']
            assert row['first_resolver_present'] == row['resolver_observations'][0]['present']
            if workspace:
                applied = capture_rows[row['applied_line'] - 1]
                assert row['apply_after_observation'] == {key: value for key, value in applied.items() if key not in ('state', 'players', 'action_hex')}
                assert row['action_hex'] == capture_rows[row['action_line'] - 1]['action_hex']
                assert row['queue_copy_observation'] == capture_rows[row['queue_copy_line'] - 1]
                assert row['resolver_observations'] == [capture_rows[line - 1] for line in row['resolver_lines']]
                for field, line in (('native_player_before', row['pre_line']), ('native_player_after', row['post_line'])):
                    players = capture_rows[line - 1]['state']['players']
                    assert row[field] == next((p for p in players if p['native_actor_id'] == row['actor_id']), None)
            if kind == 'spawn':
                continue
            before, after = row['native_player_before'], row['native_player_after']
            if row['first_resolver_present']:
                assert before is not None and before == after
                continue
            assert after is not None
            roster = row['native_roster']
            assert u(0x10) == after['definition_id'] and u(0x14) == roster['skin_value']
            assert all(roster[k] == after[k] for k in ('native_actor_id', 'display_name', 'definition_id'))
            assert action[0x358] == 0
            for field, index in (('kills', 41), ('deaths', 42)):
                assert u(0x350 + index // 32 * 4) & (1 << (index % 32))
                for layer in range(3):
                    assert u(0x40 + layer * 0xb4 + index * 4) == after[field]['layers'][layer]['bits']
            for field, offset in (('assists', 0x31c), ('resource14', 0x328), ('gold_balance', 0x308), ('net_worth', 0x30c)):
                assert u(offset + 0x20) == after[field]['bits']
            expected = [(i, u(0x368 + i * 4), u(0x390 + i * 4), u(0x3b8 + i * 4) & 65535) for i in range(u(0x45c))]
            actual = [(item['array_index'], item['definition_id'], item['instance_id'], item['quantity']) for item in after['inventory']['items'] if item]
            assert expected == actual
    return {'ok': True, 'spawn': len(data['spawn']), 'baseline': len(data['baseline']), 'clock': len(data['clock']), 'external_files_rechecked': workspace is not None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(Path(__file__).with_name('controls.json').read_text()), args.workspace)))
