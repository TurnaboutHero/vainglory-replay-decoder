import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_product_duration_provenance import replay_bytes
from vg.core import export_matches as exports
from vg.core.batch_result import PartialBatchError
from vg.core.replay_output import ReplayOutputError, recover_report_set
from vg.core.unified_decoder import DecodedMatch, DecodedPlayer, UnifiedDecoder


class ProductExportsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        self.out = self.root / 'out'
        self.out.mkdir()
        self.replay = self.add_replay('sample.0.vgr')

    def add_replay(self, name, data=None):
        path = self.inputs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(replay_bytes() if data is None else data)
        return path

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-m', 'vg.core.export_matches', *map(str, args)],
                              capture_output=True, text=True)

    def csv_rows(self, path):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))

    def hashes(self):
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.out.iterdir() if path.is_file()}

    def test_exports_happy_cli_single_destinations(self):
        # Given real replay bytes and every supported single destination form.
        for name in ('result.csv', 'result.json', 'result'):
            with self.subTest(name=name):
                target = self.out / name
                # When the public command exports both representations.
                result = self.cli(self.replay, '-o', target)
                # Then both formats parse independently with matching input identity.
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(target.with_suffix('.json').read_text())
                rows = self.csv_rows(target.with_suffix('.csv'))
                self.assertEqual(payload['input_id'], rows[0]['input_id'])
                self.assertIn('duration_status', rows[0])
                self.assertIsNone(payload['left_team'][0]['kills'])
        result = self.cli(self.replay, '-o', self.out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / 'sample.json').exists())
        result = self.cli(self.replay, '-o', self.out / 'only.csv', '--csv-only')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.out / 'only.json').exists())
        receipt = json.loads((self.out / 'only.csv.receipt.json').read_text())
        self.assertEqual(receipt['batch']['succeeded'], 1)
        self.assertEqual(receipt['status'], 'complete')

    def test_exports_happy_partial_identity_and_typed_legacy_api(self):
        # Given duplicate display names separated by a failed discovered input.
        self.replay.unlink()
        self.add_replay('a/same.0.vgr')
        self.add_replay('b/broken.0.vgr', b'broken')
        self.add_replay('c/same.0.vgr')
        # When a real batch publishes its successful matches.
        result = self.cli(self.inputs, '--batch', '-o', self.out)
        # Then every artifact uses discovered ordinals and scoped path IDs.
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads((self.out / 'all_matches.json').read_text())
        self.assertEqual((report['discovered'], report['succeeded'], report['failed']), (3, 2, 1))
        self.assertEqual(report['status'], 'partial')
        expected = [('1', 'a/same.0.vgr'), ('3', 'c/same.0.vgr')]
        for filename in ('all_matches.csv', 'match_summary.csv'):
            self.assertEqual([(r['match_idx'], r['input_id']) for r in self.csv_rows(self.out / filename)], expected)
        self.assertEqual([(str(r['match_idx']), r['input_id']) for r in report['matches']], expected)
        for ordinal, identity in expected:
            self.assertEqual(json.loads((self.out / f'match_{ordinal}.json').read_text())['input_id'], identity)
        self.assertFalse((self.out / 'match_2.json').exists())
        receipt = json.loads((self.out / 'export_receipt.json').read_text())
        self.assertEqual(receipt['batch']['results'][1]['status'], 'failed')
        with self.assertRaises(PartialBatchError) as caught:
            exports.decode_batch(str(self.inputs), output_dir=str(self.out))
        self.assertEqual(caught.exception.report['failed'], 1)

    def test_exports_happy_formula_zero_null_and_provenance(self):
        # Given names that spreadsheets would evaluate and actual negative numbers.
        names = ('=SUM(1,1)', '  +cmd', '\t@x')
        players = [DecodedPlayer(name, 'left', 'Hero', 1, i, kills=-1, deaths=0)
                   for i, name in enumerate(names)]
        match = DecodedMatch('formula', str(self.replay), 'mode', 'map', 3,
                             duration_seconds=0, left_team=players)
        # When both serializers process the same in-memory decoded value.
        json_path, csv_path = exports.export_single(self.replay, match, str(self.out / 'formula.csv'))
        # Then only CSV text is escaped, null is blank and zero remains zero.
        rows = self.csv_rows(csv_path)
        self.assertTrue(csv_path.read_bytes().startswith(b'\xef\xbb\xbf'))
        self.assertEqual([r['player_name'] for r in rows], ["'" + n for n in names])
        self.assertEqual([p['name'] for p in json.loads(json_path.read_text())['left_team']], list(names))
        self.assertEqual((rows[0]['kills'], rows[0]['deaths'], rows[0]['assists'], rows[0]['duration_s']), ('-1', '0', '', '0'))
        self.assertIn('final_validation_status', rows[0])
        summary = exports.match_to_summary_row(match)
        self.assertEqual(summary['kills_known_players'], 3)
        self.assertEqual(summary['total_players'], 3)
        self.assertIsNone(summary['right_kills'])
        self.assertIsNone(exports._complete_sum([]))

    def test_exports_happy_empty_csv_only_receipt(self):
        # Given an existing empty root.
        self.replay.unlink()
        # When CSV-only batch runs through the CLI.
        result = self.cli(self.inputs, '--batch', '--csv-only', '-o', self.out)
        # Then header-only outputs and the empty receipt are durable.
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((self.out / 'export_receipt.json').read_text())
        self.assertEqual(receipt['batch']['status'], 'empty')
        for name in ('all_matches.csv', 'match_summary.csv'):
            self.assertEqual(self.csv_rows(self.out / name), [])
            self.assertGreater((self.out / name).stat().st_size, 10)
        self.assertEqual(exports.decode_batch(str(self.inputs), output_dir=str(self.out), csv_only=True), [])

    def test_exports_failure_serialization_preserves_prior(self):
        # Given an already published generation.
        exports.decode_batch_report(str(self.inputs), output_dir=str(self.out))
        before = self.hashes()
        # When serialization fails before staging.
        with patch('vg.core.export_matches.serialize_csv', side_effect=TypeError('serialization fault')):
            with self.assertRaises(TypeError):
                exports.decode_batch_report(str(self.inputs), output_dir=str(self.out))
        # Then every previous byte and its receipt remains unchanged.
        self.assertEqual(self.hashes(), before)

    def test_exports_failure_second_replace_and_rollback_recovery(self):
        # Given a published prior generation and changed replay bytes.
        for rollback_failure in (False, True):
            with self.subTest(rollback_failure=rollback_failure):
                exports.decode_batch_report(str(self.inputs), output_dir=str(self.out))
                before = self.hashes()
                self.replay.write_bytes(replay_bytes(death=120))
                real_replace = os.replace
                calls = 0
                def fail_replace(source, destination):
                    nonlocal calls
                    calls += 1
                    if calls == 3 or (rollback_failure and calls == 4):
                        raise OSError('replace fault')
                    return real_replace(source, destination)
                # When the second output replace fails, optionally also its rollback.
                with patch('vg.core.report_transaction.os.replace', side_effect=fail_replace):
                    with self.assertRaises(ReplayOutputError):
                        exports.decode_batch_report(str(self.inputs), output_dir=str(self.out))
                # Then rollback restores bytes or leaves a recoverable pending receipt.
                receipt_path = self.out / 'export_receipt.json'
                if rollback_failure:
                    pending = json.loads(receipt_path.read_text())
                    self.assertEqual(pending['status'], 'pending')
                    self.assertEqual(pending['batch']['succeeded'], 1)
                    recover_report_set(receipt_path)
                self.assertEqual(self.hashes(), before)

    def test_exports_failure_stale_rerun_and_empty_replacement(self):
        # Given two prior owned match files and an unowned sentinel.
        extra = self.add_replay('second.0.vgr')
        exports.decode_batch_report(str(self.inputs), output_dir=str(self.out))
        sentinel = self.out / 'match_900.json'
        sentinel.write_bytes(b'unowned')
        extra.unlink()
        self.replay.unlink()
        # When the next generation is an empty CSV-only batch.
        exports.decode_batch_report(str(self.inputs), output_dir=str(self.out), csv_only=True)
        # Then stale ownership is explicit and prior data is never silently current.
        receipt = json.loads((self.out / 'export_receipt.json').read_text())
        self.assertEqual(receipt['batch']['status'], 'empty')
        self.assertEqual({Path(p).name for p in receipt['stale_outputs']}, {'match_1.json', 'match_2.json', 'all_matches.json'})
        self.assertNotIn(str(sentinel), receipt['stale_outputs'])
        self.assertEqual(sentinel.read_bytes(), b'unowned')
        self.assertEqual(self.csv_rows(self.out / 'all_matches.csv'), [])

    def test_exports_failure_input_and_output_aliases(self):
        # Given input bytes and output aliases including explicitly consumed truth.
        truth = self.out / 'truth.json'
        truth.write_text('{"matches": []}')
        before = self.replay.read_bytes(), truth.read_bytes()
        linked = self.out / 'linked.csv'
        linked.hardlink_to(self.replay)
        same = self.out / 'same.json'
        same.write_bytes(b'prior')
        same.with_suffix('.csv').hardlink_to(same)
        # When CLI preflight sees aliases or invalid global roots.
        cases = [(self.replay, '-o', linked), (self.replay, '--truth', truth, '-o', truth),
                 (self.replay, '-o', same), (self.inputs / 'missing', '--batch'),
                 (self.replay, '--batch')]
        for args in cases:
            result = self.cli(*args)
            # Then errors are actionable and no protected bytes change.
            self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual((self.replay.read_bytes(), truth.read_bytes()), before)
        self.assertEqual(same.read_bytes(), b'prior')

    def test_exports_failure_remembers_truth_without_duration(self):
        # Given a decoded match whose consumed truth has no duration override.
        truth = self.out / 'consumed.json'
        truth.write_text(json.dumps({'matches': [{'replay_file': str(self.replay),
                                                 'players': {}}]}))
        match = UnifiedDecoder(str(self.replay)).decode_with_truth(str(truth))
        before = truth.read_bytes()
        self.assertEqual(match.truth_source, str(truth.absolute()))
        # When callers omit truth_path and try to export over that consumed source.
        for export in (lambda: exports.export_match_json(match, truth),
                       lambda: exports.export_single(self.replay, match, str(truth))):
            with self.assertRaises(ReplayOutputError):
                export()
            # Then both public export APIs preserve the truth bytes.
            self.assertEqual(truth.read_bytes(), before)
