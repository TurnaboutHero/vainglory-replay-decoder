"""Private independent-reference registry and exact player-state comparison CLI.

This module is an offline validator. Production readers must never import it.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

from vg.core.replay_output import ReportInputs, ReplayOutputError, write_report_output

FIELDS = ('name', 'hero', 'kda', 'minion_kills', 'items', 'gold_balance', 'net_worth')
COMPONENTS = {'roster': ('name', 'hero'), 'counters': ('kda', 'minion_kills', 'gold_balance', 'net_worth'),
              'inventory': ('items',)}
INDEPENDENT = {'client_native', 'client_render', 'definition_asset', 'receiver_apply'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def resolved(base, path):
    return (base / path).resolve()


def metadata(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path), 'size': path.stat().st_size}


def provenance():
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return {'commit': result.stdout.strip() if result.returncode == 0 else None,
            'interpreter': sys.executable, 'python': sys.version, 'invocation': sys.argv}


def publish(output, data, sources, snapshot=None):
    output = Path(output)
    inputs = snapshot or ReportInputs(files=tuple(Path(p) for p in sources if Path(p).exists()),
                          reserved_files=tuple(Path(p) for p in sources))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_report_output(inputs, output, json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def source_paths(manifest, base):
    paths = []
    for row in manifest.get('recordings', []):
        for item in row.get('source_files', []) + row.get('images', []):
            paths.append(resolved(base, item['path']))
    for item in manifest.get('historical_sources', []) + manifest.get('reference_sources', []):
        paths.append(resolved(base, item['path']))
    return paths


def prepare(asset_root, output_dir):
    root, dest = Path(asset_root).resolve(), Path(output_dir).resolve()
    export = root / 'accuracy-20261004/corpus/manifest.json'
    manifest = {'schema_version': 'player_state.reference.v1', 'recordings': [],
                'historical_rows': [], 'historical_sources': [], 'reference_sources': [],
                'inventory_errors': [], 'provenance': provenance()}
    inputs = []
    if export.exists():
        inputs.append(export)
        exported = read_json(export)
        manifest['client_sha256'] = exported.get('client_sha256')
        for original in exported['recordings']:
            row = deepcopy(original)
            for item in row.get('source_files', []) + row.get('images', []):
                item['path'] = str(resolved(export.parent, item['path']))
            row.setdefault('observations', [])
            row.setdefault('aliases', [])
            manifest['recordings'].append(row)
        manifest['upstream_manifest'] = metadata(export)
    else:
        manifest['inventory_errors'].append({'code': 'source_missing', 'path': str(export)})
    # Controls are separate recordings unless the complete ordered source hashes match.
    controls = root / 'stat-followup-20261003/controls'
    for alias in ('normal17', 'C34'):
        files = sorted((controls / alias).glob('*.vgr'), key=lambda p: int(p.stem.rsplit('.', 1)[1]))
        if not files:
            if not any(alias == r['recording_id'] or alias in r.get('aliases', []) for r in manifest['recordings']):
                manifest['inventory_errors'].append({'code': 'source_missing', 'alias': alias})
            continue
        refs = [dict(metadata(p), section=int(p.stem.rsplit('.', 1)[1])) for p in files]
        signature = [(r['section'], r['sha256']) for r in refs]
        matching = [r for r in manifest['recordings'] if [(s['section'], s['sha256']) for s in r['source_files']] == signature]
        if matching:
            if alias != matching[0]['recording_id'] and alias not in matching[0]['aliases']:
                matching[0]['aliases'].append(alias)
        elif not any(r['recording_id'] == alias for r in manifest['recordings']):
            manifest['recordings'].append({'recording_id': alias, 'aliases': [], 'partition': 'development',
                                           'source_files': refs, 'observations': []})
        else:
            manifest['inventory_errors'].append({'code': 'control_source_conflict', 'alias': alias})
    historical = [('tournament', root / 'offline-repo/vg/output/tournament_truth.json'),
                  ('item_count', root / 'offline-repo/vg/docs/item_slotcount_truth_5_11.json')]
    for kind, path in historical:
        if not path.exists():
            manifest['inventory_errors'].append({'code': 'source_missing', 'kind': kind, 'path': str(path)})
            continue
        inputs.append(path)
        manifest['historical_sources'].append(dict(metadata(path), kind=kind))
        matches = read_json(path)['matches']
        for index, match in (enumerate(matches, 1) if isinstance(matches, list) else matches.items()):
            alias = f'M{index}'
            if kind == 'tournament':
                basename = match['replay_file'].replace('\\', '/').rsplit('/', 1)[-1]
                candidates = [r for r in manifest['recordings'] if any(
                    s.get('source_path', s['path']).replace('\\', '/').rsplit('/', 1)[-1] == basename
                    for s in r['source_files'])]
                if len(candidates) == 1 and alias not in candidates[0]['aliases']:
                    candidates[0]['aliases'].append(alias)
                rows = match['players']
            else:
                rows = match['slots']
            for name, value in rows.items():
                manifest['historical_rows'].append({'kind': kind, 'recording_alias': alias, 'name': name,
                    'original': deepcopy(value), 'source': str(path), 'status': 'historical_partial',
                    'limitations': ['native_actor_link_unobserved', 'record_boundary_unobserved',
                                    'gold_is_display_only' if kind == 'tournament' else 'item_identities_unobserved']})
    manifest['expected_counts'] = {'corpus': 56, 'tournament': 109, 'item_count': 60}
    inputs += source_paths(manifest, dest)
    output = dest / 'manifest.json'
    # Never replace a frozen registry: later observations belong in a separately frozen registry.
    if output.exists():
        raise ValueError(f'prepare destination already exists: {output}')
    publish(output, manifest, inputs)
    publish(dest / 'freeze.json', {'manifest': metadata(output), 'provenance': provenance()}, [output, *inputs])
    return manifest


def audit(manifest, base):
    errors = list(manifest.get('inventory_errors', []))
    seen, aliases = set(), set()
    for row in manifest['recordings']:
        identity = row['recording_id']
        if identity in seen:
            errors.append({'code': 'duplicate_recording', 'recording_id': identity})
        seen.add(identity)
        for alias in [identity, *row.get('aliases', [])]:
            if alias in aliases:
                errors.append({'code': 'duplicate_alias', 'alias': alias})
            aliases.add(alias)
        sections = [s['section'] for s in row['source_files']]
        if not sections or len(sections) != len(set(sections)):
            errors.append({'code': 'source_inventory_error', 'recording_id': identity})
    source_ids = [s['source_id'] for s in manifest.get('reference_sources', [])]
    if len(source_ids) != len(set(source_ids)):
        errors.append({'code': 'duplicate_reference_source'})
    checks = []
    refs = [s for r in manifest['recordings'] for s in r.get('source_files', []) + r.get('images', [])]
    refs += manifest.get('historical_sources', []) + manifest.get('reference_sources', [])
    for ref in refs:
        path = resolved(base, ref['path'])
        check = {'path': str(path), 'expected_sha256': ref['sha256']}
        if not path.is_file():
            check['code'] = 'source_missing'
        else:
            check['actual_sha256'] = digest(path)
            check['code'] = 'ok' if check['actual_sha256'] == ref['sha256'] else 'hash_mismatch'
        checks.append(check)
        if check['code'] != 'ok':
            errors.append(check)
    history = manifest.get('historical_rows', [])
    counts = {'corpus': sum(r['recording_id'].startswith('C') and r['recording_id'][1:].isdigit()
                            for r in manifest['recordings']),
              **{kind: sum(r['kind'] == kind for r in history) for kind in ('tournament', 'item_count')}}
    for kind, expected in manifest.get('expected_counts', {}).items():
        if counts.get(kind) != expected:
            errors.append({'code': 'inventory_count_error', 'kind': kind, 'expected': expected, 'actual': counts.get(kind)})
    lookup = {alias: r['recording_id'] for r in manifest['recordings'] for alias in [r['recording_id'], *r.get('aliases', [])]}
    overlap = []
    for row in history:
        overlap.append({'kind': row['kind'], 'recording_alias': row['recording_alias'], 'name': row['name'],
                        'corpus_recording_id': lookup.get(row['recording_alias']), 'status': row['status']})
    code = 2 if any(e['code'] in {'hash_mismatch', 'duplicate_recording', 'duplicate_alias', 'duplicate_reference_source'} for e in errors) else int(bool(errors))
    return {'ok': not errors, 'exit_code': code, 'counts': counts, 'errors': errors,
            'source_checks': checks, 'historical_rows': history, 'overlap': overlap,
            'note': 'Historical player rows overlap corpus recordings; they are not additional recordings or six-field truth.'}


def float_bits(value):
    if isinstance(value, dict):
        bits = value.get('float32_bits')
        if bits is not None:
            encoded = float_bits(bits)
            if 'value' in value and float_bits(value['value']) != encoded:
                raise ValueError('native value and float32 bits disagree')
            return encoded
        value = value.get('value')
    if isinstance(value, str):
        raw = value.removeprefix('0x')
        if len(raw) != 8:
            raise ValueError('float32 bits must contain eight hexadecimal digits')
        bits = int(raw, 16)
        if not 0 <= bits <= 0xffffffff or not math.isfinite(struct.unpack('>f', bits.to_bytes(4, 'big'))[0]):
            raise ValueError('nonfinite native gold bits')
        return f'{bits:08x}'
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('finite native gold required')
    return struct.pack('>f', value).hex()


def item_counts(items):
    result = Counter()
    for item in items:
        identity, quantity = item['native_item_id'], item['quantity']
        if isinstance(identity, bool) or not isinstance(identity, int) or identity < 0:
            raise ValueError('invalid native item identity')
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise ValueError('invalid native item multiplicity')
        # Quantity 0 (after 0444, before 044b) is still a held item; keep its key.
        result[identity] += quantity
    return sorted(result.items())


def actual_field(player, field):
    if field == 'name':
        return player.get('name', player.get('display_name'))
    if field == 'hero':
        hero = player.get('hero', player.get('hero_name'))
        return hero.get('name') if isinstance(hero, dict) else hero
    if field == 'kda':
        return player.get('kda', {k: player.get(k) for k in ('kills', 'deaths', 'assists')})
    if field == 'items' and isinstance(player.get('items'), (list, tuple)):
        return [dict(item, native_item_id=item['definition_id'])
                if isinstance(item, dict) and 'definition_id' in item and 'native_item_id' not in item
                else item for item in player['items']]
    return player.get(field)


def independent(refs, sources):
    return bool(refs) and all(ref in sources and sources[ref].get('kind') in INDEPENDENT for ref in refs)


def compare_observation(observation, actual, *, fields=FIELDS, reference_sources=()):
    """Compare only independently linked actors; no name matching or inferred truth."""
    issues, comparisons = [], []
    sources = {s['source_id']: s for s in reference_sources}
    def issue(code, **details):
        issues.append({'code': code, **details})
    clock = observation.get('clock_kind')
    if clock in ('game_time', 'record_time'):
        time = observation.get(clock)
        if isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time) or time < 0:
            issue('incompatible_clock', reason=f'finite nonnegative observed {clock} required')
    if clock not in ('recorded_end', 'game_time', 'record_time'):
        issue('incompatible_clock', expected=clock)
    else:
        scope = 'recorded_end' if clock == 'recorded_end' else 'capture'
        if (actual.get('scope') != scope
                or (scope == 'capture' and actual.get('requested_' + clock) != observation.get(clock))
                or (clock == 'record_time' and actual.get('query_clock') != clock)):
            issue('incompatible_clock', expected={'scope': scope, 'clock': clock, 'time': observation.get(clock)},
                  actual={'scope': actual.get('scope'), 'clock': actual.get('query_clock'),
                          'time': actual.get('requested_' + clock)})
    boundary = observation.get('record_boundary')
    if not isinstance(boundary, dict) or any(type(boundary.get(k)) is not int or boundary[k] < 0 for k in ('section', 'record_offset')):
        issue('boundary_unobserved')
    if not boundary or actual.get('record_boundary') != boundary:
        issue('boundary_mismatch', expected=observation.get('record_boundary'), actual=actual.get('record_boundary'))
    if not independent(observation.get('source_refs'), sources):
        issue('independent_source_missing')
    if actual.get('support_status') not in ('supported', 'ok'):
        issue('unsupported_state', actual=actual.get('support_status'))
    if observation.get('replay_scope') and observation['replay_scope'] != actual.get('replay_scope'):
        issue('replay_scope_mismatch', expected=observation['replay_scope'], actual=actual.get('replay_scope'))
    players = actual.get('players', [])
    ids = [p.get('native_actor_id') for p in players]
    reference = observation.get('players', [])
    expected_ids = [p.get('native_actor_id') for p in reference]
    reference_ids = [p.get('reference_player_id') for p in reference]
    if len(reference_ids) != len(set(reference_ids)):
        issue('duplicate_reference_player')
    if not reference:
        issue('reference_missing', required_missing=list(fields))
    for label, values in [('actual', ids), ('reference', expected_ids)]:
        if any(isinstance(v, bool) or not isinstance(v, int) or not 0 < v <= 0xffffffff for v in values):
            issue('actor_invalid', side=label)
        if len(set(values)) != len(values):
            issue('duplicate_actor', side=label)
    if set(ids) != set(expected_ids):
        issue('actor_set_mismatch', expected=expected_ids, actual=ids)
    by_id = {p.get('native_actor_id'): p for p in players}
    for player in reference:
        actor = player.get('native_actor_id')
        link = player.get('actor_link', {})
        if not player.get('reference_player_id') or link.get('status') != 'observed' or not independent(link.get('source_refs'), sources):
            issue('actor_link_unproved', actor=actor)
        found = by_id.get(actor, {})
        for field in fields:
            ref = player.get('fields', {}).get(field, {})
            if ref.get('status') != 'observed' or ref.get('value') is None or not independent(ref.get('source_refs'), sources):
                issue('reference_missing', actor=actor, field=field, required_missing=[field])
                continue
            expected, observed = ref['value'], actual_field(found, field)
            status = found.get('field_status', {}).get(field)
            if isinstance(status, dict):
                status = status.get('status')
            if status is not None and status not in ('observed', 'supported', 'ok'):
                issue('value_unsupported', actor=actor, field=field, status=status)
                continue
            if observed is None or (field == 'kda' and any(observed.get(k) is None for k in ('kills', 'deaths', 'assists'))):
                issue('value_missing', actor=actor, field=field)
                continue
            try:
                if field in ('gold_balance', 'net_worth'):
                    # A displayed decimal is never a native reference.
                    if not isinstance(expected, (str, dict)):
                        issue('reference_missing', actor=actor, field=field, required_missing=[field], reason='native_float32_bits_required')
                        continue
                    equal = float_bits(expected) == float_bits(observed)
                elif field == 'items':
                    equal = item_counts(expected) == item_counts(observed)
                    if ref.get('slot_order_proven'):
                        equal = equal and expected == observed
                else:
                    if field == 'kda' and any(type(v.get(k)) is not int or v[k] < 0 for v in (expected, observed) for k in ('kills', 'deaths', 'assists')):
                        raise ValueError('KDA requires nonnegative integer counters')
                    if field == 'minion_kills' and any(type(v) is not int or v < 0 for v in (expected, observed)):
                        raise ValueError('minions requires a nonnegative integer counter')
                    equal = type(expected) is type(observed) and expected == observed
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                issue('invalid_field', actor=actor, field=field, reason=str(error))
                continue
            comparisons.append({'actor': actor, 'reference_player_id': player['reference_player_id'], 'field': field,
                                'expected': expected, 'actual': observed, 'matched': equal, 'source_refs': ref['source_refs']})
            if not equal:
                issue('field_mismatch', actor=actor, field=field, expected=expected, actual=observed)
    return {'ok': not issues, 'observation_id': observation.get('observation_id'),
            'query': {k: observation.get(k) for k in ('clock_kind', 'game_time', 'record_time', 'record_boundary')},
            'required': len(reference) * len(fields), 'matched': sum(c['matched'] for c in comparisons),
            'required_missing': sorted({f for i in issues for f in i.get('required_missing', [])}),
            'issues': issues, 'comparisons': comparisons}


def mutate(observation, mutation):
    result = deepcopy(observation)
    if mutation == 'remove-items':
        for player in result.get('players', []):
            player.get('fields', {}).pop('items', None)
        return result
    for player in result.get('players', []):
        fields = player.get('fields', {})
        if mutation == 'flip-one-gold-bit' and fields.get('gold_balance', {}).get('status') == 'observed':
            fields['gold_balance']['value'] = f'{int(float_bits(fields["gold_balance"]["value"]), 16) ^ 1:08x}'
            return result
        if mutation == 'drop-one-duplicate-item' and fields.get('items', {}).get('status') == 'observed':
            items = fields['items']['value']
            counts = dict(item_counts(items))
            for item in items:
                if counts[item['native_item_id']] > 1:
                    if item['quantity'] > 1:
                        item['quantity'] -= 1
                    else:
                        items.remove(item)
                    return result
    raise ValueError(f'mutation precondition missing: {mutation}')


def legacy_state(actual):
    state = actual.get('player_state') or {}
    players = [dict(player, items=player.get('item_details'))
               for group in ('left_team', 'right_team', 'unassigned_players')
               for player in actual.get(group, [])]
    consistent = all(player.get('state_scope') == state.get('scope')
                     and player.get('record_boundary') == state.get('record_boundary')
                     and player.get('replay_scope') == state.get('replay_scope')
                     for player in players)
    return dict(state, players=players,
                support_status=state.get('support_status') if consistent else 'inconsistent_legacy_state')


def decode(recording, observation, base, surface, reader):
    replay = resolved(base, min(recording['source_files'], key=lambda s: s['section'])['path'])
    if reader:
        from vg.decoder_v2.completeness import load_frames
        from vg.core.native_roster import read_native_roster
        from vg.core.native_query import GameTime, RecordTime
        from vg.core.native_stats import read_native_stats
        frames = load_frames(str(replay))
        cutoff = (GameTime(observation['game_time']) if observation.get('clock_kind') == 'game_time' else
                  RecordTime(observation['record_time']) if observation.get('clock_kind') == 'record_time' else None)
        roster = read_native_roster(frames, cutoff=cutoff)
        if reader == 'roster':
            result = roster
        elif reader == 'counters':
            result = read_native_stats(frames, [p.entity_id for p in roster.players], cutoff=cutoff)
        else:
            from vg.core.native_inventory import read_native_inventory
            result = read_native_inventory(frames, [p.entity_id for p in roster.players], cutoff=cutoff)
        raw = asdict(result)
        for player in raw['players']:
            player['native_actor_id'] = player.pop('entity_id')
        # Readers must expose their real applied boundary; never copy the expected boundary.
        raw.update(scope='capture' if cutoff else 'recorded_end', query_clock=observation['clock_kind'],
                   requested_game_time=cutoff.seconds if isinstance(cutoff, GameTime) else None,
                   requested_record_time=cutoff.seconds if isinstance(cutoff, RecordTime) else None,
                   support_status='supported' if result.valid else result.status)
        return raw, {'reader': reader, 'replay': str(replay)}
    if observation.get('clock_kind') == 'record_time' and surface == 'legacy-cli':
        return {'support_status': 'unsupported_query_clock', 'players': []}, {
            'surface': surface, 'query_clock': 'record_time', 'invoked': False,
            'reason': 'Legacy CLI does not expose replay-record time queries'}
    command = [sys.executable, '-B', '-m', 'vg.core.unified_decoder' if surface == 'legacy-cli' else 'vg.decoder_v2.decode_match', str(replay)]
    if observation.get('clock_kind') == 'game_time':
        command += ['--at-game-time', str(observation['game_time'])]
    elif observation.get('clock_kind') == 'record_time':
        command += ['--at-record-time', str(observation['record_time'])]
    run = subprocess.run(command, capture_output=True, text=True, timeout=180)
    receipt = {'command': command, 'returncode': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
    if run.returncode:
        return {'support_status': 'decoder_error', 'players': []}, receipt
    actual = json.loads(run.stdout)
    return legacy_state(actual) if surface == 'legacy-cli' else actual, receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--asset-root', type=Path, required=True)
    prep.add_argument('--output-dir', type=Path, required=True)
    for name in ('audit', 'compare', 'verify-capture'):
        child = sub.add_parser(name)
        child.add_argument('--manifest', type=Path, required=True)
        child.add_argument('--output', type=Path, required=True)
        if name in ('compare', 'verify-capture'):
            child.add_argument('--recording', action='append')
            child.add_argument('--all-observed', action='store_true')
            child.add_argument('--require-six-fields', action='store_true')
            child.add_argument('--coverage-only', action='store_true')
            child.add_argument('--reader', choices=tuple(COMPONENTS))
            child.add_argument('--surface', choices=('default-cli', 'legacy-cli'), default='default-cli')
            child.add_argument('--expect-support-status')
            child.add_argument('--mutate-reference', choices=('remove-items', 'drop-one-duplicate-item', 'flip-one-gold-bit'))
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            manifest = prepare(args.asset_root, args.output_dir)
            report = audit(manifest, args.output_dir)
            publish(args.output_dir / 'prepare-report.json', report, [args.output_dir / 'manifest.json', *source_paths(manifest, args.output_dir)])
            return report['exit_code']
        manifest = read_json(args.manifest)
        base = args.manifest.parent
        inputs = [args.manifest, *source_paths(manifest, base)]
        freeze = base / 'freeze.json'
        if freeze.exists():
            inputs.append(freeze)
        snapshot = ReportInputs(files=tuple(p for p in inputs if p.exists()), reserved_files=inputs)
        report = audit(manifest, base)
        if freeze.exists():
            if read_json(freeze)['manifest']['sha256'] != digest(args.manifest):
                report['errors'].append({'code': 'frozen_manifest_changed'})
                report.update(ok=False, exit_code=2)
        report.update(provenance=provenance(), manifest_sha256=digest(args.manifest))
        if args.command != 'audit' and report['ok']:
            selected = manifest['recordings']
            if args.recording:
                selected = [r for r in selected if set(args.recording) & {r['recording_id'], *r.get('aliases', [])}]
                missing = set(args.recording) - {a for r in selected for a in [r['recording_id'], *r.get('aliases', [])]}
                if missing:
                    report['errors'].append({'code': 'recording_missing', 'recordings': sorted(missing)})
            report['recordings'] = []
            fields = COMPONENTS[args.reader] if args.reader and not args.require_six_fields else FIELDS
            for row in selected:
                observations = row.get('observations', [])
                entry = {'recording_id': row['recording_id'], 'partition': row.get('partition'),
                         'support': row.get('support'), 'observation_count': len(observations), 'results': []}
                report['recordings'].append(entry)
                if args.coverage_only:
                    entry['accuracy_certified'] = False
                    continue
                if not observations:
                    report['errors'].append({'code': 'reference_missing', 'recording_id': row['recording_id'], 'required_missing': list(fields)})
                    continue
                for observation in observations:
                    reference = mutate(observation, args.mutate_reference) if args.mutate_reference else observation
                    actual, receipt = decode(row, reference, base, args.surface, args.reader)
                    result = compare_observation(reference, actual, fields=fields, reference_sources=manifest.get('reference_sources', []))
                    result['decoder_invocation'] = receipt
                    if args.expect_support_status:
                        result['expected_support_status'] = args.expect_support_status
                        result['support_status_matched'] = actual.get('support_status') == args.expect_support_status
                        # A negative support check never becomes a six-field accuracy pass.
                        if not args.require_six_fields:
                            result['ok'] = result['support_status_matched']
                            result['accuracy_certified'] = False
                    entry['results'].append(result)
            results = [x for r in report['recordings'] for x in r['results']]
            report['denominator'] = {'recordings': len(selected), 'observations': len(results),
                                     'required_player_fields': sum(r['required'] for r in results),
                                     'matched_player_fields': sum(r['matched'] for r in results)}
            report['ok'] = bool(selected) and not report['errors'] and all(r['ok'] for r in results)
            report['exit_code'] = 0 if report['ok'] else 1
            report['accuracy_certified'] = report['ok'] and bool(results) and not args.coverage_only and not args.expect_support_status
        snapshot.recheck()
        publish(args.output, report, inputs, snapshot=snapshot)
        return report['exit_code']
    except (ValueError, KeyError, TypeError, OSError, ReplayOutputError, subprocess.TimeoutExpired, ImportError) as error:
        print(json.dumps({'ok': False, 'code': 'schema_or_integrity_error', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
