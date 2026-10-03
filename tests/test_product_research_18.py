import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report, write_replay
from vg.decoder_v2 import minion_outlier_compare, minion_outlier_risk_report, minion_pattern_family_compare, minion_series_peer_compare, minion_series_profile, hackedglory_minion_validation, hackedglory_xp_level_validation


class ProductSeriesResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        replays = [write_replay(self.root / folder, 'match') for folder in ('SeriesA/1', 'SeriesA/2', 'Incomplete')]
        self.sources = []
        entity = int.from_bytes((57093).to_bytes(2, 'little'), 'big')
        for replay in replays:
            metadata = replay.read_bytes()
            framed = struct.pack('>fIH', 0.0, len(metadata) + 2, 0x1234) + metadata
            for action, value in ((0x02, 20.0),) * 12 + ((0x0E, 1.0), (0x06, 3.0), (0x08, 0.6), (0x03, 1.0)):
                payload = struct.pack('>IfBBI', entity, value, action, 0, 0)
                framed += struct.pack('>fIH', 1.0, len(payload) + 2, 0x041D) + payload
            for number in (0, 1):
                path = replay.with_name(f'match.{number}.vgr')
                path.write_bytes(framed)
                self.sources.append(path)
        self.truth = self.root / 'truth.json'
        rows = [{'replay_name': f'match-{i}', 'replay_file': str(replay),
                 'players': {'PlayerOne': {'minion_kills': 3}}} for i, replay in enumerate(replays)]
        rows.append({'replay_name': 'unused', 'replay_file': str(self.root / 'Incomplete' / 'absent.0.vgr')})
        self.truth.write_text(json.dumps({'matches': rows}))
        self.sources.insert(0, self.truth)
        self.cases = []
        for module in (minion_outlier_compare, minion_outlier_risk_report,
                       minion_pattern_family_compare, minion_series_peer_compare,
                       minion_series_profile, hackedglory_minion_validation,
                       hackedglory_xp_level_validation):
            args = ('--truth', str(self.truth))
            if module in (minion_outlier_compare, minion_pattern_family_compare, minion_series_peer_compare):
                args += ('--replay-name', 'match-0')
            count = 3 if module is hackedglory_xp_level_validation else 2
            sources = (self.truth, *self.sources[1:1 + count * 2])
            self.cases.append(ReportCase(module, 'build_' + module.__name__.split('.')[-1],
                                         args, sources, tuple(replays[:count]), self.root / 'report.json'))

    def test_research_happy(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_happy(self, case)
        relative = json.loads(self.truth.read_text())
        for row in relative['matches']:
            row['replay_file'] = str(Path(row['replay_file']).relative_to(self.root))
        self.truth.write_text(json.dumps(relative))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='relative_truth'):
                self.assertEqual(run_report(case).code, 0)
        rows = json.loads(self.truth.read_text())['matches']
        keyed = {row['replay_name']: {key: value for key, value in row.items() if key != 'replay_name'} for row in rows}
        self.truth.write_text(json.dumps({'matches': keyed}))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='keyed_truth'):
                result = run_report(case)
                self.assertEqual(result.code, 0, result.stderr)
        self.truth.write_text(json.dumps({'matches': rows[:1]}))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='no_baseline'):
                self.assertEqual(run_report(case).code, 0)

    def test_research_failure(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_failures(self, case)
        original = self.truth.read_bytes()
        for data in (b'{', b'[]', b'{"matches":[{"players":[]}]}', b'{"matches":[{"replay_name":"x"}]}'):
            self.truth.write_bytes(data)
            for case in self.cases:
                with self.subTest(module=case.module.__name__, malformed=data), patch(f'{case.module.__name__}.{case.builder}') as builder:
                    self.assertEqual(run_report(case, case.output).code, 2)
                    builder.assert_not_called()
        rows = json.loads(original)['matches']
        for selected in ('absent', 'match-0'):
            changed = json.loads(original)
            if selected == 'match-0':
                changed['matches'][1]['replay_name'] = selected
            self.truth.write_text(json.dumps(changed))
            for case in (self.cases[0], self.cases[2], self.cases[3]):
                args = (*case.args[:-1], selected)
                invalid = ReportCase(case.module, case.builder, args, case.sources, case.replays, case.output)
                with self.subTest(module=case.module.__name__, selector=selected), patch(f'{case.module.__name__}.{case.builder}') as builder:
                    result = run_report(invalid, invalid.output)
                    self.assertEqual(result.code, 2)
                    self.assertIn(str(self.truth), result.stderr)
                    if selected == 'match-0':
                        self.assertIn('scoped choices', result.stderr)
                        self.assertIn(rows[0]['replay_file'], result.stderr)
                        self.assertIn(rows[1]['replay_file'], result.stderr)
                    builder.assert_not_called()
        self.truth.write_bytes(original)
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='missing_complete_replay'):
                missing = json.loads(original)
                missing['matches'][1]['replay_file'] = str(self.root / 'gone' / 'missing.0.vgr')
                self.truth.write_text(json.dumps(missing))
                result = run_report(case, case.output)
                self.assertEqual(result.code, 2)
                self.assertEqual(result.stdout, '')
        self.truth.write_bytes(original)
        foreign = json.loads(original)
        foreign['matches'][0]['replay_file'] = 'Z:/foreign/SeriesA/match.0.vgr'
        self.truth.write_text(json.dumps(foreign))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='foreign_consumed_replay'):
                result = run_report(case, case.output)
                self.assertEqual(result.code, 2)
                self.assertEqual(result.stdout, '')
                foreign_path = Path('Z:/foreign/SeriesA/match.0.vgr')
                self.assertIn(str(foreign_path), result.stderr)
                self.assertIn('input_missing' if foreign_path.is_absolute() else 'truth_unreadable', result.stderr)
        self.truth.write_bytes(original)

    def test_cli_subprocess(self) -> None:
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.sources}
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                command = [sys.executable, '-B', '-m', case.module.__name__, *case.args]
                stdout = subprocess.run(command, capture_output=True, text=True, check=False)
                self.assertEqual(stdout.returncode, 0, stdout.stderr)
                json.loads(stdout.stdout)
                saved = subprocess.run([*command, '-o', str(case.output)], capture_output=True, text=True, check=False)
                self.assertEqual(saved.returncode, 0, saved.stderr)
                self.assertIn('saved', saved.stdout)
                json.loads(case.output.read_text())
                rejected = subprocess.run([*command, '-o', str(self.truth)], capture_output=True, text=True, check=False)
                self.assertEqual(rejected.returncode, 2)
                self.assertEqual(rejected.stdout, '')
                self.assertIn(str(self.truth), rejected.stderr)
                print(json.dumps({'module': case.module.__name__, 'scenario': 'subprocess',
                                  'stdout_exit': stdout.returncode, 'saved_exit': saved.returncode,
                                  'alias_exit': rejected.returncode}))
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.sources}
        self.assertEqual(before, after)
        print(json.dumps({'scenario': 'subprocess_source_preservation', 'before': before, 'after': after}))

    def test_xp_limit_consumed_inputs(self) -> None:
        case = self.cases[-1]
        limited = ReportCase(case.module, case.builder, (*case.args, '--limit', '1'),
                             case.sources[:5], case.replays[:2], case.output)
        assert_report_happy(self, limited)
        assert_report_failures(self, limited)
        unused = case.replays[2].with_name('match.999.vgr')
        result = run_report(limited, unused)
        self.assertEqual(result.code, 0, result.stderr)
        unused.unlink()
        self.assertEqual(run_report(case, unused).code, 2)

    def test_xp_without_minion_truth(self) -> None:
        document = json.loads(self.truth.read_text())
        for row in document['matches']:
            row.pop('players', None)
        self.truth.write_text(json.dumps(document))
        result = run_report(self.cases[-1])
        self.assertEqual(result.code, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['assessment']['xp_total_export_status'], 'not_safe')


    def test_windows_paths_are_literal_in_ambiguity_diagnostics(self) -> None:
        # Given duplicate selectors whose scoped paths contain Windows separators.
        paths = (r'Z:\Team A\one\match.0.vgr', r'Z:\Team B\two\match.0.vgr')
        self.truth.write_text(json.dumps({'matches': [
            {'replay_name': 'match-0', 'replay_file': path, 'players': {}} for path in paths]}))
        before = self.truth.read_bytes()
        # When real command preflight rejects the ambiguous name before decoding.
        for case in (self.cases[0], self.cases[2], self.cases[3]):
            case.output.write_bytes(b'prior report')
            with self.subTest(module=case.module.__name__):
                result = run_report(case, case.output)
                # Then each complete candidate path can be copied without unescaping.
                self.assertEqual(result.code, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn(str(self.truth), result.stderr)
                self.assertIn('truth_ambiguous', result.stderr)
                for path in paths:
                    self.assertIn(path, result.stderr)
                self.assertEqual(case.output.read_bytes(), b'prior report')
                self.assertEqual(self.truth.read_bytes(), before)
                print(json.dumps({'module': case.module.__name__, 'scenario': 'literal_windows_candidates',
                                  'exit_code': result.code, 'stderr': result.stderr, 'paths': paths}))


if __name__ == '__main__':
    unittest.main()
