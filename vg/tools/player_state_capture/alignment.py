from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import struct

from vg.core.vgr_records import iter_records
from .evidence import (digest, import_capture, inspect_native, metadata, native_float,
                       publish, read_json, ref_path, verify_capture)
from .guards import require


def stable_samples(native):
    sample = native['sample']
    require(any(r.get('tag') == 'rpc_ready' and r.get('result', {}).get('guards') == 5
                and r['result'].get('passive') is True for r in native['rows']),
            'boundary_unproved', 'Native replay read/apply guards are required for timed alignment')
    samples = [r['payload'] for r in native['rows']
               if r.get('payload', {}).get('tag') == 'player_state_sample']
    positions = [i for i, row in enumerate(samples) if row.get('sequence') == sample['sequence']]
    require(len(positions) == 1, 'boundary_unproved', 'Native sample sequence must be unique')
    index = positions[0]
    stable = lambda row: {k: v for k, v in row.items() if k not in {'sequence', 'utc_ms'}}
    for other in samples[max(0, index - 1):index] + samples[index + 1:index + 2]:
        if not all(type(row.get('sequence')) is int and type(row.get('utc_ms')) is int for row in (sample, other)):
            continue
        ordered = sorted((sample, other), key=lambda row: row['sequence'])
        if (ordered[1]['sequence'] == ordered[0]['sequence'] + 1
                and ordered[1]['utc_ms'] > ordered[0]['utc_ms']
                and stable(other) == stable(sample)):
            return [row['sequence'] for row in ordered]
    require(False, 'boundary_unproved', 'Two consecutive stable native samples are required')


def verify_injected_sections(capture, artifacts, base, injection, slot):
    sources = capture['source_files']
    injected = [r for r in artifacts.values() if r.get('role') == 'injected_section']
    expected = {f"{slot}.{r['section']}.vgr": r['sha256'] for r in sources}
    paths = [ref_path(base, r) for r in injected]
    require(len(paths) == len(expected) and {p.name for p in paths} == set(expected)
            and len({p.parent for p in paths}) == 1,
            'boundary_source_mismatch', 'Complete exact-slot injected section artifacts are required')
    require({p.name for p in paths[0].parent.glob('*.vgr')} == set(expected),
            'boundary_source_mismatch', 'Injected section archive contains extra or missing files')
    require(all(digest(path) == ref['sha256'] == expected[path.name] for path, ref in zip(paths, injected)),
            'boundary_source_mismatch', 'Archived injected bytes differ from the original recording')
    restored = [r for r in artifacts.values() if r.get('role') == 'slot_restored']
    require(len(restored) == 1, 'boundary_source_mismatch', 'Original substitution archive receipt is required')
    receipt = read_json(ref_path(base, restored[0]))
    require(receipt.get('trial') == capture.get('trial')
            and receipt.get('archived_substitution_frames') == len(sources),
            'boundary_source_mismatch', 'Restoration receipt does not identify the complete substitution archive')
    verification = injection['verification']
    require(all(verification.get(k) == len(sources) for k in ('source_frame_count', 'target_frame_count'))
            and all(verification.get(k) == 0 for k in ('source_min_frame', 'target_min_frame',
                                                     'hash_mismatch_count', 'size_mismatch_count'))
            and all(verification.get(k) == len(sources) - 1 for k in ('source_max_frame', 'target_max_frame'))
            and verification.get('missing_target_frames') == [] and verification.get('extra_target_frames') == [],
            'boundary_source_mismatch', 'Injection receipt must verify the entire original numbered series')


def reader_boundary(capture, native, artifacts, base):
    sample = native['sample']
    require(sample is not None, 'boundary_unproved', 'A whole-player native sample is required')
    reader = sample.get('replay_reader_before')
    require(isinstance(reader, dict) and reader.get('kind') == 'replay'
            and sample.get('replay_reader_unchanged') is True
            and reader == sample.get('replay_reader_after'),
            'boundary_unproved', 'Native replay reader changed during the sample or was not captured')
    pending = reader.get('needs_record') == 0
    require(pending or reader.get('needs_record') == 1, 'boundary_unproved', 'Invalid native buffered record state')
    native_float(reader['buffered_record_time'])
    sections = capture['source_files']
    maximum = max(r['section'] for r in sections)
    section = reader.get('section')
    exhausted = section == maximum + 1 and reader.get('file_open') is False
    paused = reader.get('mode') == 2 or (sample.get('game_clock_flags', 0) & 1) == 1
    require(pending or exhausted or paused, 'boundary_unproved', 'Native exhausted reader or pause is required')
    if section == maximum + 1:
        require(reader.get('file_open') is False, 'boundary_unproved', 'Past-final section still has an open reader')
        section = maximum
    require(type(section) is int and section in {r['section'] for r in sections},
            'boundary_unproved', 'Native section is outside the original recording')
    refs = [r for r in artifacts.values() if r.get('role') == 'injection']
    require(len(refs) == 1, 'boundary_unproved', 'Exact original injection receipt is required')
    injection = read_json(ref_path(base, refs[0]))
    require(injection.get('verification', {}).get('ok') is True
            and injection['verification'].get('verified_frame_count') == len(sections)
            and injection.get('live_replay', {}).get('oname') == reader.get('slot_name'),
            'boundary_source_mismatch', 'Native slot name and verified injection disagree')
    content = bytes.fromhex(reader['content_hex'])
    require(len(content) == reader.get('content_length') and len(content) >= 2,
            'boundary_unproved', 'Native buffered content length is invalid')
    ref = next(r for r in sections if r['section'] == section)
    path = ref_path(base, ref)
    require(digest(path) == ref['sha256'], 'hash_mismatch', 'Original section changed during alignment')
    data = path.read_bytes()
    records = tuple(iter_records(data))
    matches = [record for record in records
               if struct.unpack('>I', struct.pack('>f', record.timestamp))[0] == reader['buffered_record_time']['bits']
               and struct.pack('>H', record.opcode) + record.payload == content]
    require(len(matches) == 1, 'boundary_unproved', 'Native buffered bytes/time do not identify one original record')
    record = matches[0]
    extra = {}
    if pending:
        require(reader.get('mode') in (1, 2) and reader.get('file_open') is True and not exhausted
                and native_float(reader['playback_time'])['value'] < native_float(reader['buffered_record_time'])['value'],
                'boundary_unproved', 'Timed alignment requires a known replay mode with a strictly future pending record')
        stable_sequences = stable_samples(native)
        require([r['section'] for r in sections] == list(range(maximum + 1)),
                'boundary_source_mismatch', 'Timed alignment requires the complete contiguous source recording')
        scope = hashlib.sha256(b'vgr-numbered-series-v1\x00')
        previous = predecessor = None
        for source in sections:
            path = ref_path(base, source)
            raw = path.read_bytes()
            require(hashlib.sha256(raw).hexdigest() == source['sha256'], 'hash_mismatch', 'Original section changed')
            scope.update(struct.pack('>QQ', source['section'], len(raw)))
            scope.update(raw)
            for framed_record in iter_records(raw):
                if source['section'] == section and framed_record.offset == record.offset:
                    predecessor = previous
                previous = (source['section'], framed_record.offset)
        if 'source_scope' in injection:
            require(injection['source_scope'] == 'sha256:' + scope.hexdigest(),
                    'boundary_source_mismatch', 'Verified injection must identify the exact original source bytes')
        else:
            verify_injected_sections(capture, artifacts, base, injection, reader['slot_name'])
        require(predecessor is not None, 'boundary_unproved', 'Pending first record has no applied predecessor')
        extra = {'pending_record_boundary': {'section': section, 'record_offset': record.offset},
                 'stable_sample_sequences': stable_sequences}
        section, record_offset = predecessor
    else:
        require(section == maximum and record == records[-1], 'boundary_unproved',
                'Applied-buffer alignment only certifies native EOF')
        record_offset = record.offset
    return {'producer': 'client_native', 'method': 'native_reader_buffer',
            'pid': native['identity']['pid'], 'create_time': native['identity']['create_time'],
            'sample_sequence': sample['sequence'], 'native_log_sha256': artifacts[capture['native_artifact_id']]['sha256'],
            'loaded_source_files': [{'section': r['section'], 'sha256': r['sha256']} for r in sections],
            'record_boundary': {'section': section, 'record_offset': record_offset}, 'phase': 'after_apply',
            'native_paused': paused, 'native_recorded_end': not pending, 'native_reader_exhausted': exhausted,
            'game_clock_bits': sample['game_clock']['bits'], 'native_reader': reader,
            'basis': ('native strictly future pending-buffer predecessor and stable samples in original section framing'
                      if pending else 'native applied-buffer bytes plus exhausted reader or native pause and original section framing'),
            **extra}


def align_capture(capture_dir, output_dir, sequence):
    base, output = Path(capture_dir).resolve(), Path(output_dir).resolve()
    result = verify_capture(base)
    require(result['ok'], 'capture_invalid', 'Only a valid observation can be aligned')
    require(not output.exists(), 'output_exists', 'Aligned capture destination must be new')
    capture = deepcopy(read_json(base / 'capture.json'))
    capture['sample_sequence'] = sequence
    artifacts = {r['artifact_id']: r for r in capture['artifacts']}
    native = inspect_native(ref_path(base, artifacts[capture['native_artifact_id']]), sequence)
    proof = reader_boundary(capture, native, artifacts, base)
    staging = output.with_name(output.name + '-alignment')
    require(not staging.exists(), 'output_exists', 'Alignment proof staging directory must be new')
    staging.mkdir(parents=True, exist_ok=False)
    publish(staging / 'boundary.json', proof, [base / 'capture.json', *(r['path'] for r in capture['source_files'])])
    capture['artifacts'].append(metadata(staging / 'boundary.json', artifact_id='native-boundary', role='native_boundary'))
    capture['alignment'] = {'kind': 'recorded_end_native' if proof['native_recorded_end'] else 'stable_future_pending_buffer',
                            'artifact_id': 'native-boundary'}
    capture['capture_id'] += '-aligned'
    publish(staging / 'spec.json', capture, [base / 'capture.json', staging / 'boundary.json'])
    return import_capture(staging / 'spec.json', output)
