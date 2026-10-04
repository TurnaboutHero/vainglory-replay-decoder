"""Evidence discipline and strict-framing regressions for the event atlas."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

from vg.tools.event_semantics_atlas import audit_corpus, main, read_json, summary, validate

DOCS = Path(__file__).resolve().parents[1] / 'vg/docs'


class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read_json(DOCS / 'vg-binary-event-candidates-2026-09-09.json')
        cls.atlas = read_json(DOCS / 'event_semantics_2026-10-04.json')

    def check(self, atlas=None, **kwargs):
        return validate(atlas or self.atlas, self.source, DOCS, **kwargs)

    def changed(self, opcode):
        atlas = deepcopy(self.atlas)
        row = next(row for row in atlas['events'] if row['opcode'] == opcode)
        return atlas, row

    def test_complete_source_union_and_dimensions(self):
        result = self.check(require_reviewed=True)
        self.assertTrue(result['ok'], result['issues'])
        self.assertEqual({r['opcode'] for r in self.atlas['events']}, {r['opcode'] for r in self.source['candidates']})
        counts = result['summary']
        self.assertEqual((counts['candidates'], counts['receiver'], counts['emitter'], counts['observed']), (161, 123, 111, 85))
        self.assertEqual(counts['multiple_recorded_variant_families'], 8)
        self.assertEqual(counts['recorded_variants'], 93)
        self.assertFalse(result['all_meanings_decoded'])
        self.assertEqual(result['validation_mode'], 'bounded_evidence_inventory')
        self.assertFalse(result['six_field_accuracy_certified'])

    def test_name_only_is_not_payload_proof(self):
        atlas, row = self.changed('0x0005')
        row['variants'][0]['layout'].update(status='partial', evidence=['classes'])
        issues = self.check(atlas)['issues']
        self.assertIn('certainty_without_evidence', [i['code'] for i in issues])

    def test_variant_cannot_disappear(self):
        atlas, row = self.changed('0x03ee')
        row['variants'] = [v for v in row['variants'] if v['payload_bytes'] != 222]
        self.assertIn('missing_variant', [i['code'] for i in self.check(atlas)['issues']])

    def test_framing_prefix_does_not_certify_whole_variant(self):
        atlas, row = self.changed('0x041c')
        variant = next(v for v in row['variants'] if v['payload_bytes'] == 22)
        variant['application']['status'] = 'static_proven'
        self.assertIn('framing_scope_overclaim', [i['code'] for i in self.check(atlas)['issues']])

    def test_framing_review_requires_remaining_unknown(self):
        atlas, row = self.changed('0x03ee')
        variant = next(v for v in row['variants'] if v['payload_bytes'] == 222)
        variant['framing_review']['remaining_unknown'] = ''
        self.assertIn('framing_missing_limit', [i['code'] for i in self.check(atlas)['issues']])

    def test_unobserved_candidate_remains_unknown(self):
        _, row = self.changed('0x0005')
        self.assertEqual(row['dimensions']['observed_records'], 0)
        self.assertEqual(row['semantic_status'], 'unknown')
        self.assertTrue(all(v['application']['status'] == 'unknown' for v in row['variants']))
        atlas, row = self.changed('0x0005')
        row['semantic_status'] = 'applied_static'
        self.assertIn('certainty_without_evidence', [i['code'] for i in self.check(atlas)['issues']])

    def test_high_value_unknown_blocks_acceptance(self):
        atlas, row = self.changed('0x043d')
        row['player_state_gate']['status'] = 'pending'
        result = self.check(atlas, require_reviewed=True, require_player_state_semantics=True)
        self.assertFalse(result['ok'])
        self.assertIn('player_state_gate_pending', [i['code'] for i in result['issues']])
        self.assertTrue(any(i.get('opcode') == '0x043d' for i in result['issues']))

    def test_explicit_control_flag_preserves_legacy_strict_failure(self):
        reports = []
        with tempfile.TemporaryDirectory() as directory:
            for flag in ('--require-per-opcode-runtime-controls', '--require-player-state-semantics'):
                output = Path(directory) / (flag[2:] + '.json')
                with redirect_stdout(io.StringIO()):
                    code = main(['validate', '--atlas', str(DOCS / 'event_semantics_2026-10-04.json'),
                                 '--source', str(DOCS / 'vg-binary-event-candidates-2026-09-09.json'),
                                 '--require-reviewed', flag, '--output', str(output)])
                self.assertEqual(code, 1)
                report = read_json(output)
                self.assertEqual(report['validation_mode'], 'per_opcode_runtime_controls')
                self.assertFalse(report['six_field_accuracy_certified'])
                reports.append(report['issues'])
        self.assertEqual(reports[0], reports[1])
        self.assertEqual({i['opcode'] for i in reports[0]},
                         {'0x03ee'})
        self.assertEqual({r['opcode'] for r in self.atlas['events']
                          if r['player_state_required'] and r['player_state_gate']['status'] == 'verified'},
                         {'0x03f2', '0x03f3', '0x041c', '0x041d', '0x043d', '0x0444', '0x044b', '0x046f'})
        self.assertTrue(all(i['code'] == 'player_state_gate_pending' for i in reports[0]))

    def test_receiver_proof_cannot_become_application_proof(self):
        atlas, row = self.changed('0x03ee')
        row['variants'][0]['application'].update(status='static_proven', effect='invented', evidence=['receiver:03ee'])
        self.assertIn('certainty_without_evidence', [i['code'] for i in self.check(atlas)['issues']])

    def test_runtime_match_needs_runtime_evidence(self):
        atlas, row = self.changed('0x043d')
        variant = next(v for v in row['variants'] if v['domain'] == 'serialized')
        variant['application']['status'] = 'runtime_matched'
        self.assertIn('certainty_without_evidence', [i['code'] for i in self.check(atlas)['issues']])

    def test_unaligned_practice_capture_cannot_prove_replay_variant(self):
        atlas, row = self.changed('0x043d')
        variant = next(v for v in row['variants'] if v['domain'] == 'serialized')
        variant['application']['status'] = 'runtime_matched'
        variant['application']['evidence'].append('practice-grants')
        self.assertIn('runtime_variant_unmatched', [i['code'] for i in self.check(atlas)['issues']])

    def test_orphaned_reference_and_modified_source_are_rejected(self):
        atlas, row = self.changed('0x03ee')
        row['evidence'].append('missing-evidence')
        self.assertIn('orphaned_reference', [i['code'] for i in self.check(atlas)['issues']])
        atlas['evidence']['receiver:03ee']['sha256'] = '0' * 64
        self.assertIn('evidence_hash_mismatch', [i['code'] for i in self.check(atlas)['issues']])

    def test_missing_candidate_and_dimension_drift_are_rejected(self):
        atlas, row = self.changed('0x03ee')
        row['dimensions']['observed_records'] = 1
        atlas['events'].pop()
        codes = [i['code'] for i in self.check(atlas)['issues']]
        self.assertIn('dimension_drift', codes)
        self.assertIn('candidate_union_mismatch', codes)

    def test_field_bounds_are_per_variant(self):
        atlas, row = self.changed('0x03ee')
        variant = next(v for v in row['variants'] if v['payload_bytes'] == 216)
        variant['layout']['fields'][0]['offset'] = 215
        self.assertIn('field_outside_variant', [i['code'] for i in self.check(atlas)['issues']])

    def test_falsifier_required_even_for_named_classes(self):
        atlas, row = self.changed('0x03f1')
        row['uncertainty'][0]['falsifier'] = ''
        self.assertIn('missing_falsifier', [i['code'] for i in self.check(atlas, require_reviewed=True)['issues']])

    def test_required_gate_cannot_be_removed(self):
        atlas, row = self.changed('0x043d')
        row['player_state_required'] = []
        self.assertIn('required_semantics_policy', [i['code'] for i in self.check(atlas)['issues']])

    def test_request_record_does_not_inherit_serializer_side_effect(self):
        _, row = self.changed('0x0438')
        self.assertFalse(row['dimensions']['receiver_handled'])
        recorded = next(v for v in row['variants'] if v['domain'] == 'recorded')
        self.assertEqual(recorded['application']['status'], 'unknown')

    def test_optional_unused_events_do_not_block_reader_gate(self):
        atlas, row = self.changed('0x0448')
        self.assertEqual(row['reader_usage']['role'], 'secondary_unused')
        self.assertEqual(row['player_state_required'], [])
        result = self.check(atlas, require_player_state_semantics=True)
        self.assertFalse(any(i.get('opcode') == '0x0448' for i in result['issues']))
        self.assertEqual({i['opcode'] for i in result['issues'] if i['code'] == 'player_state_gate_pending'},
                         {'0x03ee'})

    def test_reader_policy_must_match_current_sources(self):
        atlas = deepcopy(self.atlas)
        atlas['reader_policy']['source_sha256']['native_inventory.py'] = '0' * 64
        self.assertIn('reader_policy_source_drift', [i['code'] for i in self.check(atlas)['issues']])

    def test_native_prefix_does_not_close_longer_variant(self):
        atlas, row = self.changed('0x03ee')
        exact = next(v for v in row['variants'] if v['payload_bytes'] == 216)
        longer = next(v for v in row['variants'] if v['payload_bytes'] == 222)
        self.assertEqual(exact['application']['status'], 'static_proven')
        self.assertEqual(longer['application']['status'], 'unknown')
        self.assertEqual(longer['native_prefix_application']['copied_bytes'], 216)
        longer['native_prefix_application']['whole_variant_verified'] = True
        self.assertIn('native_prefix_overclaim', [i['code'] for i in self.check(atlas)['issues']])

    def test_native_prefix_size_must_be_actual_receiver_copy(self):
        atlas, row = self.changed('0x041d')
        recorded = next(v for v in row['variants'] if v['domain'] == 'recorded')
        recorded['native_prefix_application']['copied_bytes'] = 8
        self.assertIn('native_prefix_bounds', [i['code'] for i in self.check(atlas)['issues']])

    def test_suffix_field_proof_requires_replay_target(self):
        atlas, row = self.changed('0x041d')
        recorded = next(v for v in row['variants'] if v['domain'] == 'recorded')
        recorded['required_field_application']['evidence'].remove('atlas:replay-vtable')
        self.assertIn('required_field_proof_incomplete', [i['code'] for i in self.check(atlas)['issues']])

    def test_suffix_field_proof_does_not_cover_networking(self):
        atlas, row = self.changed('0x03f2')
        recorded = next(v for v in row['variants'] if v['payload_bytes'] == 126)
        recorded['required_field_application']['mode'] = 'networking'
        self.assertIn('required_field_scope_overclaim', [i['code'] for i in self.check(atlas)['issues']])

    def test_removing_field_proof_reopens_exact_variant(self):
        atlas, row = self.changed('0x03ee')
        recorded = next(v for v in row['variants'] if v['payload_bytes'] == 222)
        del recorded['required_field_application']
        issues = self.check(atlas, require_player_state_semantics=True)['issues']
        unknown = [i for i in issues if i['code'] == 'required_semantics_unknown']
        self.assertEqual([(i['opcode'], i['variant']) for i in unknown], [('0x03ee', ('recorded', 222))])

    def test_serialized_and_recorded_variants_are_separate(self):
        _, row = self.changed('0x043d')
        self.assertEqual({(v['domain'], v['payload_bytes']) for v in row['variants']}, {('serialized', 12), ('recorded', 14)})
        self.assertEqual(next(v for v in row['variants'] if v['domain'] == 'serialized')['application']['status'], 'static_proven')
        recorded = next(v for v in row['variants'] if v['domain'] == 'recorded')
        self.assertEqual(recorded['application']['status'], 'runtime_matched')
        self.assertIn('c33-inventory-matches', recorded['application']['evidence'])
        _, unobserved = self.changed('0x044c')
        self.assertEqual(next(v for v in unobserved['variants'] if v['domain'] == 'recorded')['application']['status'], 'unknown')


class CorpusAuditTests(unittest.TestCase):
    def fixture(self, root, data, expected_length=4, expected_records=1):
        docs = root / 'docs'
        prior = docs / 'evidence/2026-09-09-binary-events/corpus/provenance.json'
        prior.parent.mkdir(parents=True)
        replay = root / 'match.0.vgr'
        replay.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        prior.write_text(json.dumps({'record_count': expected_records, 'rows': [
            {'corpus': 'C01', 'record_count': expected_records, 'sections': [{'number': 0, 'sha256': digest}]}]}))
        manifest = {'recordings': [{'recording_id': 'C01', 'partition': 'holdout', 'source_files': [
            {'section': 0, 'path': 'match.0.vgr', 'sha256': digest}]}]}
        source = {'candidates': [{'opcode': '0x1234', 'observed': {'record_count': expected_records,
                  'payload_length_histogram': {str(expected_length): expected_records}, 'recording_counts': {'C01': expected_records}}}]}
        atlas = {'events': [{'opcode': '0x1234', 'variants': [{'domain': 'recorded', 'payload_bytes': expected_length}]}]}
        return manifest, root / 'manifest.json', atlas, source, docs

    def test_strict_framing_does_not_scan_embedded_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = struct.pack('>fIH', 1.0, 6, 0x1234) + bytes.fromhex('03ee03f3')
            result, _ = audit_corpus(*self.fixture(Path(tmp), data))
            self.assertTrue(result['ok'], result['issues'])
            self.assertEqual(result['summary']['records'], 1)
            self.assertEqual(result['summary']['observed_opcodes'], 1)
            self.assertEqual(result['recordings'][0]['partition'], 'holdout')
            self.assertEqual(list(result['first_exemplars']), ['0x1234:4'])

    def test_malformed_record_fails_with_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = struct.pack('>fIH', 1.0, 10, 0x1234) + b'x'
            result, _ = audit_corpus(*self.fixture(Path(tmp), data))
            self.assertFalse(result['ok'])
            self.assertIn('malformed_records', [i['code'] for i in result['issues']])

    def test_hash_mismatch_and_missing_recording_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = struct.pack('>fIH', 1.0, 6, 0x1234) + b'four'
            args = self.fixture(Path(tmp), data)
            args[0]['recordings'][0]['source_files'][0]['sha256'] = '0' * 64
            result, _ = audit_corpus(*args)
            self.assertIn('source_hash_mismatch', [i['code'] for i in result['issues']])
            args[0]['recordings'] = []
            result, _ = audit_corpus(*args)
            self.assertIn('missing_recording', [i['code'] for i in result['issues']])

    def test_actual_new_variant_and_drift_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = struct.pack('>fIH', 1.0, 7, 0x1234) + b'five!'
            result, _ = audit_corpus(*self.fixture(Path(tmp), data))
            codes = [i['code'] for i in result['issues']]
            self.assertIn('uncatalogued_variant', codes)
            self.assertIn('corpus_drift', codes)
            self.assertEqual(result['observations'][0]['payload_length_histogram'], {'5': 1})


if __name__ == '__main__':
    unittest.main()
