import unittest
from pathlib import Path
from unittest.mock import patch

from vg.core.stored_paths import stored_parent, stored_path_key
from vg.decoder_v2.minion_series_profile import build_minion_series_profile


class TestProductStoredPaths(unittest.TestCase):
    def test_stored_paths_happy(self) -> None:
        equivalent = [
            (r"C:\Series\Set\match", "c:/series/set/match", r"C:\Series\Set"),
            (r"\\Server\Share\Set\match", "//server/share/set/match", r"\\Server\Share\Set"),
            ("/series/set/match", "/series/set/other", "/series/set"),
            ("series/set/match", "series/set/other", "series/set"),
        ]
        for first, second, display in equivalent:
            with self.subTest(first=first):
                self.assertEqual(stored_parent(first), display)
                self.assertEqual(stored_path_key(stored_parent(first)), stored_path_key(stored_parent(second)))

        rows = []
        for directory in (r"C:\Replays\SeriesA\1", "c:/replays/seriesa/2"):
            rows.append({
                "fixture_directory": directory, "residual_vs_0e": 0,
                "solo_subfamily_total": 5, "mixed_subfamily_total": 1,
                "solo_excess_vs_peer_mean": 0, "mixed_excess_vs_peer_mean": 0,
            })
        with patch("vg.decoder_v2.minion_series_profile.build_minion_outlier_risk_report", return_value={"all_rows": rows}):
            report = build_minion_series_profile("truth.json")
        self.assertEqual(len(report["rows"]), 1)
        self.assertEqual(report["rows"][0]["player_rows"], 2)
        self.assertEqual(report["rows"][0]["series"], r"C:\Replays\SeriesA")
        self.assertNotEqual(stored_path_key("/Series"), stored_path_key("/series"))

    def test_stored_paths_failure(self) -> None:
        with patch.object(Path, "resolve", side_effect=AssertionError("metadata must not resolve")), patch.object(Path, "open", side_effect=AssertionError("metadata must not open")):
            for path, expected in (("", ""), ("/", "/"), ("C:\\", "C:\\"), ("C:match", "C:"), ("match", ".")):
                with self.subTest(path=path):
                    self.assertEqual(stored_parent(path), expected)
            self.assertEqual(stored_path_key(stored_parent("Z:/remote/series/match")), "z:/remote/series")
            self.assertEqual(stored_parent("\\\\Server\\Share\\"), "\\\\Server\\Share\\")


if __name__ == "__main__":
    unittest.main()
