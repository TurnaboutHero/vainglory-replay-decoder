from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_product_duration_provenance import replay_bytes
from vg.analysis import batch_report as analysis
from vg.core.batch_result import PartialBatchError
from vg.core.unified_decoder import UnifiedDecoder
from vg.tools import replay_batch_parser as parser


class ProductBatchReportsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        self.replay = self.inputs / 'good.0.vgr'
        self.replay.write_bytes(replay_bytes())
        self.output = self.root / 'report.json'

    def cli(self, module, *args):
        return subprocess.run([sys.executable, '-B', '-m', module, *map(str, args)],
                              capture_output=True, text=True)

    def test_batch_reports_happy_zero_estimate_truth_and_unknown(self):
        # Given actual decoded zero truth, estimated duration and no-roster unknown.
        truth = self.root / 'truth.json'
        truth.write_text(json.dumps({'matches': [{'replay_file': str(self.replay),
            'match_info': {'duration_seconds': 0}, 'players': {}}]}))
        zero = UnifiedDecoder(str(self.replay)).decode_with_truth(str(truth))
        self.replay.write_bytes(replay_bytes(death=120))
        estimate = UnifiedDecoder(str(self.replay)).decode()
        self.replay.write_bytes(replay_bytes(roster=False))
        unknown = UnifiedDecoder(str(self.replay)).decode()
        # When the actual values are aggregated together.
        report = analysis.generate_report([zero, estimate, unknown])
        # Then zero participates, provenance is separated and final unknowns persist.
        stats = report['match_stats']
        self.assertEqual((stats['min_duration_s'], stats['max_duration_s'], stats['avg_duration_s']), (0, 120, 60))
        self.assertEqual((stats['duration_known_samples'], stats['duration_total_samples']), (2, 3))
        self.assertEqual(stats['duration_aggregation_scope'], 'observed_values_not_verified_final')
        self.assertEqual(report['duration_provenance_coverage'], {
            'unknown': {'total_samples': 1, 'known_samples': 0, 'avg_duration_s': None},
            'estimated': {'total_samples': 1, 'known_samples': 1, 'avg_duration_s': 120},
            'supplied_truth': {'total_samples': 1, 'known_samples': 1, 'avg_duration_s': 0}})
        self.assertIsNone(stats['total_kills'])
        self.assertEqual(stats['known_player_samples']['kills'], 0)
        self.assertEqual(report['hero_stats'][0]['known_samples']['kills'], 0)
        self.assertEqual(report['hero_stats'][0]['total_samples'], 2)

    def test_batch_reports_happy_public_apis_and_clis(self):
        # Given a roster family and a valid no-roster family.
        (self.inputs / 'empty-roster.0.vgr').write_bytes(replay_bytes(roster=False))
        # When both public APIs and CLIs process the directory.
        analytical = analysis.decode_all_report(str(self.inputs))
        parsed = parser.batch_parse(self.inputs)
        for module in ('vg.analysis.batch_report', 'vg.tools.replay_batch_parser'):
            result = self.cli(module, self.inputs, '-o', self.output)
            # Then outcomes and stable scoped IDs agree at both surfaces.
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(self.output.read_text())
            self.assertEqual((payload['discovered'], payload['succeeded'], payload['failed']), (2, 2, 0))
            self.assertEqual([row['input_id'] for row in payload['results']], ['empty-roster.0.vgr', 'good.0.vgr'])
        self.assertEqual(analytical['results'], parsed['results'])
        self.assertEqual(len(analysis.decode_all(str(self.inputs))), 2)
        self.assertEqual([row['status'] for row in parsed['replays']], ['complete', 'complete'])

    def test_batch_reports_happy_empty_and_no_roster(self):
        # Given zero players and later an existing empty root.
        self.replay.write_bytes(replay_bytes(roster=False))
        # When no-player statistics are generated and both empty CLIs execute.
        report = analysis.decode_all_report(str(self.inputs))
        rendered = io.StringIO()
        with redirect_stdout(rendered):
            analysis.print_report(report)
        # Then unknown totals/durations remain null and display N/A.
        for key in ('total_kills', 'avg_kills_per_match', 'avg_duration_s', 'min_duration_s', 'max_duration_s'):
            self.assertIsNone(report['match_stats'][key])
        self.assertIn('N/A', rendered.getvalue())
        self.replay.unlink()
        self.assertEqual(analysis.decode_all(str(self.inputs)), [])
        for module in ('vg.analysis.batch_report', 'vg.tools.replay_batch_parser'):
            result = self.cli(module, self.inputs, '-o', self.output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.output.read_text())['status'], 'empty')

    def test_batch_reports_happy_truth_cli_zero(self):
        # Given explicit matched truth with known zero duration.
        truth = self.root / 'truth.json'
        truth.write_text(json.dumps({'matches': [{'replay_file': str(self.replay),
            'match_info': {'duration_seconds': 0}, 'players': {}}]}))
        # When the reporting CLI consumes the supplied truth.
        result = self.cli('vg.analysis.batch_report', self.inputs, '--truth', truth, '-o', self.output)
        # Then duration zero and its supplied provenance survive publication.
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(self.output.read_text())
        self.assertEqual(report['match_stats']['avg_duration_s'], 0)
        self.assertEqual(report['duration_provenance_coverage']['supplied_truth']['known_samples'], 1)

    def test_batch_reports_failure_partial_failed_and_invalid_roots(self):
        # Given one good and one malformed family.
        bad = self.inputs / 'bad.0.vgr'
        bad.write_bytes(b'broken')
        # When both CLIs and legacy list API encounter per-input failures.
        for module in ('vg.analysis.batch_report', 'vg.tools.replay_batch_parser'):
            result = self.cli(module, self.inputs, '-o', self.output)
            # Then partial status retains both outcomes, unlike a global input error.
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(self.output.read_text())
            self.assertEqual((report['status'], report['discovered'], report['succeeded'], report['failed']), ('partial', 2, 1, 1))
            self.assertEqual([row['status'] for row in report['results']], ['failed', 'complete'])
            before = self.output.read_bytes()
            for root in (self.root / 'missing', self.replay):
                invalid = self.cli(module, root, '-o', self.output)
                self.assertEqual(invalid.returncode, 2, invalid.stderr)
                self.assertEqual(self.output.read_bytes(), before)
        with self.assertRaises(PartialBatchError) as caught:
            analysis.decode_all(str(self.inputs))
        self.assertEqual(caught.exception.report['failed'], 1)
        self.replay.unlink()
        for module in ('vg.analysis.batch_report', 'vg.tools.replay_batch_parser'):
            failed = self.cli(module, self.inputs, '-o', self.output)
            self.assertEqual(failed.returncode, 1, failed.stderr)
            self.assertEqual(json.loads(self.output.read_text())['status'], 'failed')

    def test_batch_reports_failure_publication_preserves_prior(self):
        # Given a prior report and actual replay input.
        self.output.write_bytes(b'prior-report')
        before = hashlib.sha256(self.output.read_bytes()).hexdigest()
        # When the final replace fails in each real command handler.
        for module in (analysis, parser):
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch('vg.core.replay_output.os.replace', side_effect=OSError('replace fault')), \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                code = module.main([str(self.inputs), '-o', str(self.output)])
            # Then prior bytes remain and success is never announced.
            self.assertEqual(code, 2)
            self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), before)
            self.assertNotIn('Saved to:', stdout.getvalue())
            self.assertNotIn('JSON report saved', stdout.getvalue())
            self.assertIn('replace fault', stderr.getvalue())

    def test_batch_reports_failure_aliases_including_late_and_truth(self):
        # Given direct, hardlink and truth aliases of consumed inputs.
        alias = self.root / 'alias.json'
        alias.hardlink_to(self.replay)
        truth = self.root / 'truth.json'
        truth.write_text(json.dumps({'matches': [{'replay_file': str(self.replay), 'players': {}}]}))
        before = self.replay.read_bytes(), truth.read_bytes()
        # When CLI preflight and final recheck see each alias.
        for module in ('vg.analysis.batch_report', 'vg.tools.replay_batch_parser'):
            for destination in (self.replay, alias, self.inputs / 'good.5.vgr'):
                result = self.cli(module, self.inputs, '-o', destination)
                # Then no consumed bytes or future replay sections are overwritten.
                self.assertEqual(result.returncode, 2, result.stderr)
        result = self.cli('vg.analysis.batch_report', self.inputs, '--truth', truth, '-o', truth)
        self.assertEqual(result.returncode, 2, result.stderr)
        for module, function in ((analysis, 'decode_all_report'), (parser, 'batch_parse')):
            original = getattr(module, function)
            def introduce_alias(*args, **kwargs):
                report = original(*args, **kwargs)
                self.output.hardlink_to(self.replay)
                return report
            with patch.object(module, function, side_effect=introduce_alias), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(module.main([str(self.inputs), '-o', str(self.output)]), 2)
            self.output.unlink()
        self.assertEqual((self.replay.read_bytes(), truth.read_bytes()), before)
        self.assertFalse((self.inputs / 'good.5.vgr').exists())
