import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report
from tests.test_product_duration_provenance import replay_bytes
from vg.decoder_v2 import completeness_audit, completeness_outlier_compare, kda_postgame_audit, validation
from vg.decoder_v2.report_inputs import load_research_truth


class ProductFoundationResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.base = self.root / 'replays'
        self.base.mkdir()
        self.replays = []
        rows = []
        for number in range(9):
            replay = self.base / f'match{number}.0.vgr'
            replay.write_bytes(replay_bytes())
            self.replays.append(replay)
            rows.append({'replay_name': f'display{number}', 'replay_file': f'replays/{replay.name}',
                         'match_info': {'duration_seconds': 0},
                         'players': {'PlayerOne': {'hero_name': 'Inara', 'kills': 0, 'deaths': 0,
                                                   'assists': 0, 'minion_kills': 0}}})
        self.truth = self.root / 'truth.json'
        self.truth.write_text(json.dumps({'matches': rows}))
        self.cases = [
            ReportCase(validation, 'build_foundation_report', ('--truth', str(self.truth)),
                       (self.truth, *self.replays), tuple(self.replays), self.root / 'report.json'),
            ReportCase(completeness_audit, 'build_completeness_audit', ('--base', str(self.base)),
                       tuple(self.replays), tuple(self.replays), self.root / 'report.json'),
            ReportCase(completeness_outlier_compare, 'build_completeness_outlier_compare',
                       ('--base', str(self.base), '--replay-name', 'match0'),
                       tuple(self.replays), tuple(self.replays), self.root / 'report.json'),
            ReportCase(kda_postgame_audit, 'build_kda_postgame_audit', ('--truth', str(self.truth)),
                       (self.truth, *self.replays), tuple(self.replays), self.root / 'report.json'),
        ]
        inventory = self.root / 'inventory'
        inventory.mkdir()
        extra_replay = inventory / 'extra.0.vgr'
        extra_replay.write_bytes(replay_bytes())
        manifest = inventory / 'replayManifest-extra.txt'
        manifest.write_text('metadata-only fixture')
        image = inventory / 'result.png'
        image.write_bytes(b'metadata only, not decoded pixels')
        self.cases.append(ReportCase(validation, 'build_foundation_report',
                          ('--truth', str(self.truth), '--base', str(inventory)),
                          (self.truth, *self.replays, extra_replay, manifest, image),
                          (*self.replays, extra_replay), self.root / 'report.json'))

    def test_research_happy(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_happy(self, case)
        report = json.loads(run_report(self.cases[0]).stdout)
        self.assertIsNone(report['truth_inventory'])
        self.assertEqual(report['player_block_validation']['matches_total'], 9)
        self.assertEqual(len(report['minion_candidate_probes']), 2)
        self.assertEqual(len(report['current_decoder_validation']['match_results']), 9)
        explicit = validation.main
        from contextlib import redirect_stderr, redirect_stdout
        import io
        output, diagnostics = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(diagnostics):
            code = explicit(['--truth', str(self.truth), '--base', str(self.base)])
        self.assertEqual(code, 0, diagnostics.getvalue())
        self.assertEqual(json.loads(output.getvalue())['truth_inventory']['total_families'], 9)
        empty = self.root / 'empty'
        empty.mkdir()
        self.assertEqual(completeness_audit.build_completeness_audit(str(empty))['status'], 'empty')
        self.truth.write_text('{"matches":[{"replay_name":"metadata"}]}')
        self.assertEqual(load_research_truth(self.truth)[0]['players'], {})

    def test_research_failure(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_failures(self, case)
        original = self.truth.read_bytes()
        for payload in ('{', '[]', '{"matches":[{"players":[]}]}', '{"matches":[{"replay_name":"x"}]}'):
            self.truth.write_text(payload)
            for case in (self.cases[0], self.cases[3]):
                with patch(f'{case.module.__name__}.{case.builder}') as builder:
                    self.assertEqual(run_report(case, case.output).code, 2)
                    builder.assert_not_called()
        self.truth.write_bytes(original)
        missing = self.root / 'missing'
        for module, builder, args in (
            (validation, 'build_foundation_report', ('--truth', str(self.truth), '--base', str(missing))),
            (completeness_audit, 'build_completeness_audit', ('--base', str(missing))),
            (completeness_outlier_compare, 'build_completeness_outlier_compare',
             ('--base', str(self.base), '--replay-name', 'missing'))):
            case = ReportCase(module, builder, args, (), (), self.root / 'report.json')
            self.assertEqual(run_report(case).code, 2)
        duplicate = self.base / 'nested'
        duplicate.mkdir()
        (duplicate / 'match0.0.vgr').write_bytes(replay_bytes())
        self.assertEqual(run_report(self.cases[2]).code, 2)
