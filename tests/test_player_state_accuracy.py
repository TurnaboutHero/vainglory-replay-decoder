"""Adversarial contracts for the independent player-state accuracy gate."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from vg.tools.player_state_accuracy import (FIELDS, audit, compare_observation, digest,
    decode, legacy_state, main, mutate, prepare, publish)
from vg.core.replay_output import ReplayOutputError


def fixture():
    values = {'name': 'same-name', 'hero': 'Lyra', 'kda': {'kills': 0, 'deaths': 1, 'assists': 2},
              'minion_kills': 0, 'items': [{'native_item_id': 101, 'quantity': 2}],
              'gold_balance': '3f800000', 'net_worth': '40000000'}
    player = {'reference_player_id': 'client-player-1', 'native_actor_id': 0x12345678,
              'actor_link': {'status': 'observed', 'source_refs': ['capture']},
              'fields': {k: {'status': 'observed', 'value': v, 'source_refs': ['capture']}
                         for k, v in values.items()}}
    observation = {'observation_id': 'sample', 'clock_kind': 'game_time', 'game_time': 10,
                   'record_boundary': {'section': 1, 'record_offset': 20}, 'source_refs': ['capture'],
                   'players': [player]}
    actual = {'support_status': 'supported', 'scope': 'capture', 'requested_game_time': 10,
              'record_boundary': {'section': 1, 'record_offset': 20},
              'players': [dict(deepcopy(values), native_actor_id=0x12345678)]}
    actual['players'][0].update(gold_balance=1.0, net_worth=2.0)
    sources = [{'source_id': 'capture', 'kind': 'client_native'}]
    return observation, actual, sources


class AccuracyTests(unittest.TestCase):
    def compare(self, reference, actual, sources):
        return compare_observation(reference, actual, reference_sources=sources)

    def test_exact_fields_and_zeros_pass(self):
        result = self.compare(*fixture())
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['matched'], len(FIELDS))

    def test_legacy_cli_preserves_actual_exported_players(self):
        from tests.test_player_state_service import recording
        with tempfile.TemporaryDirectory() as tmp:
            replay = Path(tmp) / 'match.0.vgr'
            replay.write_bytes(recording())
            actual, receipt = decode({'source_files': [{'section': 0, 'path': str(replay)}]},
                                     {'clock_kind': 'recorded_end'}, Path(tmp), 'legacy-cli', None)
            self.assertEqual(receipt['returncode'], 0, receipt['stderr'])
            raw = json.loads(receipt['stdout'])
            self.assertTrue(raw['unassigned_players'])
            self.assertEqual(actual['scope'], 'recorded_end')
            self.assertEqual(actual['support_status'], 'supported')
            self.assertEqual(actual['players'][0]['native_actor_id'], raw['unassigned_players'][0]['native_actor_id'])
            self.assertEqual(actual['players'][0]['items'], raw['unassigned_players'][0]['item_details'])
            raw['unassigned_players'][0]['kills'] = 999
            self.assertEqual(legacy_state(raw)['players'][0]['kills'], 999)
            raw['unassigned_players'] = []
            self.assertEqual(legacy_state(raw)['players'], [])

    def test_legacy_player_boundary_must_match_embedded_scope(self):
        actual = {'player_state': {'scope': 'recorded_end', 'support_status': 'supported',
                                  'record_boundary': {'section': 1, 'record_offset': 20}, 'replay_scope': 'one'},
                  'unassigned_players': [{'state_scope': 'recorded_end', 'replay_scope': 'one',
                                          'record_boundary': {'section': 1, 'record_offset': 19}}]}
        self.assertEqual(legacy_state(actual)['support_status'], 'inconsistent_legacy_state')

    def test_altered_actor_and_name_fail(self):
        for field, value, code in [('native_actor_id', 123, 'actor_set_mismatch'), ('name', 'other', 'field_mismatch')]:
            with self.subTest(field=field):
                ref, actual, sources = fixture()
                actual['players'][0][field] = value
                result = self.compare(ref, actual, sources)
                self.assertFalse(result['ok'])
                self.assertIn(code, [i['code'] for i in result['issues']])

    def test_duplicate_loss_fails_and_grouped_items_match(self):
        ref, actual, sources = fixture()
        actual['players'][0]['items'] = [{'native_item_id': 101, 'quantity': 1}] * 2
        self.assertTrue(self.compare(ref, actual, sources)['ok'])
        actual['players'][0]['items'].pop()
        result = self.compare(ref, actual, sources)
        self.assertFalse(result['ok'])
        self.assertEqual(result['issues'][0]['field'], 'items')

    def test_one_gold_bit_fails(self):
        ref, actual, sources = fixture()
        ref = mutate(ref, 'flip-one-gold-bit')
        result = self.compare(ref, actual, sources)
        self.assertFalse(result['ok'])
        self.assertEqual(result['issues'][0]['field'], 'gold_balance')

    def test_public_definition_id_adapter_preserves_multiplicity(self):
        ref, actual, sources = fixture()
        actual['players'][0]['items'] = [{'definition_id': 101, 'quantity': 1, 'reconstruction_index': n}
                                         for n in (2, 3)]
        self.assertTrue(self.compare(ref, actual, sources)['ok'])
        self.assertNotIn('native_item_id', actual['players'][0]['items'][0])
        actual['players'][0]['items'] = tuple(actual['players'][0]['items'])
        self.assertTrue(self.compare(ref, actual, sources)['ok'])
        actual['players'][0]['items'] = list(actual['players'][0]['items'])
        actual['players'][0]['items'].pop()
        result = self.compare(ref, actual, sources)
        self.assertFalse(result['ok'])
        self.assertEqual(result['issues'][0]['field'], 'items')

    def test_missing_reference_fails(self):
        ref, actual, sources = fixture()
        changed = mutate(ref, 'remove-items')
        self.assertIn('items', ref['players'][0]['fields'])
        result = self.compare(changed, actual, sources)
        self.assertFalse(result['ok'])
        self.assertEqual(result['required_missing'], ['items'])

    def test_missing_value_fails(self):
        ref, actual, sources = fixture()
        actual['players'][0]['items'] = None
        self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_duplicate_actor_and_lost_actor_fail(self):
        for players in ([], fixture()[1]['players'] * 2):
            ref, actual, sources = fixture()
            actual['players'] = players
            self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_duplicate_names_do_not_merge(self):
        ref, actual, sources = fixture()
        second = deepcopy(ref['players'][0])
        second.update(native_actor_id=0xffffffff, reference_player_id='second')
        ref['players'].append(second)
        actual['players'].append(dict(actual['players'][0], native_actor_id=0xffffffff))
        self.assertTrue(self.compare(ref, actual, sources)['ok'])

    def test_unproved_join_or_decoder_truth_fails(self):
        ref, actual, sources = fixture()
        ref['players'][0]['actor_link']['status'] = 'inferred'
        self.assertFalse(self.compare(ref, actual, sources)['ok'])
        ref, actual, sources = fixture()
        sources[0]['kind'] = 'decoder_output'
        self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_incompatible_clocks_and_boundaries_fail(self):
        for patch in ({'scope': 'recorded_end'}, {'requested_game_time': 11}, {'record_boundary': None}):
            ref, actual, sources = fixture()
            actual.update(patch)
            self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_display_gold_not_native_bits(self):
        ref, actual, sources = fixture()
        ref['players'][0]['fields']['gold_balance']['value'] = 1.0
        self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_mutation_requires_real_duplicate(self):
        ref, actual, sources = fixture()
        changed = mutate(ref, 'drop-one-duplicate-item')
        self.assertEqual(ref['players'][0]['fields']['items']['value'][0]['quantity'], 2)
        self.assertFalse(self.compare(changed, actual, sources)['ok'])
        ref['players'][0]['fields']['items']['value'] = []
        with self.assertRaises(ValueError):
            mutate(ref, 'drop-one-duplicate-item')

    def test_invalid_counter_and_nonfinite_gold_fail(self):
        for field, value in [('minion_kills', False), ('kda', {'kills': False, 'deaths': 1, 'assists': 2}),
                             ('gold_balance', '7fc00000')]:
            ref, actual, sources = fixture()
            actual['players'][0][field] = value
            self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_missing_time_and_withheld_value_fail(self):
        ref, actual, sources = fixture()
        del ref['game_time']
        actual['requested_game_time'] = None
        self.assertFalse(self.compare(ref, actual, sources)['ok'])
        ref, actual, sources = fixture()
        actual['players'][0]['field_status'] = {'items': 'unobserved'}
        self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_raw_gold_and_bits_must_agree(self):
        ref, actual, sources = fixture()
        ref['players'][0]['fields']['gold_balance']['value'] = {'float32_bits': '3f800000', 'value': 2.0}
        self.assertFalse(self.compare(ref, actual, sources)['ok'])

    def test_output_manifest_hardlink_and_symlink_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'manifest.json'
            source.write_text('{"original": true}')
            for name, kind in [('manifest.json', 'same'), ('hard.json', 'hard'), ('sym.json', 'sym')]:
                output = Path(tmp) / name
                if kind == 'hard':
                    output.hardlink_to(source)
                elif kind == 'sym':
                    output.symlink_to(source)
                with self.assertRaises(ReplayOutputError):
                    publish(output, {'overwritten': True}, [source])
            self.assertEqual(source.read_text(), '{"original": true}')

    def test_source_missing_and_hash_mismatch_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            replay = base / 'a.0.vgr'
            manifest = {'recordings': [{'recording_id': 'C01', 'source_files': [
                {'section': 0, 'path': str(replay), 'sha256': '0' * 64}]}]}
            self.assertEqual(audit(manifest, base)['exit_code'], 1)
            replay.write_bytes(b'original')
            self.assertEqual(audit(manifest, base)['exit_code'], 2)

    def test_historical_import_keeps_every_original_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = root / 'accuracy-20261004/corpus/manifest.json'
            export.parent.mkdir(parents=True)
            replay = export.parent / 'a.0.vgr'
            replay.write_bytes(b'private')
            export.write_text(json.dumps({'recordings': [{'recording_id': 'C35', 'source_files': [
                {'section': 0, 'path': 'a.0.vgr', 'source_path': 'D:/a.0.vgr', 'sha256': digest(replay)}]}]}))
            truth = root / 'offline-repo/vg/output/tournament_truth.json'
            truth.parent.mkdir(parents=True)
            truth.write_text(json.dumps({'matches': [{'replay_file': 'D:\\a.0.vgr', 'players': {'name': {'gold': 6300}}}]}))
            slots = root / 'offline-repo/vg/docs/item_slotcount_truth_5_11.json'
            slots.parent.mkdir(parents=True)
            slots.write_text(json.dumps({'matches': {'1': {'slots': {'name': 2}}}}))
            manifest = prepare(root, root / 'reference')
            self.assertEqual(len(manifest['historical_rows']), 2)
            self.assertEqual(manifest['historical_rows'][0]['original'], {'gold': 6300})
            self.assertEqual(manifest['historical_rows'][1]['original'], 2)
            self.assertEqual(manifest['recordings'][0]['observations'], [])
            self.assertEqual(manifest['recordings'][0]['aliases'], ['M1'])
            self.assertIn('inventory_count_error', [e['code'] for e in audit(manifest, root)['errors']])
            self.assertEqual(main(['prepare', '--asset-root', str(root), '--output-dir', str(root / 'reference')]), 2)

    def test_cli_missing_truth_writes_failure_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay = root / 'a.0.vgr'
            replay.write_bytes(b'not-decoded-without-reference')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'recordings': [{'recording_id': 'normal17', 'source_files': [
                {'section': 0, 'path': str(replay), 'sha256': digest(replay)}], 'observations': []}]}))
            output = root / 'failure.json'
            self.assertEqual(main(['compare', '--manifest', str(manifest), '--recording', 'normal17',
                                  '--require-six-fields', '--mutate-reference', 'remove-items', '--output', str(output)]), 1)
            result = json.loads(output.read_text())
            self.assertFalse(result['ok'])
            self.assertIn('items', result['errors'][0]['required_missing'])
            self.assertEqual(result['denominator']['recordings'], 1)


if __name__ == '__main__':
    unittest.main()
