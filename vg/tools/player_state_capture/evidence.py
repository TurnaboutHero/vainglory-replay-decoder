from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from pathlib import Path, PureWindowsPath
import struct

from vg.core.replay_output import ReportInputs, validate_report_outputs
from .guards import CLIENT_HASHES, CaptureError, identifier, require, require_backup


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def utc_timestamp(value):
    if not isinstance(value, str):
        return value
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(?:Z|\+00:00)', value)
    return (match[1], (match[2] or '').rstrip('0')) if match else value


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metadata(path, **extra):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=digest(path), size=path.stat().st_size, **extra)


def publish(path, value, sources=()):
    path = Path(path)
    inputs = ReportInputs(files=tuple(Path(p) for p in sources))
    validate_report_outputs(inputs, (path,))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    inputs.recheck()
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def ref_path(base, ref):
    return (Path(base) / ref['path']).resolve()


def inspect_native(path, selected_sequence=None):
    rows = jsonl(path)
    identities = [r for r in rows if r.get('tag') == 'identity']
    require(len(identities) == 1, 'native_identity_missing', 'One native process identity is required')
    identity = identities[0]
    require(identity.get('sha256') in CLIENT_HASHES and type(identity.get('pid')) is int
            and identity['pid'] > 0 and type(identity.get('create_time')) in (int, float),
            'native_identity_invalid', 'Native executable/process identity is invalid')
    failures = [r for r in rows if r.get('tag') in {'runner_error', 'script_error', 'detach_error', 'unexpected_detach'}
                or r.get('payload', {}).get('tag') in {'inventory_error', 'inventory_limit', 'trace_error'}
                or (r.get('tag') == 'observation_end' and r.get('failed') is not False)]
    require(not failures, 'native_observer_failed', 'Native observer reported an error')
    require(any(r.get('tag') == 'detached' for r in rows)
            and any(r.get('tag') == 'observation_end' and r.get('failed') is False for r in rows),
            'native_detach_missing', 'Successful observation and detach receipts are required')
    samples = [r['payload'] for r in rows if r.get('payload', {}).get('tag') == 'player_state_sample']
    selected = None
    if samples:
        require(any(r.get('tag') == 'rpc_ready' and r.get('result', {}).get('guards') in (3, 5)
                    and r['result'].get('passive') is True for r in rows),
                'native_guard_missing', 'Native build guards were not confirmed')
        valid = [r for r in samples if r.get('game_clock') is not None and r.get('players')
                 and r.get('roster_count') == len(r['players'])]
        require(bool(valid), 'no_observation', 'No sample has a live session and complete nonempty player roster')
        if selected_sequence is not None:
            matches = [r for r in valid if r.get('sequence') == selected_sequence]
            require(len(matches) == 1, 'sample_missing', 'Selected native sample is absent or incomplete')
            selected = matches[0]
        else:
            selected = valid[-1]
        ids = [r.get('native_actor_id') for r in selected['players']]
        require(all(type(i) is int and 0 < i <= 0xffffffff for i in ids) and len(set(ids)) == len(ids),
                'actor_identity_invalid', 'Native player IDs must be unique positive uint32 values')
        require(selected.get('pid') == identity['pid'], 'foreign_process', 'Native sample belongs to a different process')
        native_float(selected['game_clock'])
    events = [r['payload'] for r in rows if r.get('payload', {}).get('tag', '').startswith('inventory_')
              and r['payload'].get('tag') != 'inventory_ready']
    require(selected is not None or bool(events), 'no_observation', 'No player state or inventory event was observed')
    return {'identity': identity, 'sample_count': len(samples), 'inventory_event_count': len(events),
            'sample': selected, 'kind': 'player_state' if selected else 'inventory_trace', 'rows': rows}


def verify_alignment(capture, native, artifacts, base):
    alignment = capture.get('alignment', {'kind': 'unverified'})
    if alignment.get('kind') == 'unverified':
        return None
    require(native['sample'] is not None, 'boundary_unproved', 'Inventory event traces are not whole-state boundaries')
    require(alignment.get('kind') in {'exact_record_boundary', 'recorded_end_paused', 'recorded_end_native', 'stable_future_pending_buffer'},
            'boundary_unproved', 'Unsupported native boundary proof')
    proof_ref = artifacts.get(alignment.get('artifact_id'))
    require(proof_ref is not None and proof_ref.get('role') == 'native_boundary',
            'boundary_unproved', 'Hashed native boundary artifact is required')
    proof = read_json(ref_path(base, proof_ref))
    sample = native['sample']
    if proof.get('method') == 'native_reader_buffer':
        from .alignment import reader_boundary
        require(proof == reader_boundary(capture, native, artifacts, base),
                'boundary_unproved', 'Native reader boundary proof changed')
        require(alignment['kind'] == ('recorded_end_native' if proof['native_recorded_end'] else 'stable_future_pending_buffer'),
                'boundary_unproved', 'Capture alignment kind disagrees with native reader boundary')
        return proof
    require(alignment['kind'] != 'stable_future_pending_buffer', 'boundary_unproved',
            'Stable reader boundaries require independently recomputed native reader proof')
    boundary_fields = ('pid', 'create_time', 'sample_sequence', 'loaded_source_files', 'record_boundary',
                       'phase', 'native_paused', 'native_recorded_end', 'game_clock_bits')
    boundary_events = [r['payload'] for r in native['rows']
                       if r.get('payload', {}).get('tag') == 'player_state_boundary'
                       and all(r['payload'].get(k) == proof.get(k) for k in boundary_fields)]
    require(len(boundary_events) == 1, 'boundary_unproved',
            'Boundary proof must match one independently emitted native log event')
    require(proof.get('producer') == 'client_native' and proof.get('pid') == native['identity']['pid']
            and proof.get('create_time') == native['identity']['create_time']
            and proof.get('sample_sequence') == sample['sequence']
            and proof.get('native_log_sha256') == artifacts[capture['native_artifact_id']]['sha256'],
            'boundary_identity_mismatch', 'Boundary does not identify this native sample and process')
    expected_sources = [(r['section'], r['sha256']) for r in capture['source_files']]
    actual_sources = [(r['section'], r['sha256']) for r in proof.get('loaded_source_files', [])]
    require(actual_sources == expected_sources, 'boundary_source_mismatch', 'Native boundary loaded source identity differs')
    boundary = proof.get('record_boundary', {})
    require(type(boundary.get('section')) is int and type(boundary.get('record_offset')) is int
            and boundary['section'] in {r['section'] for r in capture['source_files']}
            and boundary['record_offset'] >= 0 and proof.get('phase') == 'after_apply',
            'boundary_unproved', 'Actual applied section/record offset is required')
    if alignment['kind'] == 'recorded_end_paused':
        require(proof.get('native_paused') is True and proof.get('native_recorded_end') is True,
                'boundary_unproved', 'Paused recorded EOF must be independently observed')
    else:
        require(sample.get('atomic_record_boundary') is True
                and sample.get('record_boundary') == boundary,
                'boundary_unproved', 'Timed atomic boundary must originate in the native sample')
    require(proof.get('game_clock_bits') == sample['game_clock']['bits'],
            'boundary_clock_mismatch', 'Native boundary and sample clocks differ')
    return proof


def verify_capture(capture_dir, require_restored=False, capture_override=None):
    base = Path(capture_dir).resolve()
    capture = capture_override if capture_override is not None else read_json(base / 'capture.json')
    errors, checks = [], []
    native, proof = None, None
    artifacts = {}
    try:
        require(capture.get('schema_version') == 'player_state.capture.v1', 'schema_error', 'Unknown capture schema')
        identifier(capture.get('capture_id'))
        require(capture.get('partition') in {'development', 'holdout'}, 'partition_missing', 'Frozen partition is required')
        for ref in capture.get('artifacts', []):
            artifact_id = identifier(ref.get('artifact_id'))
            require(artifact_id not in artifacts, 'duplicate_artifact', 'Artifact IDs must be unique')
            artifacts[artifact_id] = ref
        sources = capture.get('source_files', [])
        require(bool(sources), 'source_missing', 'Source section identities are required')
        sections = [r.get('section') for r in sources]
        require(all(type(n) is int and n >= 0 for n in sections) and len(set(sections)) == len(sections)
                and sections == sorted(sections), 'source_inventory_invalid', 'Source section order must be unique and sorted')
        for ref in [*sources, *artifacts.values()]:
            path = ref_path(base, ref)
            require(path.is_file() and path.stat().st_size > 0, 'artifact_missing', f'Missing or empty artifact: {path}')
            actual = digest(path)
            checks.append({'path': str(path), 'expected_sha256': ref['sha256'], 'actual_sha256': actual})
            require(actual == ref['sha256'], 'hash_mismatch', f'Artifact changed: {path}')
        require(capture.get('native_artifact_id') in artifacts, 'native_log_missing', 'Native log reference is required')
        native = inspect_native(ref_path(base, artifacts[capture['native_artifact_id']]), capture.get('sample_sequence'))
        expected = capture.get('process', {})
        require(all(expected.get(k) == native['identity'].get(k) for k in ('pid', 'create_time', 'exe', 'sha256')),
                'process_identity_mismatch', 'Capture and native process identity differ')
        screenshots = [r for r in artifacts.values() if r.get('role') == 'screenshot']
        require(bool(screenshots), 'screenshot_missing', 'At least one original screenshot is required')
        for ref in screenshots:
            with ref_path(base, ref).open('rb') as stream:
                header = stream.read(24)
            require(header[:8] == b'\x89PNG\r\n\x1a\n' and len(header) == 24
                    and all(struct.unpack('>II', header[16:24])), 'screenshot_invalid', 'Screenshot must be a nonempty PNG')
        actions = [r for r in artifacts.values() if r.get('role') == 'actions']
        require(bool(actions), 'actions_missing', 'Original OS action transcript is required')
        action_rows = [row for ref in actions for row in jsonl(ref_path(base, ref))]
        matching = [row for row in action_rows if 'error' not in row.get('result', {})
                    and row.get('result', {}).get('state', {}).get('owned_pid') == expected['pid']]
        require(bool(matching), 'action_identity_mismatch', 'No successful OS action belongs to the captured process')
        shot_names = {PureWindowsPath(row['result']['shot']['path']).name for row in matching
                      if row.get('result', {}).get('shot', {}).get('pid') == expected['pid']}
        require(all(Path(ref['path']).name in shot_names for ref in screenshots),
                'screenshot_identity_mismatch', 'Screenshot filenames and process must match the OS action receipt')
        proof = verify_alignment(capture, native, artifacts, base)
        if require_restored:
            roles = {r['role']: r for r in artifacts.values()}
            for role in ('slot_backup', 'slot_restored', 'worker_cleanup', 'worker_exited', 'restored_inventory'):
                require(role in roles, 'cleanup_missing', f'Missing cleanup evidence: {role}')
            backup = read_json(ref_path(base, roles['slot_backup']))
            restore = read_json(ref_path(base, roles['slot_restored']))
            cleanup = read_json(ref_path(base, roles['worker_cleanup']))
            exited = read_json(ref_path(base, roles['worker_exited']))
            inventory = read_json(ref_path(base, roles['restored_inventory']))
            trials = [r for r in inventory.get('trials', []) if r.get('trial') == capture.get('trial')]
            require(len(trials) == 1, 'restore_mismatch', 'Restored inventory must identify this exact trial')
            restored_files = trials[0]['files']
            require(cleanup.get('worker_absent') is True and cleanup.get('task_absent') is True
                    and exited.get('state', {}).get('owned_alive') is False
                    and exited['state'].get('owned_pid') == expected['pid']
                    and inventory.get('old_owned_game_pid') == expected['pid']
                    and inventory.get('old_owned_game_pid_absent') is True
                    and inventory.get('old_worker_observer_processes') == [],
                    'cleanup_incomplete', 'Owned game, observer, worker and task must be absent')
            actual_hashes = {r['name']: r['sha256'] for r in restored_files if r.get('exists') is True}
            require_backup(backup, actual_hashes, [])
            originals = [r for r in artifacts.values() if r.get('role') == 'original_backup']
            require({Path(r['path']).name: r['sha256'] for r in originals}
                    == {r['name']: r['sha256'] for r in backup['files']},
                    'backup_conflict', 'Hashed original backup files are missing or changed')
            original_times = {r['name']: tuple(utc_timestamp(r.get(k)) for k in ('last_write_utc', 'creation_utc'))
                              for r in backup['files']}
            require(all(tuple(utc_timestamp(r.get(k)) for k in ('last_write_utc', 'creation_utc')) == original_times.get(r['name'])
                        for r in restored_files), 'restore_mismatch', 'Restored file timestamps differ')
            require(restore.get('all_backup_hashes_match') is True and restore.get('other_groups_touched') is False
                    and restore.get('restored_frames') == len(backup['files'])
                    and restore.get('trial') == capture.get('trial'),
                    'restore_mismatch', 'Restoration receipt and actual slot inventory differ')
        require(all(digest(row['path']) == row['expected_sha256'] for row in checks),
                'hash_mismatch', 'Consumed evidence changed during verification')
    except (CaptureError, KeyError, TypeError, ValueError, OSError) as exc:
        errors.append({'code': getattr(exc, 'code', 'schema_error'), 'message': str(exc)})
    return {'ok': not errors, 'capture_id': capture.get('capture_id'),
            'status': 'failed' if errors else ('aligned' if proof else 'observation_only'),
            'alignment_verified': proof is not None, 'restoration_verified': require_restored and not errors,
            'errors': errors, 'file_checks': checks,
            'native': {k: v for k, v in (native or {}).items() if k not in {'rows', 'sample'}},
            'record_boundary': proof.get('record_boundary') if proof else None}


def import_capture(spec_path, output_dir):
    spec_path = Path(spec_path).resolve()
    spec = read_json(spec_path)
    output = Path(output_dir).resolve()
    require(not output.exists(), 'output_exists', 'Capture directory must be new')
    refs = [*spec.get('source_files', []), *spec.get('artifacts', [])]
    for ref in refs:
        path = ref_path(spec_path.parent, ref)
        actual = metadata(path)
        if ref.get('sha256') is not None:
            require(actual['sha256'] == ref['sha256'], 'hash_mismatch', f'Import source changed: {path}')
        ref.update(actual)
    spec['schema_version'] = 'player_state.capture.v1'
    spec['import_spec'] = metadata(spec_path)
    output.mkdir(parents=True, exist_ok=False)
    publish(output / 'capture.json', spec, [spec_path, *(r['path'] for r in refs)])
    result = verify_capture(output)
    publish(output / 'verification.json', result, [output / 'capture.json', *(r['path'] for r in refs)])
    publish(output / 'freeze.json', {'capture': metadata(output / 'capture.json'),
                                    'verification': metadata(output / 'verification.json')},
            [output / 'capture.json', output / 'verification.json'])
    return result


def observed(value, source):
    return {'status': 'observed', 'value': value, 'source_refs': [source]}


def native_float(raw):
    bits = raw.get('bits')
    require(type(bits) is int and 0 <= bits <= 0xffffffff, 'native_value_invalid', 'Missing uint32 resource bits')
    value = struct.unpack('>f', struct.pack('>I', bits))[0]
    require(math.isfinite(value) and value == raw.get('value'), 'native_value_invalid', 'Resource value and bits disagree')
    return {'float32_bits': f'{bits:08x}', 'value': value}


def counter(value):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0 and int(value) == value,
            'native_value_invalid', 'Counter must be a nonnegative integer')
    return int(value)


def export_reference(capture_dir, manifest_path, output_dir, *, query_clock='game_time'):
    require(query_clock in {'game_time', 'record_time'}, 'unsupported_query_clock', 'Unsupported reference query clock')
    base, manifest_path, output = Path(capture_dir).resolve(), Path(manifest_path).resolve(), Path(output_dir).resolve()
    result = verify_capture(base, require_restored=True)
    require(result['ok'], 'capture_invalid', json.dumps(result['errors']))
    require(result['alignment_verified'], 'boundary_unproved', 'Unaligned samples remain observation-only')
    require(not output.exists(), 'output_exists', 'Reference registry destination must be new')
    capture = read_json(base / 'capture.json')
    registry = deepcopy(read_json(manifest_path))
    frozen = read_json(manifest_path.parent / 'freeze.json')
    require(frozen.get('manifest', {}).get('sha256') == digest(manifest_path),
            'reference_freeze_mismatch', 'Input registry differs from its frozen hash')
    records = [r for r in registry['recordings'] if capture['recording_id'] in [r['recording_id'], *r.get('aliases', [])]]
    require(len(records) == 1, 'recording_identity_missing', 'Capture must identify one frozen recording')
    recording = records[0]
    require(recording['partition'] == capture['partition'], 'partition_changed', 'Development/holdout partition changed')
    require([(r['section'], r['sha256']) for r in recording['source_files']]
            == [(r['section'], r['sha256']) for r in capture['source_files']],
            'source_identity_mismatch', 'Capture source differs from the frozen registry')
    artifacts = {r['artifact_id']: r for r in capture['artifacts']}
    native_ref = artifacts[capture['native_artifact_id']]
    native = inspect_native(ref_path(base, native_ref), capture.get('sample_sequence'))
    sample = native['sample']
    source_id = capture['capture_id'] + '-native'
    require(not any(r['source_id'] == source_id for r in registry.get('reference_sources', [])),
            'duplicate_reference', 'Capture was already imported')
    registry.setdefault('reference_sources', []).append(dict(native_ref, source_id=source_id, kind='client_native'))
    players = []
    for row in sample['players']:
        native_float(row['assists'])
        native_float(row['resource14'])
        kda = {k: counter(row[k]['value']) for k in ('kills', 'deaths', 'assists')}
        fields = {'name': observed(row['display_name'], source_id), 'kda': observed(kda, source_id),
                  'hero': {'status': 'unobserved'},
                  'minion_kills': observed(counter(row['resource14']['value']), source_id),
                  'gold_balance': observed(native_float(row['gold_balance']), source_id),
                  'net_worth': observed(native_float(row['net_worth']), source_id), 'items': {'status': 'unobserved'}}
        inventory = row.get('inventory')
        if inventory is not None:
            items = []
            for item in inventory['items']:
                if item is not None:
                    require(type(item.get('definition_id')) is int and item['definition_id'] > 0
                            and type(item.get('quantity')) is int and item['quantity'] > 0,
                            'native_value_invalid', 'Invalid native item identity or quantity')
                    items.append({'native_item_id': item['definition_id'], 'quantity': item['quantity']})
            require(len(items) == inventory['occupied'], 'inventory_incomplete', 'Occupied count and entries disagree')
            fields['native_items'] = observed(items, source_id)
        players.append({'reference_player_id': f"{capture['capture_id']}-actor-{row['native_actor_id']}",
                        'native_actor_id': row['native_actor_id'],
                        'actor_link': {'status': 'observed', 'source_refs': [source_id]}, 'fields': fields})
    eof = capture['alignment']['kind'] in {'recorded_end_paused', 'recorded_end_native'}
    require(query_clock != 'record_time' or capture['alignment']['kind'] == 'stable_future_pending_buffer',
            'boundary_unproved', 'Record-time export requires verified stable native pending-buffer alignment')
    observation = {'observation_id': capture['capture_id'], 'clock_kind': 'recorded_end' if eof else query_clock,
                   'record_boundary': result['record_boundary'], 'source_refs': [source_id], 'players': players,
                   'replay_scope': capture.get('replay_scope', recording.get('replay_scope'))}
    if not eof:
        from vg.core.native_query import GameTime, RecordTime, select_native_query
        game_clock = native_float(sample['game_clock'])
        if query_clock == 'record_time':
            observation['record_time'] = native_float(sample['replay_reader_before']['playback_time'])['value']
            observation['observed_game_time'] = game_clock['value']
            observation['observed_game_time_bits'] = game_clock['float32_bits']
            cutoff = RecordTime(observation['record_time'])
        else:
            observation['game_time'] = game_clock['value']
            cutoff = GameTime(observation['game_time'])
        query = select_native_query([(r['section'], ref_path(base, r).read_bytes()) for r in capture['source_files']],
                                    cutoff)
        boundary = result['record_boundary']
        require(query.valid and query.record_boundary == (boundary['section'], boundary['record_offset']),
                f'unsupported_{query_clock}_boundary',
                f'Native {query_clock} clock does not select the proven applied boundary: {query.status}; '
                f'query={query.record_boundary}, native={boundary}')
    require(not any(r.get('observation_id') == observation['observation_id'] for r in recording.get('observations', [])),
            'duplicate_observation', 'Observation ID already exists')
    recording.setdefault('observations', []).append(observation)
    for row in registry['recordings']:
        for ref in row.get('source_files', []) + row.get('images', []):
            ref['path'] = str(ref_path(manifest_path.parent, ref))
    for ref in registry.get('reference_sources', []) + registry.get('historical_sources', []):
        ref['path'] = str(ref_path(manifest_path.parent, ref))
    output.mkdir(parents=True, exist_ok=False)
    publish(output / 'manifest.json', registry, [manifest_path, base / 'capture.json', native_ref['path']])
    publish(output / 'freeze.json', {'manifest': metadata(output / 'manifest.json'), 'capture': metadata(base / 'capture.json')},
            [output / 'manifest.json', base / 'capture.json'])
    return {'ok': True, 'manifest': str(output / 'manifest.json'), 'observation_id': observation['observation_id'],
            'players': len(players), 'unobserved_fields': ['hero', 'items'],
            'minion_kills_semantics': 'native scoreboard CS; creature taxonomy unproved'}
