from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import struct

from vg.core.vgr_records import iter_records
from .evidence import (digest, import_capture, inspect_native, metadata, native_float,
                       publish, read_json, ref_path, verify_capture)
from .guards import require


def reader_boundary(capture, native, artifacts, base):
    sample = native['sample']
    require(sample is not None, 'boundary_unproved', 'A whole-player native sample is required')
    reader = sample.get('replay_reader_before')
    require(isinstance(reader, dict) and reader.get('kind') == 'replay'
            and sample.get('replay_reader_unchanged') is True
            and reader == sample.get('replay_reader_after'),
            'boundary_unproved', 'Native replay reader changed during the sample or was not captured')
    require(reader.get('needs_record') == 1, 'boundary_unproved', 'Buffered record has not been confirmed applied')
    native_float(reader['buffered_record_time'])
    sections = capture['source_files']
    maximum = max(r['section'] for r in sections)
    section = reader.get('section')
    exhausted = section == maximum + 1 and reader.get('file_open') is False
    paused = reader.get('mode') == 2 or (sample.get('game_clock_flags', 0) & 1) == 1
    require(exhausted or paused, 'boundary_unproved', 'Native exhausted reader or pause is required')
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
    originals = [ref_path(base, r) for r in sections]
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
    require(section == maximum and record == records[-1], 'boundary_unproved',
            'This exporter only certifies native EOF; timed reader alignment is not implemented')
    return {'producer': 'client_native', 'method': 'native_reader_buffer',
            'pid': native['identity']['pid'], 'create_time': native['identity']['create_time'],
            'sample_sequence': sample['sequence'], 'native_log_sha256': artifacts[capture['native_artifact_id']]['sha256'],
            'loaded_source_files': [{'section': r['section'], 'sha256': r['sha256']} for r in sections],
            'record_boundary': {'section': section, 'record_offset': record.offset}, 'phase': 'after_apply',
            'native_paused': paused, 'native_recorded_end': True, 'native_reader_exhausted': exhausted,
            'game_clock_bits': sample['game_clock']['bits'], 'native_reader': reader,
            'basis': 'native applied-buffer bytes plus exhausted reader or native pause and original section framing'}


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
    capture['alignment'] = {'kind': 'recorded_end_native', 'artifact_id': 'native-boundary'}
    capture['capture_id'] += '-aligned'
    publish(staging / 'spec.json', capture, [base / 'capture.json', staging / 'boundary.json'])
    return import_capture(staging / 'spec.json', output)
