import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tests.test_product_duration_provenance import replay_bytes
from vg.core.unified_decoder import DecodedMatch, DecodedPlayer
from vg.core.export_matches import match_to_csv_rows, match_to_summary_row, export_single
from vg.analysis.batch_report import generate_report, print_report
from vg.analysis.truth_comparison import compare_player_stats, compare_all


def player(name='known', **kwargs):
    values = dict(kills=4, deaths=2, assists=6, minion_kills=12)
    values.update(kwargs)
    return DecodedPlayer(name, 'left', 'Caine', 1, 1500, **values)


def match(*players):
    return DecodedMatch('sample', 'sample.0.vgr', '5v5', 'Rise', 5,
                        left_team=list(players))


class NullableStatsExportsTests(unittest.TestCase):
    def test_unverified_winner_is_not_a_loss_or_zero_win_rate(self):
        decoded = match(player())
        self.assertIsNone(match_to_csv_rows(decoded)[0]['is_winner'])
        self.assertIsNone(generate_report([decoded])['hero_stats'][0]['win_rate'])
        decoded.winner = 'left'
        self.assertEqual(match_to_csv_rows(decoded)[0]['is_winner'],1)
        self.assertEqual(generate_report([decoded])['hero_stats'][0]['win_rate'],100.)

    def test_missing_gold_is_not_a_partial_total_or_average(self):
        decoded = match(player(gold_earned=5600), player('unknown',gold_earned=None))
        self.assertIsNone(match_to_summary_row(decoded)['left_gold'])
        report = generate_report([decoded])
        self.assertIsNone(report['hero_stats'][0]['avg_gold'])
        self.assertIsNone(report['match_stats']['avg_gold_per_player'])
        self.assertEqual(match_to_summary_row(match(player(gold_earned=5600)))['left_gold'],5600)

    def test_known_stats_unchanged(self):
        decoded = match(player())
        self.assertEqual(match_to_csv_rows(decoded)[0]['kda_ratio'], 5.0)
        self.assertEqual(match_to_summary_row(decoded)['left_kills'], 4)
        report = generate_report([decoded])
        self.assertEqual(report['hero_stats'][0]['avg_assists'], 6.0)
        self.assertEqual(report['match_stats']['avg_kills_per_match'], 4.0)

    def test_missing_components_are_not_partial_totals(self):
        decoded = match(player(), player('unknown', kills=None, deaths=None,
                                         assists=None, minion_kills=None))
        row = match_to_csv_rows(decoded)[1]
        self.assertIsNone(row['kda_ratio'])
        self.assertIsNone(match_to_summary_row(decoded)['left_kills'])
        self.assertIsNone(match_to_summary_row(decoded)['left_deaths'])
        report = generate_report([decoded])
        for key in ['avg_kills', 'avg_deaths', 'avg_assists', 'avg_minion_kills']:
            self.assertIsNone(report['hero_stats'][0][key])
        self.assertIsNone(report['match_stats']['avg_kills_per_match'])
        output = io.StringIO()
        with redirect_stdout(output):
            print_report(report)
        self.assertIn('N/A', output.getvalue())

    def test_missing_assists_do_not_make_ratio(self):
        self.assertIsNone(match_to_csv_rows(match(player(assists=None)))[0]['kda_ratio'])

    def test_real_exports_preserve_null_and_blank(self):
        decoded = match(player(kills=None, deaths=None, assists=None, minion_kills=None,
                               truth_kills=0, truth_deaths=0))
        with tempfile.TemporaryDirectory() as tmp:
            replay = Path(tmp) / 'sample.0.vgr'
            replay.write_bytes(replay_bytes())
            json_path, csv_path = export_single(replay, decoded, str(Path(tmp) / 'out.json'))
            self.assertIsNone(json.loads(json_path.read_text())['left_team'][0]['kills'])
            with csv_path.open(encoding='utf-8-sig', newline='') as stream:
                row = next(csv.DictReader(stream))
            for key in ['kills', 'deaths', 'assists', 'minion_kills', 'kda_ratio', 'kill_match', 'death_match']:
                self.assertEqual(row[key], '')

    def test_accuracy_excludes_unknown_values_and_reports_them(self):
        decoded = match(player(), player('unknown', kills=None, deaths=None,
                                         assists=None, minion_kills=None))
        truth_players = {p.name: dict(hero_name='Caine', team='left', kills=4,
                                      deaths=2, assists=6, minion_kills=12)
                         for p in decoded.all_players}
        with tempfile.TemporaryDirectory() as tmp:
            truth_path = Path(tmp) / 'truth.json'
            truth_path.write_text(json.dumps({'matches': [
                {'replay_file': 'sample.0.vgr', 'players': truth_players}]}))
            output = io.StringIO()
            # Substitute only the replay IO boundary, keeping real comparisons/output.
            with patch('vg.analysis.truth_comparison.UnifiedDecoder.decode', return_value=decoded), \
                    patch('vg.analysis.truth_comparison.UnifiedDecoder.__init__', return_value=None), \
                    redirect_stdout(output):
                compare_all(str(truth_path))
        self.assertIn('Kills:             1/1 (100.0%)', output.getvalue())
        self.assertIn('kill=1, death=1, assist=1, mk=1', output.getvalue())
        self.assertIn('kill: unavailable', output.getvalue())

    def test_truth_comparison_distinguishes_unknown_and_difference(self):
        result = compare_player_stats(player(kills=None, assists=None),
                                      dict(kills=0, deaths=3, assists=0, minion_kills=12))
        self.assertIsNone(result['kill']['match'])
        self.assertIsNone(result['kill']['diff'])
        self.assertIsNone(result['assist']['match'])
        self.assertEqual(result['death']['diff'], -1)
        self.assertFalse(result['death']['match'])
        self.assertTrue(result['mk']['match'])


if __name__ == '__main__':
    unittest.main()
