import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report, write_replay
from vg.decoder_v2 import minion_acceptance_gate_research, minion_policy_candidates, minion_policy_cross_validation, minion_policy_stability_audit, minion_policy_validation, minion_series_bucket_rule_research, minion_window_fixture_research, minion_window_research
from vg.decoder_v2.minion_policy import MINION_POLICY_CHOICES


class ProductPolicyResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.replays = [write_replay(self.root / folder, 'match') for folder in ('a', 'b', 'Incomplete')]
        self.sections = []
        entity = int.from_bytes((57093).to_bytes(2, 'little'), 'big')
        for replay in self.replays:
            metadata = replay.read_bytes()
            framed = struct.pack('>fIH', 0.0, len(metadata) + 2, 0x1234) + metadata
            for action, value in ((0x02, 20.0),) * 12 + ((0x0E, 1.0), (0x06, 3.0), (0x08, 0.6), (0x03, 1.0)):
                payload = struct.pack('>IfBBI', entity, value, action, 0, 0)
                framed += struct.pack('>fIH', 1.0, len(payload) + 2, 0x041D) + payload
            for number in (0, 1):
                path = replay.with_name(f'match.{number}.vgr')
                path.write_bytes(framed)
                self.sections.append(path)
        self.truth = self.root / 'truth.json'
        rows = [{'replay_name': f'match-{i}', 'replay_file': str(replay),
                 'players': {'PlayerOne': {'minion_kills': 2 if i == 1 else 3}}}
                for i, replay in enumerate(self.replays)]
        self.truth.write_text(json.dumps({'matches': rows}))
        self.output = self.root / 'report.json'
        complete_sources = (self.truth, *self.sections[:4])
        modules = ((minion_acceptance_gate_research, 'build_minion_acceptance_gate_research'),
                   (minion_policy_candidates, 'build_minion_policy_candidates'),
                   (minion_policy_cross_validation, 'build_minion_policy_cross_validation'),
                   (minion_policy_stability_audit, 'build_minion_policy_stability_audit'),
                   (minion_policy_validation, 'validate_minion_policy'),
                   (minion_series_bucket_rule_research, 'build_minion_series_bucket_rule_research'),
                   (minion_window_fixture_research, 'build_minion_window_fixture_report'))
        self.cases = []
        for module, builder in modules:
            args = ('--truth', str(self.truth))
            sources, replays = complete_sources, tuple(self.replays[:2])
            if module is minion_policy_validation:
                args += ('--policy', 'nonfinals-baseline-0e')
            if module is minion_policy_stability_audit:
                sources, replays = (self.truth, *self.sections), tuple(self.replays)
            self.cases.append(ReportCase(module, builder, args, sources, replays, self.output))
        self.window = ReportCase(minion_window_research, 'build_minion_window_report',
                                 (str(self.replays[0]), '--truth', str(self.truth)),
                                 (self.truth, *self.sections[:2]), (self.replays[0],), self.output)
        self.cases.append(self.window)
        self.window_without_truth = ReportCase(minion_window_research, 'build_minion_window_report',
                                              (str(self.replays[0]),), tuple(self.sections[:2]),
                                              (self.replays[0],), self.output)
        self.disabled = ReportCase(minion_policy_validation, 'validate_minion_policy',
                                   ('--truth', str(self.truth)), (self.truth,), (), self.output)

    def test_research_happy(self) -> None:
        for case in (*self.cases, self.window_without_truth, self.disabled):
            with self.subTest(module=case.module.__name__, args=case.args):
                assert_report_happy(self, case)
                report = json.loads(case.output.read_text())
                self.assertIn(report['research_status'], ('research_only', 'unavailable'))
                self.assertIn('research_coverage', report)
        validation = minion_policy_validation.validate_minion_policy(str(self.truth), 'nonfinals-baseline-0e')
        self.assertEqual(validation['player_rows'], 2)
        self.assertEqual(validation['accepted_exact'], 1)
        self.assertEqual(validation['accepted_error'], 1)
        window = json.loads(run_report(self.window).stdout)
        self.assertEqual(window['players'][0]['residual_vs_0e'], 1)
        self.assertEqual(window['research_coverage']['truth_player_rows'], 1)
        fixture = json.loads(run_report(self.cases[6]).stdout)
        self.assertEqual(fixture['research_status'], 'research_only')
        self.assertEqual(fixture['research_coverage']['comparison_samples'], 2)
        cross = json.loads(run_report(self.cases[2]).stdout)
        self.assertEqual(cross['leave_one_series_out']['summary']['research_status'], 'unavailable')
        self.assertEqual(cross['leave_one_series_out']['folds'][0]['research_coverage']['training_rows'], 0)
        self.assertEqual(cross['leave_one_replay_out']['summary']['available_folds'], 2)

        original = self.truth.read_bytes()
        document = json.loads(original)
        document['matches'][1]['replay_name'] = 'match-0'
        document['matches'][1]['replay_file'] = str(self.root / 'unread' / 'missing.0.vgr')
        self.truth.write_text(json.dumps(document))
        self.assertEqual(json.loads(run_report(self.window).stdout)['players'][0]['residual_vs_0e'], 1)
        unknown = json.loads(original)
        unknown['matches'][1]['players']['PlayerOne'] = {}
        self.truth.write_text(json.dumps(unknown))
        fixture = json.loads(run_report(self.cases[6]).stdout)
        self.assertEqual(fixture['research_status'], 'unavailable')
        self.assertEqual(fixture['research_coverage']['comparison_samples'], 0)
        unknown = json.loads(original)
        for row in unknown['matches']:
            del row['players']
        self.truth.write_text(json.dumps(unknown))
        for case in self.cases:
            result = run_report(case)
            self.assertEqual(result.code, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['research_status'], 'unavailable')
        self.truth.write_text(json.dumps({'matches': []}))
        for case in self.cases:
            result = run_report(case)
            self.assertEqual(result.code, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['research_status'], 'unavailable')
            self.assertTrue(report['research_reason'])
        self.truth.write_bytes(original)
        for replay in self.sections:
            replay.unlink()
        with patch('vg.decoder_v2.minion_policy.collect_player_minion_policy_context') as read_replay:
            result = run_report(self.disabled)
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['research_status'], 'unavailable')
        read_replay.assert_not_called()
        self.truth.write_text(json.dumps({'players': {}}))
        self.assertEqual(run_report(self.disabled).code, 0)

    def test_research_failure(self) -> None:
        for case in (*self.cases, self.window_without_truth, self.disabled):
            with self.subTest(module=case.module.__name__, args=case.args):
                assert_report_failures(self, case)
        original = self.truth.read_bytes()
        for data in (b'{', b'[]', b'{"matches":[{"players":[]}]}'):
            self.truth.write_bytes(data)
            for case in (*self.cases, self.disabled):
                with self.subTest(module=case.module.__name__, malformed=data), patch(f'{case.module.__name__}.{case.builder}') as builder:
                    result = run_report(case, case.output)
                    self.assertEqual(result.code, 2)
                    self.assertIn(str(self.truth), result.stderr)
                    builder.assert_not_called()
        self.truth.write_bytes(original)
        self.truth.unlink()
        for case in (*self.cases, self.disabled):
            with patch(f'{case.module.__name__}.{case.builder}') as builder:
                result = run_report(case, case.output)
                self.assertEqual(result.code, 2)
                self.assertIn(str(self.truth), result.stderr)
                builder.assert_not_called()
        self.truth.write_bytes(original)
        for policy in MINION_POLICY_CHOICES:
            case = ReportCase(self.disabled.module, self.disabled.builder,
                              (*self.disabled.args, '--policy', policy),
                              self.disabled.sources, self.disabled.replays, self.output)
            self.assertEqual(run_report(case).code, 0)
        invalid = ReportCase(self.disabled.module, self.disabled.builder,
                             (*self.disabled.args, '--policy', 'unknown'),
                             self.disabled.sources, self.disabled.replays, self.output)
        with self.assertRaises(SystemExit) as caught:
            run_report(invalid)
        self.assertEqual(caught.exception.code, 2)
        self.sections[0].unlink()
        self.sections[1].unlink()
        for case in self.cases:
            result = run_report(case, case.output)
            self.assertEqual(result.code, 2, case.module.__name__)
            self.assertEqual(result.stdout, '')
        self.assertEqual(run_report(self.window_without_truth, self.output).code, 2)


if __name__ == '__main__':
    unittest.main()
