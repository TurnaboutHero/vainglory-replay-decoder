"""Audit existing raw 041d decoding with source hashes; never reconstruct effects."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from vg.analysis.native_event_fields import decode_fields
from vg.core.replay_input import replay_sections, select_replay
from vg.core.replay_output import ReportInputs, write_report_output
from vg.core.vgr_records import iter_records


def audit(replay_file, *, witness_limit=16):
    """Read every framed record, retaining the first witness per index/mode/sign.

    Timestamp is outer replay-record time, not an observed game clock. Neither
    a received operand nor a same-actor opposite operand identifies a temporary
    resource instance, callback, accepted amount or reset of that instance.
    """
    if type(witness_limit) is not int or not 1 <= witness_limit <= 64:
        raise ValueError('witness_limit must be an integer from 1 to 64')
    replay = select_replay(replay_file)
    sections = replay_sections(replay)
    inputs = ReportInputs(files=tuple(p for _, p in sections), replays=(replay,))
    identities = {i.path: i.digest for i in inputs.identities if i is not None}
    sources, witnesses = [], {}
    layouts, counts = Counter(), Counter()
    record_count = 0
    for number, path in sections:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if identities.get(path) != digest:
            raise ValueError('Replay bytes changed after preflight')
        section_records = 0
        for record in iter_records(data):
            record_count += 1
            section_records += 1
            if record.opcode != 0x041d:
                continue
            fields = decode_fields(record)
            layouts[(record.content_length, fields['decoding_status'])] += 1
            if fields['decoding_status'] != 'decoded':
                continue
            index = fields['native_index']
            if index not in (4, 5):
                continue
            value = fields['value']
            sign = ('nonfinite' if value is None else 'positive' if value > 0
                    else 'negative' if value < 0 else 'zero')
            operation = fields['native_operation']
            counts[(index, record.payload[9], operation, sign)] += 1
            key = (index, operation, sign)
            if key not in witnesses:
                witnesses[key] = {
                    'section': number, 'section_sha256': digest,
                    'record_offset': record.offset, 'record_time': record.timestamp,
                    'record_sha256': hashlib.sha256(
                        data[record.offset:record.offset + 8 + record.content_length]).hexdigest(),
                    'actor_ref_raw': fields['ref0'], 'actor_bytes_be': record.payload[:4].hex(),
                    'resource_index_raw': index, 'operand': value,
                    'operand_bits': fields['value_bits'], 'operand_bytes_be': record.payload[4:8].hex(),
                    'operation': operation, 'operation_byte_raw': record.payload[9],
                    'flags_raw': fields['native_flags'], 'opaque_suffix_hex': record.payload[12:].hex(),
                    'source_actor': None, 'temporary_resource_instance': None,
                    'cause': None, 'effect_status': 'unverified',
                }
        sources.append({'section': number, 'sha256': digest,
                        'bytes': len(data), 'records': section_records})
    if replay_sections(replay) != sections:
        raise ValueError('Replay section set changed after preflight')
    inputs.recheck()
    return {
        'schema': 'vg.resource-wire-observations.v1',
        'scope': 'raw_041d_operands_only', 'recording_build_status': 'unverified',
        'decoder': 'vg.analysis.native_event_fields.decode_fields',
        'time_basis': 'outer_record_timestamp; no game-time projection',
        'framing': 'complete iter_records traversal; no byte signature scan',
        'record_count': record_count, 'sources': sources,
        'resource_layouts': [{'content_length': length, 'decoding_status': status, 'count': count}
                             for (length, status), count in sorted(layouts.items())],
        'counts': [{'resource_index_raw': index, 'operation_byte_raw': mode,
                    'operation': operation, 'operand_sign': sign, 'count': count}
                   for (index, mode, operation, sign), count in sorted(counts.items())],
        'witness_policy': 'first record per resource index / ADD-or-SET / operand sign',
        'witness_classes': len(witnesses), 'witnesses': list(witnesses.values())[:witness_limit],
        'limitations': ['No barrier/fortified-health name or accumulated state is assigned.',
                        'No buff instance, source actor, reason, callback or accepted effect is inferred.',
                        'ADD and SET are wire operations; a SET is not a proved instance reset.',
                        'Zero observations do not prove the resource or producer is unused.'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay', type=Path, help='existing frame-zero replay or unambiguous directory')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--witness-limit', type=int, default=16)
    args = parser.parse_args(argv)
    # Protect output publication with the same source snapshot used before audit.
    replay = select_replay(args.replay)
    inputs = ReportInputs(replays=(replay,))
    result = audit(replay, witness_limit=args.witness_limit)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    inputs.recheck()
    if args.output:
        write_report_output(inputs, args.output, text)
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
