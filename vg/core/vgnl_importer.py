"""Offline VGNL v1 WebSocket *application payload* importer.

No WebSocket/TCP decoding, authentication, networking or result validation.
The strict adapter policy and static-client evidence limits are documented in
vg/docs/VGNL_OFFLINE_IMPORTER.md. Native timestamp bytes remain opaque.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Iterable
import uuid
import zlib


HEADER = struct.Struct('>4sBBH16sq4s4siqfiiI')
MAX_RECORD_BODY = 2_097_152
MAX_LONG = 2**63 - 1
REFERENCE_APK_SHA256 = '8394caa6f44b536924e8dd733870ee7642a04cc47abcb971ffcaadfe931a2543'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VGNLFormatError(ValueError):
    def __init__(self, code: str, message: str, offset: int = 0):
        self.code = code
        self.offset = offset
        super().__init__(message)


@dataclass(frozen=True)
class SourceInput:
    """Exact source bytes and a caller-supplied locator, never an identity claim."""
    data: bytes
    locator: str

    @classmethod
    def read(cls, path: str | Path) -> SourceInput:
        path = Path(path)
        return cls(path.read_bytes(), str(path.absolute()))


@dataclass(frozen=True)
class NativeRecord:
    offset: int
    timestamp: bytes
    body: bytes


@dataclass(frozen=True)
class Frame:
    version: int
    kind: int
    flags: int
    epoch: str
    sequence: int
    first_native_timestamp: bytes
    last_native_timestamp: bytes
    source_section: int
    source_offset: int
    game_clock: float
    record_count: int
    payload_crc32: int
    payload: bytes
    records: tuple[NativeRecord, ...]


def split_records(payload: bytes) -> tuple[NativeRecord, ...]:
    records = []
    offset = 0
    while offset < len(payload):
        if len(payload) - offset < 8:
            raise VGNLFormatError('partial_record_header', 'Native record header is truncated', offset)
        length = struct.unpack_from('>i', payload, offset + 4)[0]
        if not 0 <= length <= MAX_RECORD_BODY:
            raise VGNLFormatError('record_length', 'Native body length is outside producer bounds', offset + 4)
        end = offset + 8 + length
        if end > len(payload):
            raise VGNLFormatError('partial_record', 'Native record body is truncated', offset)
        records.append(NativeRecord(offset, payload[offset:offset + 4], payload[offset + 8:end]))
        offset = end
    return tuple(records)


def decode_frame(data: bytes) -> Frame:
    """Validate exactly one unmasked binary application payload, not a stream."""
    if len(data) < HEADER.size:
        raise VGNLFormatError('partial_header', 'VGNL header needs 68 bytes')
    (magic, version, kind, flags, epoch, sequence, first, last, section, offset,
     clock, count, size, crc) = HEADER.unpack_from(data)
    if magic != b'VGNL':
        raise VGNLFormatError('bad_magic', 'Expected VGNL application payload, not raw WebSocket/TCP bytes')
    if version != 1 or kind not in (1, 2):
        raise VGNLFormatError('unsupported_format', 'Only observed version 1, kinds 1 and 2 are supported', 4)
    if size < 0 or len(data) != HEADER.size + size:
        raise VGNLFormatError('payload_length', 'Declared payload length does not match exact input length', 60)
    payload = data[HEADER.size:]
    if zlib.crc32(payload) & 0xffffffff != crc:
        raise VGNLFormatError('crc32_mismatch', 'Payload CRC32 mismatch', 64)
    if sequence < 0 or section < 0 or offset < 0 or offset > MAX_LONG - size:
        raise VGNLFormatError('negative_or_overflowing_position', 'Invalid sequence, section or source byte boundary')
    if not math.isfinite(clock):
        raise VGNLFormatError('nonfinite_clock', 'Strict adapter requires a finite sampled game clock', 52)
    records = ()
    if kind == 2:
        if payload or count or section or offset or first != last:
            raise VGNLFormatError('end_shape', 'End frame must have zero payload/count/section/offset and equal timestamps')
        expected_flags = 4 if clock >= 0 else 0
    else:
        try:
            records = split_records(payload)
        except VGNLFormatError as exc:
            raise VGNLFormatError(exc.code, str(exc), HEADER.size + exc.offset) from exc
        if count != len(records) or not records:
            raise VGNLFormatError('record_count', 'Data frame must contain the declared nonzero complete record count', 56)
        if first != records[0].timestamp or last != records[-1].timestamp:
            raise VGNLFormatError('timestamp_bounds', 'Timestamp bytes differ from first/last native records', 32)
        expected_flags = (7 if section == 0 else 6) if offset == 0 else 4
    if flags != expected_flags:
        raise VGNLFormatError('unsupported_flags', 'Flags do not match the observed producer shape', 6)
    return Frame(version, kind, flags, str(uuid.UUID(bytes=epoch)), sequence,
                 first, last, section, offset, clock, count, crc, payload, records)


def logical_replay_id(value: str) -> str:
    """Java UTF-16 code-unit normalization only; identifies neither UUID."""
    units = value.encode('utf-16-be', errors='surrogatepass')
    if len(units) == 146 and units[72:74] == b'\x00-':
        return units[74:].decode('utf-16-be', errors='surrogatepass')
    return value


def _integer(value, name: str, maximum: int = MAX_LONG, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def _epoch(value) -> str:
    if not isinstance(value, str):
        raise ValueError('epoch must be a UUID string')
    return str(uuid.UUID(value))


def _json_object(source: SourceInput) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f'Invalid JSON constant: {value}')
    try:
        value = json.loads(source.data, object_pairs_hook=unique, parse_constant=reject_constant)
    except RecursionError as exc:
        raise ValueError('JSON nesting exceeds the supported parser depth') from exc
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value


@dataclass
class ImportResult:
    report: dict
    sources: tuple[SourceInput, ...]
    sections: dict[int, bytes] = field(default_factory=dict)

    def write(self, destination: str | Path) -> Path:
        """Write a new bundle exclusively. Never overwrite inputs or prior output.

        The manifest is written last; its absence indicates interrupted output.
        A failed write leaves only this new directory for inspection, never deletes
        or alters any pre-existing user file.
        """
        destination = Path(destination)
        encoded = json.dumps(self.report, ensure_ascii=True, indent=2, allow_nan=False) + '\n'
        destination.mkdir(parents=False, exist_ok=False)
        (destination / 'sources').mkdir()
        for index, source in enumerate(self.sources):
            (destination / 'sources' / f'{index:06d}.bin').write_bytes(source.data)
        if self.sections:
            (destination / 'replay').mkdir()
            for section, data in sorted(self.sections.items()):
                (destination / 'replay' / f'imported.{section}.vgr').write_bytes(data)
        (destination / 'manifest.json').write_text(encoded, encoding='utf-8')
        return destination / 'manifest.json'


def import_payloads(
    inputs: Iterable[SourceInput], *, replay_id: str,
    resume: SourceInput | None = None,
    terminal_scoreboards: Iterable[SourceInput] = (),
) -> ImportResult:
    """Import one externally labelled replay context and one transport epoch.

    Resume metadata describes claimed prior bytes, never supplies those bytes.
    Any error withholds all reconstructed VGR output; exact inputs are still
    retained. Duplicate and ordering diagnostics never silently discard provenance.
    """
    if not isinstance(replay_id, str) or not replay_id:
        raise ValueError('An explicit nonempty raw replay_id context is required')
    inputs = tuple(inputs)
    terminals = tuple(terminal_scoreboards)
    sources = inputs + ((resume,) if resume is not None else ()) + terminals
    report = {
        'schema_version': 'vg.vgnl-import.v1',
        'scope': 'offline_websocket_application_payloads',
        'replay_context': {'raw_replay_id': replay_id, 'source': 'caller_supplied_unverified',
                           'logical_replay_id': logical_replay_id(replay_id),
                           'normalization': 'java_utf16_length73_hyphen36_strip37_not_uuid_validation'},
        'contract_reference': {'apk_sha256': REFERENCE_APK_SHA256, 'client_version': '1.11',
                               'request_header_build': '113', 'basis': 'static_client_analysis_only'},
        'claims': {'recording_client': 'unverified', 'account_identity': 'unverified',
                   'server_authentication': 'unverified', 'server_acceptance': 'unverified',
                   'replay_completeness': 'unverified', 'authoritative_result': False,
                   'definitive_analysis_eligible': False,
                   'terminal_scoreboard_stats_available': False},
        'identity_scopes': {
            'epoch': 'transport/archive generation only',
            'platform_match_uuid': 'not supplied by binary frames; not inferred from epoch or replay_id',
            'player_uuid': 'not supplied by binary frames or terminal rows',
            'install_id': 'not supplied by binary frames or terminal rows',
            'entity_id': 'match-scoped native actor identifier; no account binding'},
        'sources': [], 'frames': [], 'issues': [], 'resume': None,
        'terminal_scoreboards': [], 'sections': [],
    }
    for index, source in enumerate(sources):
        kind = 'binary_payload' if index < len(inputs) else (
            'resume_metadata' if resume is not None and index == len(inputs) else 'terminal_scoreboard')
        report['sources'].append({'source_index': index, 'locator': source.locator,
                                  'kind': kind, 'size_bytes': len(source.data),
                                  'sha256': sha256(source.data), 'saved_as': f'sources/{index:06d}.bin'})

    def issue(code, *, severity='error', source_index=None, **detail):
        report['issues'].append({'code': code, 'severity': severity,
                                 'source_index': source_index, **detail})

    expected_epoch = None
    latest = -1
    resume_ends = {}
    prior_bytes_claimed = False
    if resume is not None:
        index = len(inputs)
        try:
            value = _json_object(resume)
            if set(value) != {'epoch', 'latest_sequence', 'segments'}:
                raise ValueError('Resume metadata requires exactly epoch, latest_sequence, segments')
            epoch = _epoch(value['epoch'])
            sequence = _integer(value['latest_sequence'], 'latest_sequence', MAX_LONG - 1, -1)
            if not isinstance(value['segments'], list):
                raise ValueError('segments must be an array')
            segments = []
            for segment in value['segments']:
                if not isinstance(segment, dict) or set(segment) != {'source_section', 'source_offset', 'length'}:
                    raise ValueError('Each resume segment requires section, offset and length only')
                section = _integer(segment['source_section'], 'source_section', 2**31 - 1)
                offset = _integer(segment['source_offset'], 'source_offset')
                length = _integer(segment['length'], 'length')
                if offset > MAX_LONG - length:
                    raise ValueError('Resume boundary overflows signed 64-bit range')
                segments.append((section, offset, length))
            expected_epoch, latest = epoch, sequence
            report['resume'] = {'source_index': index, 'epoch': epoch, 'latest_sequence': latest,
                                'segments': value['segments'], 'status': 'unverified_external_claims'}
            seen = set()
            for section, offset, length in sorted(segments):
                end = resume_ends.get(section, 0)
                if (section, offset, length) in seen:
                    issue('resume_duplicate_segment', severity='warning', source_index=index,
                          section=section, offset=offset, length=length)
                    continue
                if offset != end:
                    issue('resume_segment_overlap' if offset < end else 'resume_segment_gap',
                          source_index=index, section=section, expected_offset=end, actual_offset=offset)
                resume_ends[section] = max(end, offset + length)
                seen.add((section, offset, length))
                prior_bytes_claimed |= bool(length or offset)
            if latest >= 0:
                issue('resume_history_unavailable', severity='warning', source_index=index,
                      message='Earlier sequence history is claimed, not verified; VGR reconstruction is withheld')
            if prior_bytes_claimed:
                issue('resume_bytes_unavailable', severity='warning', source_index=index,
                      message='Claimed prior ranges have no supplied bytes; VGR reconstruction is withheld')
        except (ValueError, UnicodeError, KeyError) as exc:
            issue('invalid_resume', source_index=index, message=str(exc))

    decoded = []
    seen_sequences = {}
    for index, source in enumerate(inputs):
        item = {'source_index': index, 'validation': 'invalid'}
        report['frames'].append(item)
        try:
            frame = decode_frame(source.data)
        except VGNLFormatError as exc:
            issue(exc.code, source_index=index, input_byte_offset=exc.offset, message=str(exc))
            continue
        item.update({
            'validation': 'valid', 'transport_epoch': frame.epoch, 'transport_sequence': frame.sequence,
            'kind': frame.kind, 'flags': frame.flags, 'source_section': frame.source_section,
            'source_offset': frame.source_offset, 'payload_length': len(frame.payload),
            'payload_sha256': sha256(frame.payload), 'payload_crc32': f'{frame.payload_crc32:08x}',
            'crc32_verified': True, 'record_count': frame.record_count,
            'first_native_timestamp_hex': frame.first_native_timestamp.hex(),
            'last_native_timestamp_hex': frame.last_native_timestamp.hex(), 'game_clock': frame.game_clock,
            'game_clock_present': bool(frame.flags & 4),
            'records': [{'input_byte_offset': HEADER.size + record.offset,
                         'source_byte_offset': frame.source_offset + record.offset,
                         'timestamp_hex': record.timestamp.hex(), 'body_length': len(record.body),
                         'record_sha256': sha256(frame.payload[record.offset:record.offset + 8 + len(record.body)])}
                        for record in frame.records]})
        if expected_epoch is None:
            expected_epoch = frame.epoch
        if frame.epoch != expected_epoch:
            issue('epoch_mismatch', source_index=index, expected_epoch=expected_epoch, actual_epoch=frame.epoch)
            continue
        if frame.sequence in seen_sequences:
            previous = seen_sequences[frame.sequence]
            same = source.data == inputs[previous].data
            issue('duplicate_frame' if same else 'sequence_conflict', source_index=index,
                  severity='warning' if same else 'error', previous_source_index=previous, sequence=frame.sequence)
            continue
        seen_sequences[frame.sequence] = index
        decoded.append((frame, index))

    if not inputs:
        issue('no_binary_inputs')
    if [frame.sequence for frame, _ in decoded] != sorted(frame.sequence for frame, _ in decoded):
        issue('input_order_differs_from_sequence', severity='warning', message='Validated using sequence order; original input order retained')
    expected_sequence = latest + 1
    cursors = dict(resume_ends)
    chunks: dict[int, list[bytes]] = {}
    ranges = {}
    section_inputs: dict[int, list[int]] = {}
    end_seen = False
    last_timestamp = None
    highest_section = -1
    for frame, index in sorted(decoded, key=lambda pair: pair[0].sequence):
        if frame.sequence < expected_sequence:
            issue('resume_sequence_conflict', source_index=index, expected_sequence=expected_sequence, actual_sequence=frame.sequence)
        elif frame.sequence > expected_sequence:
            issue('sequence_gap', source_index=index, first_missing=expected_sequence, last_missing=frame.sequence - 1)
        expected_sequence = max(expected_sequence, frame.sequence + 1)
        if end_seen:
            issue('frame_after_end', source_index=index)
        if frame.kind == 2:
            if last_timestamp is not None and frame.last_native_timestamp != last_timestamp:
                issue('end_timestamp_conflict', source_index=index)
            end_seen = True
            continue
        section, offset, length = frame.source_section, frame.source_offset, len(frame.payload)
        key = (section, offset, length)
        if key in ranges:
            previous = ranges[key]
            same = frame.payload == previous[0]
            issue('duplicate_source_range' if same else 'source_range_conflict', source_index=index,
                  severity='warning' if same else 'error', previous_source_index=previous[1], section=section, offset=offset)
            continue
        ranges[key] = (frame.payload, index)
        if section < highest_section:
            issue('section_order_conflict', source_index=index, section=section, prior_section=highest_section)
        highest_section = max(highest_section, section)
        expected_offset = cursors.get(section, 0)
        if offset != expected_offset:
            code = 'source_offset_overlap' if offset < expected_offset else 'source_offset_gap'
            if section in resume_ends and offset < resume_ends[section]:
                code = 'resume_offset_conflict'
            issue(code, source_index=index, section=section, expected_offset=expected_offset, actual_offset=offset)
        cursors[section] = max(expected_offset, offset + length)
        chunks.setdefault(section, []).append(frame.payload)
        section_inputs.setdefault(section, []).append(index)
        last_timestamp = frame.last_native_timestamp

    next_section = 0
    for section in sorted(set(resume_ends) | set(chunks)):
        if section != next_section:
            issue('source_section_gap', first_missing=next_section, last_missing=section - 1)
        next_section = section + 1
    if not end_seen:
        issue('transport_end_not_observed', severity='warning')
    if not chunks:
        issue('no_data_records_observed', severity='warning')

    for number, source in enumerate(terminals):
        index = len(inputs) + (resume is not None) + number
        try:
            value = _json_object(source)
            if set(value) != {'type', 'epoch', 'source', 'players'}:
                raise ValueError('Only observed terminal_scoreboard fields are accepted')
            epoch = _epoch(value['epoch'])
            if value['type'] != 'terminal_scoreboard' or value['source'] != 'native_terminal_actor_model':
                raise ValueError('Unknown terminal scoreboard type or source')
            if epoch != expected_epoch:
                raise ValueError('Terminal scoreboard epoch does not match imported transport epoch')
            players = value['players']
            if not isinstance(players, list) or not 1 <= len(players) <= 16:
                raise ValueError('Terminal scoreboard must contain 1 to 16 rows')
            entities = set()
            for row in players:
                if not isinstance(row, dict) or set(row) != {'entity_id', 'hero'}:
                    raise ValueError('Terminal row contains only entity_id and hero, never K/D/A or account identity')
                entity = _integer(row['entity_id'], 'entity_id', 2**32 - 2, 1)
                hero = row['hero']
                if (not isinstance(hero, str) or not 1 <= len(hero) <= 64
                        or any(not 32 <= ord(char) <= 126 or char in '\\"' for char in hero)):
                    raise ValueError('Hero text is outside the observed printable ASCII bounds')
                if entity in entities:
                    raise ValueError('Duplicate terminal entity_id')
                entities.add(entity)
            report['terminal_scoreboards'].append({
                'source_index': index, 'transport_epoch': epoch, 'source': value['source'], 'players': players,
                'usage': 'entity_hero_corroboration_only_no_automatic_join',
                'snapshot_freshness': 'unverified_may_be_cached', 'hero_canonical_id': 'unverified'})
        except (ValueError, UnicodeError, KeyError) as exc:
            issue('invalid_terminal_scoreboard', source_index=index, message=str(exc))

    errors = any(item['severity'] == 'error' for item in report['issues'])
    reconstruct = not errors and not prior_bytes_claimed and latest == -1
    sections = {section: b''.join(parts) for section, parts in chunks.items()} if reconstruct else {}
    for section in sorted(chunks):
        data = sections.get(section)
        report['sections'].append({'source_section': section, 'source_indices': section_inputs[section],
                                   'reconstruction': 'contiguous_observed_bytes' if data is not None else 'withheld',
                                   'saved_as': f'replay/imported.{section}.vgr' if data is not None else None,
                                   'sha256': sha256(data) if data is not None else None,
                                   'size_bytes': len(data) if data is not None else None})
    report.update({'transport_epoch': expected_epoch, 'transport_end_observed': end_seen,
                   'status': 'issues' if errors else 'validated_observations',
                   'reconstruction': 'contiguous_observed_bytes' if sections else 'withheld',
                   'sequence_origin': 'resume_claim' if resume is not None else 'zero',
                   'crc_scope': 'payload_bytes_only_not_header_authentication'})
    return ImportResult(report, sources, sections)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('payloads', nargs='+', help='One complete binary WebSocket application payload per file, in capture order')
    parser.add_argument('--replay-id', required=True, help='Explicit raw replayId context, kept unverified')
    parser.add_argument('-o', '--output', required=True, help='New output directory; parent must exist')
    parser.add_argument('--resume', help='Offline JSON epoch/latest_sequence/segments claims; supplies no bytes')
    parser.add_argument('--terminal-scoreboard', action='append', default=[], help='Offline terminal_scoreboard JSON; repeatable')
    args = parser.parse_args(argv)
    try:
        result = import_payloads((SourceInput.read(path) for path in args.payloads), replay_id=args.replay_id,
                                 resume=SourceInput.read(args.resume) if args.resume else None,
                                 terminal_scoreboards=(SourceInput.read(path) for path in args.terminal_scoreboard))
        manifest = result.write(args.output)
    except (OSError, ValueError) as exc:
        print(f'VGNL import failed: {exc}', file=sys.stderr)
        return 2
    print(f"{result.report['status']}: {manifest}")
    return 1 if result.report['status'] == 'issues' else 0


if __name__ == '__main__':
    raise SystemExit(main())
