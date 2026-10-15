"""Synthetic transport tests; these are not captured VGNL/server fixtures."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import uuid
import zlib

from vg.core.vgnl_importer import (
    HEADER, MAX_RECORD_BODY, SourceInput, VGNLFormatError, decode_frame,
    import_payloads, logical_replay_id, split_records,
)

EPOCH = '00000000-0000-4000-8000-000000000001'
OTHER = '00000000-0000-4000-8000-000000000002'
ROOT = Path(__file__).resolve().parents[1]


def record(body=b'\x03\xf1test', timestamp=b'\x01\x02\x03\x04'):
    return timestamp + struct.pack('>i', len(body)) + body


def frame(payload=None, sequence=0, section=0, offset=0, epoch=EPOCH, kind=1, **changes):
    if payload is None:
        payload = record() if kind == 1 else b''
    records = split_records(payload) if kind == 1 and not changes.get('count') else ()
    fields = dict(magic=b'VGNL', version=1, kind=kind,
                  flags=((7 if section == 0 else 6) if offset == 0 else 4) if kind == 1 else 4,
                  epoch=uuid.UUID(epoch).bytes, sequence=sequence,
                  first=records[0].timestamp if records else b'\x01\x02\x03\x04',
                  last=records[-1].timestamp if records else b'\x01\x02\x03\x04',
                  section=section, offset=offset, clock=1.25,
                  count=len(records), size=len(payload), crc=zlib.crc32(payload) & 0xffffffff)
    fields.update(changes)
    return HEADER.pack(*fields.values()) + payload


def source(data, locator='fixture:synthetic'):
    return SourceInput(data, locator)


def metadata(value):
    return source(json.dumps(value).encode(), 'fixture:synthetic-json')


def resume(latest=0, segments=None, epoch=EPOCH):
    return metadata({'epoch': epoch, 'latest_sequence': latest, 'segments': segments or []})


def segment(offset=0, length=14, section=0):
    return {'source_section': section, 'source_offset': offset, 'length': length}


def terminal(**changes):
    value = dict(type='terminal_scoreboard', epoch=EPOCH, source='native_terminal_actor_model',
                 players=[{'entity_id': 7, 'hero': 'Ringo'}])
    value.update(changes)
    return metadata(value)


def imported(*data, **kwargs):
    return import_payloads([source(item, f'fixture:{index}') for index, item in enumerate(data)],
                           replay_id='raw-replay-context', **kwargs)


def codes(result):
    return {issue['code'] for issue in result.report['issues']}


class FrameTests(unittest.TestCase):
    def assert_invalid(self, data, code):
        with self.assertRaises(VGNLFormatError) as caught:
            decode_frame(data)
        self.assertEqual(caught.exception.code, code)

    def test_header_offsets_raw_timestamp_and_crc(self):
        data = frame()
        parsed = decode_frame(data)
        self.assertEqual(HEADER.size, 68)
        self.assertEqual(data[:8], b'VGNL\x01\x01\x00\x07')
        self.assertEqual(data[8:24], uuid.UUID(EPOCH).bytes)
        self.assertEqual(struct.unpack_from('>f', data, 52)[0], 1.25)
        self.assertEqual(parsed.payload, record())
        self.assertEqual(parsed.first_native_timestamp, b'\x01\x02\x03\x04')
        self.assertEqual(parsed.records[0].body, b'\x03\xf1test')

    def test_all_truncations_and_trailing_bytes(self):
        data = frame()
        for length in range(len(data)):
            with self.subTest(length=length), self.assertRaises(VGNLFormatError):
                decode_frame(data[:length])
        self.assert_invalid(data + b'\0', 'payload_length')
        self.assert_invalid(data + data, 'payload_length')

    def test_magic_version_kind(self):
        for changes, code in (({'magic': b'junk'}, 'bad_magic'), ({'version': 2}, 'unsupported_format'),
                              ({'kind': 3}, 'unsupported_format')):
            self.assert_invalid(frame(**changes), code)

    def test_crc_corruption_and_negative_declared_length(self):
        data = bytearray(frame())
        data[-1] ^= 1
        self.assert_invalid(bytes(data), 'crc32_mismatch')
        self.assert_invalid(frame(size=-1), 'payload_length')

    def test_strict_flags_bounds_clock_count_and_timestamps(self):
        cases = [({'flags': 0}, 'unsupported_flags'), ({'flags': 15}, 'unsupported_flags'),
                 ({'sequence': -1}, 'negative_or_overflowing_position'),
                 ({'section': -1}, 'negative_or_overflowing_position'),
                 ({'offset': -1}, 'negative_or_overflowing_position'),
                 ({'offset': 2**63 - 1}, 'negative_or_overflowing_position'),
                 ({'clock': float('nan')}, 'nonfinite_clock'),
                 ({'clock': float('inf')}, 'nonfinite_clock'),
                 ({'count': -1}, 'record_count'), ({'count': 2}, 'record_count'),
                 ({'first': b'abcd'}, 'timestamp_bounds'), ({'last': b'abcd'}, 'timestamp_bounds')]
        for changes, code in cases:
            with self.subTest(changes=changes):
                self.assert_invalid(frame(**changes), code)
        self.assert_invalid(frame(payload=b''), 'record_count')

    def test_complete_record_bounds_including_zero_length(self):
        self.assertEqual(decode_frame(frame(record(b''))).record_count, 1)
        self.assertEqual(len(split_records(record(b'x' * MAX_RECORD_BODY))[0].body), MAX_RECORD_BODY)
        bad = [b'\0' * 7, b'abcd' + struct.pack('>i', -1),
               b'abcd' + struct.pack('>i', MAX_RECORD_BODY + 1), b'abcd' + struct.pack('>i', 2) + b'x']
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(VGNLFormatError):
                decode_frame(frame(payload, count=1))

    def test_end_shape(self):
        self.assertEqual(decode_frame(frame(kind=2)).kind, 2)
        self.assertEqual(decode_frame(frame(kind=2, clock=-1, flags=0)).flags, 0)
        for changes in ({'first': b'abcd'}, {'count': 1}, {'section': 1}, {'offset': 1}, {'payload': b'x'}):
            self.assert_invalid(frame(kind=2, **changes), 'end_shape')

    def test_normalization_does_not_validate_uuid_or_assign_player(self):
        self.assertEqual(logical_replay_id('x' * 36 + '-' + 'y' * 36), 'y' * 36)
        self.assertEqual(logical_replay_id(EPOCH), EPOCH)
        self.assertEqual(logical_replay_id('😀' * 18 + '-' + 'y' * 36), 'y' * 36)
        raw = '😀' * 36 + '-' + 'y' * 36
        self.assertEqual(logical_replay_id(raw), raw)


class ImportTests(unittest.TestCase):
    def test_contiguous_reconstruction_preserves_provenance_and_no_promotion(self):
        a, b = record(), record(b'body', b'efgh')
        result = imported(frame(a), frame(b, 1, offset=len(a)), frame(kind=2, sequence=2, first=b'efgh', last=b'efgh'))
        self.assertEqual(result.sections, {0: a + b})
        self.assertEqual(result.report['status'], 'validated_observations')
        self.assertTrue(result.report['transport_end_observed'])
        self.assertEqual(result.report['claims']['replay_completeness'], 'unverified')
        self.assertFalse(result.report['claims']['definitive_analysis_eligible'])
        self.assertFalse(result.report['claims']['authoritative_result'])
        self.assertEqual(result.report['frames'][1]['records'][0]['source_byte_offset'], len(a))
        self.assertEqual(result.report['frames'][1]['records'][0]['input_byte_offset'], 68)
        self.assertEqual(result.report['sources'][0]['sha256'], hashlib.sha256(frame(a)).hexdigest())
        self.assertEqual(result.report['sources'][0]['locator'], 'fixture:0')

    def test_multiple_sections_and_missing_end_are_observed_prefix_only(self):
        result = imported(frame(), frame(section=1, sequence=1))
        self.assertEqual(result.sections, {0: record(), 1: record()})
        self.assertIn('transport_end_not_observed', codes(result))
        self.assertEqual(result.report['reconstruction'], 'contiguous_observed_bytes')

    def test_sequence_duplicate_and_conflict(self):
        same = imported(frame(), frame())
        self.assertIn('duplicate_frame', codes(same))
        self.assertEqual(same.sections, {0: record()})
        self.assertEqual(len(same.report['sources']), 2)
        conflict = imported(frame(), frame(record(b'other')))
        self.assertIn('sequence_conflict', codes(conflict))
        self.assertFalse(conflict.sections)

    def test_duplicate_source_range_and_conflict(self):
        same = imported(frame(), frame(sequence=1))
        self.assertIn('duplicate_source_range', codes(same))
        self.assertEqual(same.sections, {0: record()})
        conflict = imported(frame(), frame(record(b'\x03\xf1xxxx'), sequence=1))
        self.assertIn('source_range_conflict', codes(conflict))
        self.assertFalse(conflict.sections)

    def test_gaps_overlap_and_section_order_never_fill_or_concatenate(self):
        cases = [([frame(sequence=1)], 'sequence_gap'),
                 ([frame(offset=3)], 'source_offset_gap'),
                 ([frame(section=2)], 'source_section_gap'),
                 ([frame(), frame(offset=1, sequence=1)], 'source_offset_overlap'),
                 ([frame(), frame(section=1, sequence=1), frame(offset=14, sequence=2)], 'section_order_conflict')]
        for frames, code in cases:
            with self.subTest(code=code):
                result = imported(*frames)
                self.assertIn(code, codes(result))
                self.assertFalse(result.sections)

    def test_huge_gaps_are_reported_as_ranges(self):
        result = imported(frame(sequence=2**63 - 1, section=2**31 - 1))
        self.assertEqual(len([i for i in result.report['issues'] if i['code'] == 'sequence_gap']), 1)
        self.assertFalse(result.sections)

    def test_explicit_reordering_retains_input_order(self):
        result = imported(frame(sequence=1, offset=14), frame())
        self.assertIn('input_order_differs_from_sequence', codes(result))
        self.assertEqual(result.sections, {0: record() * 2})
        self.assertEqual([item['transport_sequence'] for item in result.report['frames']], [1, 0])

    def test_epoch_mixing_always_withheld(self):
        result = imported(frame(), frame(sequence=1, epoch=OTHER))
        self.assertIn('epoch_mismatch', codes(result))
        self.assertFalse(result.sections)
        self.assertEqual(result.report['frames'][1]['transport_epoch'], OTHER)

    def test_frame_after_end_and_end_timestamp_conflict(self):
        for frames, code in (([frame(kind=2), frame(sequence=1)], 'frame_after_end'),
                             ([frame(), frame(kind=2, sequence=1, first=b'abcd', last=b'abcd')], 'end_timestamp_conflict')):
            result = imported(*frames)
            self.assertIn(code, codes(result))
            self.assertFalse(result.sections)

    def test_invalid_inputs_remain_in_bundle_and_block_reconstruction(self):
        result = imported(b'bad', frame())
        self.assertIn('partial_header', codes(result))
        self.assertFalse(result.sections)
        self.assertEqual(result.sources[0].data, b'bad')
        self.assertEqual(result.report['frames'][1]['validation'], 'valid')

    def test_empty_input_and_explicit_context(self):
        self.assertIn('no_binary_inputs', codes(imported()))
        with self.assertRaises(ValueError):
            import_payloads([], replay_id='')

    def test_resume_is_claim_only_never_fills_prior_bytes(self):
        result = imported(frame(sequence=1, offset=14), resume=resume(segments=[segment()]))
        self.assertEqual(result.report['status'], 'validated_observations')
        self.assertIn('resume_bytes_unavailable', codes(result))
        self.assertFalse(result.sections)
        self.assertEqual(result.report['resume']['status'], 'unverified_external_claims')

    def test_resume_offset_sequence_epoch_conflicts(self):
        for data, code in ((frame(sequence=1), 'resume_offset_conflict'),
                           (frame(offset=14), 'resume_sequence_conflict'),
                           (frame(sequence=1, offset=14, epoch=OTHER), 'epoch_mismatch')):
            result = imported(data, resume=resume(segments=[segment()]))
            self.assertIn(code, codes(result))
            self.assertFalse(result.sections)

    def test_resume_duplicate_gap_overlap_and_missing_section(self):
        for segments, code in (([segment(), segment()], 'resume_duplicate_segment'),
                               ([segment(4)], 'resume_segment_gap'),
                               ([segment(), segment(5)], 'resume_segment_overlap'),
                               ([segment(section=2)], 'source_section_gap')):
            result = imported(frame(sequence=1, offset=14), resume=resume(segments=segments))
            self.assertIn(code, codes(result))
            self.assertFalse(result.sections)

    def test_invalid_resume_types_bounds_and_duplicate_json_keys(self):
        values = [resume(latest=True), resume(latest=2**63 - 1), resume(epoch='bad'),
                  resume(segments=[segment(-1)]), resume(segments=[segment(length=True)]),
                  resume(segments=[segment(2**63 - 1, 1)]), resume(segments=[segment(section=2**31)]),
                  metadata([]), source(b'{"epoch":1,"epoch":2}'), source(b'{"epoch":NaN}')]
        for value in values:
            with self.subTest(value=value):
                result = imported(frame(), resume=value)
                self.assertIn('invalid_resume', codes(result))
                self.assertFalse(result.sections)

    def test_deeply_nested_sidecars_report_errors_and_preserve_sources(self):
        nested = source(b'{"x":' + b'[' * 10000 + b'0' + b']' * 10000 + b'}')
        for kwargs, code in (({'resume': nested}, 'invalid_resume'),
                             ({'terminal_scoreboards': [nested]}, 'invalid_terminal_scoreboard')):
            with self.subTest(code=code):
                result = imported(frame(), **kwargs)
                self.assertIn(code, codes(result))
                self.assertEqual(result.sources[-1].data, nested.data)
                self.assertFalse(result.sections)
                with tempfile.TemporaryDirectory() as directory:
                    result.write(Path(directory) / 'bundle')
                    self.assertEqual((Path(directory) / 'bundle/sources/000001.bin').read_bytes(), nested.data)

    def test_terminal_entity_hero_only_without_account_or_stat_join(self):
        result = imported(frame(), terminal_scoreboards=[terminal()])
        row = result.report['terminal_scoreboards'][0]
        self.assertEqual(row['players'], [{'entity_id': 7, 'hero': 'Ringo'}])
        self.assertEqual(row['usage'], 'entity_hero_corroboration_only_no_automatic_join')
        self.assertFalse(result.report['claims']['terminal_scoreboard_stats_available'])
        self.assertEqual(result.report['claims']['account_identity'], 'unverified')

    def test_terminal_rejects_stats_unbound_epoch_unknown_fields_and_bad_rows(self):
        values = [terminal(epoch=OTHER), terminal(players=[]), terminal(players=[{'entity_id': 7, 'hero': 'Ringo', 'kills': 4}]),
                  terminal(players=[{'entity_id': True, 'hero': 'Ringo'}]),
                  terminal(players=[{'entity_id': 0, 'hero': 'Ringo'}]),
                  terminal(players=[{'entity_id': 2**32 - 1, 'hero': 'Ringo'}]),
                  terminal(players=[{'entity_id': 7, 'hero': 'a"b'}]),
                  terminal(players=[{'entity_id': 7, 'hero': 'é'}]),
                  terminal(players=[{'entity_id': 7, 'hero': 'Ringo'}] * 2), terminal(account_uuid=EPOCH)]
        for value in values:
            with self.subTest(value=value):
                result = imported(frame(), terminal_scoreboards=[value])
                self.assertIn('invalid_terminal_scoreboard', codes(result))
                self.assertFalse(result.sections)

    def test_existing_synthetic_decoder_fixture_round_trip(self):
        # Existing repository fixture, rewrapped synthetically, not a captured VGNL stream.
        from tests.test_product_duration_provenance import replay_bytes
        from vg.core.vgr_records import iter_records
        from vg.decoder_v2.player_state import decode_player_state
        data = replay_bytes(crystal=120, death=110)
        native = split_records(data)
        midpoint = native[len(native) // 2].offset
        result = imported(frame(data[:midpoint]), frame(data[midpoint:], sequence=1, offset=midpoint))
        self.assertEqual(result.sections[0], data)
        self.assertEqual(len(list(iter_records(result.sections[0]))), len(native))
        with tempfile.TemporaryDirectory() as directory:
            result.write(Path(directory) / 'bundle')
            state = decode_player_state(Path(directory) / 'bundle/replay/imported.0.vgr').to_dict()
            self.assertEqual(state['players'][0]['name'], 'PlayerOne')
            self.assertFalse(state['definitive_analysis']['eligible'])


class CLITests(unittest.TestCase):
    def test_cli_bundle_success_error_exit_and_never_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='VGNL spaces ') as directory:
            root = Path(directory)
            path = root / 'source.bin'
            path.write_bytes(frame())
            before = path.read_bytes()
            args = [sys.executable, '-B', '-m', 'vg.core.vgnl_importer', str(path),
                    '--replay-id', '../../unsafe-name', '-o', str(root / 'bundle')]
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / 'bundle/manifest.json').read_text())
            self.assertEqual(report['replay_context']['raw_replay_id'], '../../unsafe-name')
            self.assertEqual((root / 'bundle/replay/imported.0.vgr').read_bytes(), record())
            self.assertEqual((root / 'bundle/sources/000000.bin').read_bytes(), before)
            again = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual(path.read_bytes(), before)
            path.write_bytes(b'bad')
            args[-1] = str(root / 'bad-bundle')
            invalid = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 1)
            self.assertFalse((root / 'bad-bundle/replay').exists())
            self.assertEqual((root / 'bad-bundle/sources/000000.bin').read_bytes(), b'bad')

    def test_cli_resume_and_terminal_sidecars_preserve_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / 'frame.bin'
            payload.write_bytes(frame(sequence=1, offset=14))
            claimed = root / 'resume.json'
            claimed.write_bytes(resume(segments=[segment()]).data)
            scoreboard = root / 'terminal.json'
            scoreboard.write_bytes(terminal().data)
            args = [sys.executable, '-B', '-m', 'vg.core.vgnl_importer', str(payload),
                    '--replay-id', 'test', '--resume', str(claimed),
                    '--terminal-scoreboard', str(scoreboard), '-o', str(root / 'bundle')]
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root / 'bundle/manifest.json').read_text())
            self.assertEqual(report['reconstruction'], 'withheld')
            self.assertEqual(len(report['terminal_scoreboards']), 1)
            self.assertEqual((root / 'bundle/sources/000001.bin').read_bytes(), claimed.read_bytes())
            self.assertEqual((root / 'bundle/sources/000002.bin').read_bytes(), scoreboard.read_bytes())

    def test_cli_missing_input_and_parent_are_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            args = [sys.executable, '-B', '-m', 'vg.core.vgnl_importer', str(Path(directory) / 'missing'),
                    '--replay-id', 'test', '-o', str(Path(directory) / 'out')]
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            Path(args[4]).write_bytes(frame())
            args[-1] = str(Path(directory) / 'absent-parent/out')
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(directory) / 'absent-parent').exists())


if __name__ == '__main__':
    unittest.main()
