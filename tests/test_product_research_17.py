import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report, write_replay
from vg.decoder_v2 import minion_action_cluster_compare, minion_action_provenance, minion_action_relation_compare, minion_action_self_vs_team, minion_action_value_compare, minion_hero_compare, minion_hero_outlier_score


class ProductComparisonResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        replays = [write_replay(self.root / folder, 'match') for folder in ('a', 'b')]
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
        self.cases = [ReportCase(module, 'build_' + module.__name__.split('.')[-1],
                                 ('--truth', str(self.truth), '--replay-name', 'match-0'),
                                 tuple(self.sources), tuple(replays), self.root / 'report.json')
                      for module in (minion_action_cluster_compare, minion_action_provenance,
                                     minion_action_relation_compare, minion_action_self_vs_team,
                                     minion_action_value_compare, minion_hero_compare, minion_hero_outlier_score)]

    def test_research_happy(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_happy(self, case)
        hero = minion_hero_compare.build_minion_hero_compare(str(self.truth), 'match-0')
        self.assertEqual(hero['rows'][0]['residual_vs_0e'], 1)
        self.assertIn('0x02@20.0', hero['selected_patterns'])
        self.assertEqual(hero['rows'][0]['same_hero_peer_count'], 1)
        self.assertEqual(hero['rows'][0]['same_hero_peers'][0]['replay_name'], 'match-1')
        relative = json.loads(self.truth.read_text())
        for row in relative['matches']:
            row['replay_file'] = str(Path(row['replay_file']).relative_to(self.root))
        self.truth.write_text(json.dumps(relative))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='relative_truth'):
                self.assertEqual(run_report(case).code, 0)
        rows = json.loads(self.truth.read_text())['matches']
        self.truth.write_text(json.dumps({'matches': rows[:1]}))
        for case in self.cases:
            with self.subTest(module=case.module.__name__, scenario='no_baseline'):
                self.assertEqual(run_report(case).code, 0)
        hero = minion_hero_compare.build_minion_hero_compare(str(self.truth), 'match-0')
        self.assertEqual(hero['rows'][0]['same_hero_peer_count'], 0)

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
            for case in self.cases:
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
        duplicate_peers = json.loads(original)
        duplicate_peers['matches'].insert(2, dict(duplicate_peers['matches'][1]))
        duplicate_peers['matches'][2]['replay_file'] = str(self.root / 'c' / 'match.0.vgr')
        self.truth.write_text(json.dumps(duplicate_peers))
        relation = self.cases[2]
        with patch(f'{relation.module.__name__}.{relation.builder}') as builder:
            result = run_report(relation, relation.output)
            self.assertEqual(result.code, 2)
            self.assertIn('ambiguous peer', result.stderr)
            builder.assert_not_called()
        self.truth.write_bytes(original)
        missing_value = json.loads(original)
        missing_value['matches'][0]['players']['PlayerOne'] = {}
        self.truth.write_text(json.dumps(missing_value))
        for case in (self.cases[2], *self.cases[4:]):
            result = run_report(case, case.output)
            self.assertEqual(result.code, 2)
            self.assertIn('requires minion_kills', result.stderr)
        self.truth.write_bytes(original)
        self.sources[-1].unlink()
        self.sources[-2].unlink()
        for case in self.cases:
            self.assertEqual(run_report(case, case.output).code, 2)


if __name__ == '__main__':
    unittest.main()
