import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report, write_replay
from vg.decoder_v2 import action02_hero_affinity, action02_sharing_profile, action02_subfamily_summary, action02_value_context_profile, residual_signal_research


class ProductActionResearch(unittest.TestCase):
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
            for action, value in ((0x02, 20.0), (0x0E, 1.0), (0x06, 3.0), (0x08, 0.6), (0x03, 1.0)):
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
        self.cases = [ReportCase(module, builder, ('--truth', str(self.truth)), tuple(self.sources), tuple(replays), self.root / 'report.json')
                      for module, builder in ((action02_hero_affinity, 'build_action02_hero_affinity'),
                                              (action02_sharing_profile, 'build_action02_sharing_profile'),
                                              (action02_subfamily_summary, 'build_action02_subfamily_summary'),
                                              (action02_value_context_profile, 'build_action02_value_context_profile'),
                                              (residual_signal_research, 'build_residual_signal_report'))]

    def test_research_happy(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_happy(self, case)
        sharing = action02_sharing_profile.build_action02_sharing_profile(str(self.truth))
        self.assertEqual(sharing['rows'][0]['value'], 20.0)
        self.assertEqual(sharing['rows'][0]['match_count'], 2)
        self.assertEqual(sharing['rows'][0]['event_count'], 4)
        self.assertEqual(sharing['rows'][0]['shared_cluster_rate'], 0)
        residual = residual_signal_research.build_residual_signal_report(str(self.truth))
        self.assertEqual(residual['rows'], 2)
        self.assertEqual(residual['positive_residual_distribution'], [1, 1])

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
        self.truth.write_bytes(original)
        self.sources[-1].unlink()
        self.sources[-2].unlink()
        for case in self.cases:
            self.assertEqual(run_report(case, case.output).code, 2)


if __name__ == '__main__':
    unittest.main()
