"""Validate fixed-build event claims and census strictly framed corpus records."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from vg.core.replay_output import ReportInputs, ReplayOutputError, write_report_output
from vg.core.vgr_records import VGRRecordError, iter_records

SOURCE = Path('vg/docs/vg-binary-event-candidates-2026-09-09.json')
REQUIRED_PLAYER_STATE = {
    '0x03ee', '0x03f2', '0x03f3', '0x041c', '0x041d', '0x043d', '0x0444',
    '0x044b', '0x046f',
}
READER_SOURCES = ('native_roster.py', 'native_stats.py', 'native_gold.py',
                  'native_inventory.py', 'native_query.py')
CAPABILITIES = {
    'catalog': {'identity', 'class_link'},
    'receiver': {'layout'},
    'emitter': {'layout'},
    'native_inventory': {'class_link'},
    'native_apply': {'layout', 'application'},
    'native_review': {'layout'},
    'native_layout': {'layout'},
    'native_consumer': {'layout'},
    'runtime_capture': {'runtime'},
    'corpus': {'shape'},
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def provenance():
    run = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return {'invocation': sys.argv, 'interpreter': sys.executable, 'python': sys.version,
            'commit': run.stdout.strip() if run.returncode == 0 else None}


def source_variant_keys(row):
    observed = (row.get('observed') or {}).get('payload_length_histogram', {})
    emitted = {r['payload_bytes'] for r in row.get('emitter_evidence', [])}
    return {('recorded', int(size)) for size in observed} | {('serialized', size) for size in emitted}


def summary(rows):
    return {'candidates': len(rows),
            'receiver': sum(r['dimensions']['receiver_handled'] for r in rows),
            'emitter': sum(r['dimensions']['emitter_found'] for r in rows),
            'observed': sum(r['dimensions']['observed_records'] > 0 for r in rows),
            'observed_records': sum(r['dimensions']['observed_records'] for r in rows),
            'recorded_variants': sum(v['domain'] == 'recorded' for r in rows for v in r['variants']),
            'serialized_variants': sum(v['domain'] == 'serialized' for r in rows for v in r['variants']),
            'multiple_recorded_variant_families': sum(sum(v['domain'] == 'recorded' for v in r['variants']) > 1 for r in rows),
            'semantic_status': dict(Counter(r['semantic_status'] for r in rows))}


def validate(atlas, source, docs, *, require_reviewed=False, require_player_state_semantics=False):
    """Reject inventory loss and claims stronger than their typed, hashed evidence."""
    issues = []
    def issue(code, opcode=None, **details):
        issues.append({'code': code, **({'opcode': opcode} if opcode else {}), **details})
    if atlas.get('schema_version') != 'event_semantics.v1':
        issue('schema_version')
    if atlas.get('executable_sha256') != source['executable_sha256']:
        issue('build_mismatch')
    policy = atlas.get('reader_policy', {})
    expected_sources = {name: sha(docs.parent / 'core' / name) for name in READER_SOURCES}
    if policy.get('source_sha256') != expected_sources:
        issue('reader_policy_source_drift')
    if set(policy.get('primary_opcodes', [])) != REQUIRED_PLAYER_STATE:
        issue('reader_policy_primary_drift')
    evidence = atlas['evidence']
    for key, ref in evidence.items():
        path = (docs / ref['path']).resolve()
        if not path.is_relative_to(docs.resolve()):
            issue('evidence_path_escape', evidence=key)
        elif not path.is_file():
            issue('evidence_missing', evidence=key, path=ref['path'])
        elif sha(path) != ref['sha256']:
            issue('evidence_hash_mismatch', evidence=key)
        if ref['kind'] not in CAPABILITIES:
            issue('evidence_kind', evidence=key)
    def refs_valid(refs, opcode, capability=None):
        missing = [ref for ref in refs if ref not in evidence]
        if missing:
            issue('orphaned_reference', opcode, references=missing)
        if capability and not any(capability in CAPABILITIES.get(evidence.get(ref, {}).get('kind'), set()) for ref in refs):
            issue('certainty_without_evidence', opcode, capability=capability, references=refs)
    candidates = {r['opcode']: r for r in source['candidates']}
    rows = atlas['events']
    ids = [r['opcode'] for r in rows]
    if len(ids) != len(set(ids)):
        issue('duplicate_candidate')
    if set(ids) != set(candidates):
        issue('candidate_union_mismatch', missing=sorted(set(candidates) - set(ids)), extra=sorted(set(ids) - set(candidates)))
    for row in rows:
        opcode = row['opcode']
        original = candidates.get(opcode)
        if original is None:
            continue
        observed = original.get('observed') or {}
        expected_dimensions = {'receiver_handled': original['receiver_handled'],
                               'emitter_found': bool(original['emitter_evidence']),
                               'observed_records': observed.get('record_count', 0),
                               'observed_recordings': observed.get('recording_count', 0)}
        if row['dimensions'] != expected_dimensions:
            issue('dimension_drift', opcode, expected=expected_dimensions, actual=row['dimensions'])
        expected_paths = {
            'receiver': original['receiver_target_va'],
            'constructors': sorted({a for link in original['native_links'] for a in link['path']}),
            'serializers': sorted({e['emitter'] for e in original['emitter_evidence']}),
            'apply_candidates': sorted({slot['target'] for link in original['native_links']
                                        for slot in link.get('slots', []) if slot['offset'] == 8}),
        }
        if row['paths'] != expected_paths:
            issue('native_path_drift', opcode)
        if bool(row['player_state_required']) != (opcode in REQUIRED_PLAYER_STATE):
            issue('required_semantics_policy', opcode)
        if row['direction']['status'] == 'runtime_verified':
            refs_valid(row['direction'].get('evidence', []), opcode, 'runtime')
        elif row['direction']['status'] != 'unproved':
            issue('direction_status', opcode)
        if row['native_copy_lengths'] != original['static_memmove_copy_bytes']:
            issue('native_copy_length_drift', opcode)
        refs_valid(row['evidence'], opcode)
        if row['name']['certainty'] == 'class_linked':
            if not (original['native_names'] or original['callbacks']) or row['name']['value'] not in [original['candidate'], *original['native_names'], *original['callbacks']]:
                issue('name_not_linked', opcode)
            refs_valid(row['name']['evidence'], opcode, 'class_link')
        variants = row['variants']
        keys = [(v['domain'], v['payload_bytes']) for v in variants]
        if len(keys) != len(set(keys)):
            issue('duplicate_variant', opcode)
        missing = source_variant_keys(original) - set(keys)
        if missing:
            issue('missing_variant', opcode, variants=sorted(missing))
        for variant in variants:
            key = (variant['domain'], variant['payload_bytes'])
            if key not in source_variant_keys(original):
                issue('unsubstantiated_variant', opcode, variant=key)
            if variant['domain'] == 'recorded' and variant['historical_samples'] != observed.get('payload_length_histogram', {}).get(str(variant['payload_bytes'])):
                issue('variant_count_drift', opcode, variant=key)
            layout = variant['layout']
            if layout['status'] not in ('unknown', 'partial', 'proven_prefix'):
                issue('layout_status', opcode, status=layout['status'])
            refs_valid(layout['evidence'], opcode, 'layout' if layout['status'] != 'unknown' else None)
            for field in layout['fields']:
                offset, width, count = field['offset'], field['width'], field.get('count', 1)
                stride = field.get('stride', width)
                if any(type(x) is not int or x < 0 for x in (offset, width, count, stride)) or not width or not count or offset + (count - 1) * stride + width > variant['payload_bytes']:
                    issue('field_outside_variant', opcode, field=field['name'], variant=key)
                if field['endian'] not in ('big', 'little', 'byte', 'utf8', 'opaque'):
                    issue('field_endian', opcode, field=field['name'])
                refs_valid(field['evidence'], opcode, 'layout')
            prefix = variant.get('native_prefix_application')
            if prefix is not None:
                copied = prefix['copied_bytes']
                if (type(copied) is not int or copied not in original['static_memmove_copy_bytes']
                        or copied >= variant['payload_bytes'] or not original['receiver_handled']):
                    issue('native_prefix_bounds', opcode, variant=key)
                if prefix['whole_variant_verified'] is not False or prefix['tail_status'] != 'opaque_unproved':
                    issue('native_prefix_overclaim', opcode, variant=key)
                if not prefix['effect']:
                    issue('missing_effect', opcode)
                refs_valid(prefix['evidence'], opcode, 'application')
            application = variant['application']
            framing = variant.get('framing_review')
            if framing is not None:
                if (framing.get('status') != 'direct_prefix_and_cursor_proven_only'
                        or not prefix or framing.get('native_copy_bytes') != prefix['copied_bytes']
                        or framing.get('opaque_suffix_bytes') != variant['payload_bytes'] - prefix['copied_bytes']
                        or application['status'] != 'unknown'):
                    issue('framing_scope_overclaim', opcode, variant=key)
                if any(not framing.get(name) for name in ('finding', 'remaining_unknown', 'minimal_experiment')):
                    issue('framing_missing_limit', opcode, variant=key)
                refs_valid(framing.get('evidence', []), opcode, 'application')
            field_application = variant.get('required_field_application')
            if field_application is not None:
                supported = {('0x03ee', 222), ('0x03f2', 126), ('0x041c', 22), ('0x041d', 14)}
                if (variant['domain'] != 'recorded' or (opcode, variant['payload_bytes']) not in supported
                        or not framing or not prefix
                        or field_application.get('status') != 'static_proven'
                        or field_application.get('mode') != 'fixed_build_replay'
                        or set(field_application.get('fields', [])) != set(row['player_state_required'])
                        or field_application.get('whole_event_semantics_verified') is not False):
                    issue('required_field_scope_overclaim', opcode, variant=key)
                proof = field_application.get('evidence', [])
                required_refs = {'atlas:004eb2d0', 'atlas:004676f0', 'atlas:004eb220', 'atlas:replay-vtable',
                                 'atlas:004ca130', 'atlas:004cfec0', 'atlas:009546f0'}
                if not required_refs.issubset(proof) or not field_application.get('suffix_effect') or not field_application.get('guards'):
                    issue('required_field_proof_incomplete', opcode, variant=key)
                refs_valid(proof, opcode, 'application')
            if application['status'] not in ('unknown', 'static_proven', 'runtime_matched'):
                issue('application_status', opcode)
            refs_valid(application['evidence'], opcode, 'application' if application['status'] != 'unknown' else None)
            if application['status'] == 'runtime_matched':
                refs_valid(application['evidence'], opcode, 'runtime')
                scope = {'opcode': opcode, 'domain': variant['domain'], 'payload_bytes': variant['payload_bytes']}
                if not any(scope in evidence.get(ref, {}).get('verified_variants', []) for ref in application['evidence']):
                    issue('runtime_variant_unmatched', opcode, variant=scope)
            if application['status'] != 'unknown' and not application['effect']:
                issue('missing_effect', opcode)
            if layout['status'] == 'unknown' and (layout['fields'] or application['status'] != 'unknown'):
                issue('certainty_without_evidence', opcode, reason='unknown layout carries interpreted fields/application')
        derived_status = ('applied_static' if any(v['application']['status'] != 'unknown' for v in variants)
                          else 'layout_only' if any(v['layout']['status'] != 'unknown' for v in variants)
                          else 'class_only' if row['name']['certainty'] == 'class_linked' else 'unknown')
        if row['semantic_status'] != derived_status:
            issue('semantic_status', opcode, expected=derived_status)
        if row['semantic_status'] == 'applied_static' and not any(v['application']['status'] != 'unknown' for v in variants):
            issue('certainty_without_evidence', opcode, reason='applied status without an applied variant')
        if not row['uncertainty'] or any(not item.get('statement') or not item.get('falsifier') or not item.get('next_step') for item in row['uncertainty']):
            issue('missing_falsifier', opcode)
        for label in row.get('native_labels', []):
            refs_valid(label['evidence'], opcode, 'layout')
        for observation in row.get('final_field_observations', []):
            if observation.get('status') != 'matched_final_snapshot' or not observation.get('scope'):
                issue('final_field_observation_scope', opcode)
            refs_valid(observation.get('evidence', []), opcode, 'runtime')
        if require_reviewed:
            review = row['review']
            if review['status'] not in ('bounded_unknown', 'scoped_proof'):
                issue('not_reviewed', opcode)
            if review['static']['status'] != 'inspected' or not review['static']['finding']:
                issue('missing_static_review', opcode)
            refs_valid(review['static']['evidence'], opcode)
            for stage in ('passive', 'controlled'):
                if not review[stage]['status'] or not review[stage]['finding']:
                    issue('missing_research_stage', opcode, stage=stage)
        if require_player_state_semantics and row['player_state_required']:
            for variant in variants:
                if variant['domain'] == 'recorded' and (variant['layout']['status'] == 'unknown' or
                        (variant['application']['status'] == 'unknown' and not variant.get('required_field_application'))):
                    issue('required_semantics_unknown', opcode, variant=(variant['domain'], variant['payload_bytes']))
            if row['player_state_gate']['status'] != 'verified':
                issue('player_state_gate_pending', opcode, reason=row['player_state_gate']['reason'])
            else:
                refs_valid(row['player_state_gate']['evidence'], opcode, 'runtime')
    counts = summary(rows)
    if atlas.get('summary') != counts:
        issue('summary_drift', actual=counts)
    return {'ok': not issues, 'issues': issues, 'summary': counts,
            'validation_mode': 'per_opcode_runtime_controls' if require_player_state_semantics else 'bounded_evidence_inventory',
            'six_field_accuracy_certified': False,
            'all_meanings_decoded': False,
            'scope': 'Evidence and bounded semantics inventory. Unknowns remain; structural or static proof does not certify six-field runtime accuracy.'}


def audit_corpus(manifest, manifest_path, atlas, source, docs):
    """Count opcode/length only; never decode player values or tune on holdouts."""
    prior_path = docs / 'evidence/2026-09-09-binary-events/corpus/provenance.json'
    prior = read_json(prior_path)
    expected = {r['corpus']: r for r in prior['rows']}
    rows = manifest['recordings']
    present = [r['recording_id'] for r in rows if r['recording_id'] in expected]
    issues = []
    if len(present) != len(set(present)):
        issues.append({'code': 'duplicate_recording'})
    if set(present) != set(expected):
        issues.append({'code': 'missing_recording', 'recordings': sorted(set(expected) - set(present))})
    global_counts = defaultdict(Counter)
    recording_counts = defaultdict(dict)
    exemplars = {}
    recordings, source_checks, input_paths = [], [], []
    for row in rows:
        identity = row['recording_id']
        if identity not in expected:
            continue
        counts = defaultdict(Counter)
        files = row['source_files']
        sections = [s['section'] for s in files]
        previous = {s['number']: s for s in expected[identity]['sections']}
        if len(sections) != len(set(sections)) or set(sections) != set(previous):
            issues.append({'code': 'section_inventory_mismatch', 'recording_id': identity})
        section_records = []
        for ref in sorted(files, key=lambda f: f['section']):
            path = (manifest_path.parent / ref['path']).resolve()
            input_paths.append(path)
            if not path.is_file():
                issues.append({'code': 'source_missing', 'recording_id': identity, 'section': ref['section']})
                continue
            data = path.read_bytes()
            actual_hash = hashlib.sha256(data).hexdigest()
            check = {'recording_id': identity, 'section': ref['section'], 'sha256': actual_hash,
                     'manifest_match': actual_hash == ref['sha256'],
                     'historical_match': actual_hash == previous.get(ref['section'], {}).get('sha256')}
            source_checks.append(check)
            if not check['historical_match']:
                issues.append({'code': 'historical_source_hash_mismatch', **check})
            if not check['manifest_match']:
                issues.append({'code': 'source_hash_mismatch', **check})
                continue
            total = 0
            try:
                for record in iter_records(data):
                    opcode, size = f'0x{record.opcode:04x}', len(record.payload)
                    counts[opcode][size] += 1
                    total += 1
                    key = f'{opcode}:{size}'
                    if key not in exemplars:
                        exemplars[key] = {'recording_id': identity, 'section': ref['section'],
                                          'record_offset': record.offset, 'record_timestamp': record.timestamp,
                                          'section_sha256': actual_hash}
            except VGRRecordError as error:
                issues.append({'code': 'malformed_records', 'recording_id': identity, 'section': ref['section'], 'reason': str(error)})
            section_records.append({'section': ref['section'], 'records': total})
        total = sum(sum(c.values()) for c in counts.values())
        recordings.append({'recording_id': identity, 'partition': row.get('partition'), 'sections': len(section_records),
                           'records': total, 'historical_records': expected[identity]['record_count'],
                           'record_count_delta': total - expected[identity]['record_count'], 'section_records': section_records})
        for opcode, count in counts.items():
            global_counts[opcode].update(count)
            recording_counts[opcode][identity] = sum(count.values())
    candidates = {r['opcode']: r for r in source['candidates']}
    variants = {r['opcode']: {v['payload_bytes'] for v in r['variants'] if v['domain'] == 'recorded'} for r in atlas['events']}
    observations, drift = [], []
    for opcode, counts in sorted(global_counts.items()):
        old = candidates.get(opcode, {}).get('observed') or {}
        observed = {'opcode': opcode, 'records': sum(counts.values()), 'recordings': len(recording_counts[opcode]),
                    'payload_length_histogram': {str(k): v for k, v in sorted(counts.items())},
                    'recording_counts': recording_counts[opcode]}
        observations.append(observed)
        if opcode not in candidates:
            issues.append({'code': 'uncatalogued_opcode', 'opcode': opcode})
        missing = set(counts) - variants.get(opcode, set())
        if missing:
            issues.append({'code': 'uncatalogued_variant', 'opcode': opcode, 'payload_lengths': sorted(missing)})
        if observed['payload_length_histogram'] != old.get('payload_length_histogram', {}) or observed['recording_counts'] != old.get('recording_counts', {}):
            drift.append({'opcode': opcode, 'prior_records': old.get('record_count', 0), 'actual_records': observed['records'],
                          'prior_payload_lengths': old.get('payload_length_histogram', {}), 'actual_payload_lengths': observed['payload_length_histogram']})
    for opcode, candidate in candidates.items():
        if candidate.get('observed') and opcode not in global_counts:
            drift.append({'opcode': opcode, 'prior_records': candidate['observed']['record_count'], 'actual_records': 0})
    hashes_match = all(r['manifest_match'] and r['historical_match'] for r in source_checks)
    if drift:
        issues.append({'code': 'corpus_drift', 'reason': 'source hashes unchanged; counting implementation or corruption must be resolved' if hashes_match else 'source set/hash differences; see per-section receipts', 'opcodes': len(drift)})
    return {'ok': not issues, 'issues': issues, 'recordings': recordings,
            'summary': {'recordings': len(recordings), 'sections': len(source_checks),
                        'records': sum(r['records'] for r in recordings), 'observed_opcodes': len(global_counts),
                        'recorded_variants': sum(len(x) for x in global_counts.values()),
                        'historical_records': prior['record_count'], 'all_historical_hashes_match': hashes_match},
            'excluded_non_corpus_controls': [r['recording_id'] for r in rows if r['recording_id'] not in expected],
            'observations': observations, 'first_exemplars': exemplars, 'source_checks': source_checks, 'drift': drift,
            'scope': 'All fixed-corpus strict frame opcodes and lengths only; no player-state values interpreted, including holdouts.'}, input_paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'audit-corpus'):
        child = sub.add_parser(name)
        child.add_argument('--atlas', type=Path, required=True)
        child.add_argument('--source', type=Path, default=SOURCE)
        child.add_argument('--output', type=Path, required=True)
        if name == 'validate':
            child.add_argument('--require-reviewed', action='store_true')
            child.add_argument('--require-per-opcode-runtime-controls', '--require-player-state-semantics',
                               dest='require_player_state_semantics', action='store_true',
                               help='Require every primary opcode control gate; legacy alias retained. '
                                    'This strict research audit is separate from exact six-field reference comparison.')
        else:
            child.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        atlas, source = read_json(args.atlas), read_json(args.source)
        docs = args.source.parent
        sources = [args.atlas, args.source, *[(docs / r['path']).resolve() for r in atlas['evidence'].values()]]
        if sha(args.source) != atlas['source_catalog_sha256']:
            raise ValueError('source catalog hash changed')
        inputs = ReportInputs(files=sources)
        report = validate(atlas, source, docs,
                          require_reviewed=getattr(args, 'require_reviewed', False),
                          require_player_state_semantics=getattr(args, 'require_player_state_semantics', False))
        if args.command == 'audit-corpus' and report['ok']:
            sources.append(args.manifest)
            manifest = read_json(args.manifest)
            sources.extend((args.manifest.parent / ref['path']).resolve()
                           for row in manifest['recordings'] for ref in row['source_files'])
            inputs.recheck()
            inputs = ReportInputs(files=[p for p in sources if p.exists()], reserved_files=sources)
            report, _ = audit_corpus(manifest, args.manifest, atlas, source, docs)
            inputs.recheck()
        report['provenance'] = provenance()
        report['atlas_sha256'] = sha(args.atlas)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_report_output(inputs, args.output, json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'ok': report['ok'], 'summary': report['summary'], 'issues': len(report['issues']), 'output': str(args.output)}))
        return 0 if report['ok'] else 1
    except (OSError, ValueError, KeyError, TypeError, ReplayOutputError) as error:
        print(json.dumps({'ok': False, 'code': 'integrity_or_schema_error', 'reason': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
