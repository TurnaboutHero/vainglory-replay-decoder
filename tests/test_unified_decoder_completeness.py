import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from vg.core.native_stats import ClockAudit

from vg.core.unified_decoder import (
    DecodedPlayer,
    UnifiedDecoder,
    _assess_core_completeness,
)


class TestCoreCompletenessPolicy(unittest.TestCase):
    def test_high_ratio_with_stale_crystal_is_unknown(self) -> None:
        complete, reason = _assess_core_completeness(100, 100, 69.0, 100.0)
        self.assertIsNone(complete)
        self.assertIn("coverage", reason.lower())

    def test_high_ratio_without_crystal_is_unknown(self) -> None:
        complete, _ = _assess_core_completeness(100, 100, None, 100.0)
        self.assertIsNone(complete)

    def test_aligned_terminal_candidate_is_unknown(self) -> None:
        complete, reason = _assess_core_completeness(100, 100, 100.0, 100.0)
        self.assertIsNone(complete)
        self.assertIn("terminal", reason.lower())

    def test_missing_timing_is_unknown(self) -> None:
        complete, reason = _assess_core_completeness(None, 100, 100.0, 100.0)
        self.assertIsNone(complete)
        self.assertIn("insufficient", reason.lower())

    def test_low_ratio_is_incomplete_even_with_crystal(self) -> None:
        complete, reason = _assess_core_completeness(89, 100, 89.0, 89.0)
        self.assertFalse(complete)
        self.assertIn("falls short", reason.lower())

    def test_exact_ratio_boundary_is_not_terminal_proof(self) -> None:
        complete, _ = _assess_core_completeness(90, 100, 90.0, 90.0)
        self.assertIsNone(complete)

    def test_exact_crystal_alignment_boundary_is_not_terminal_proof(self) -> None:
        complete, _ = _assess_core_completeness(100, 100, 70.0, 100.0)
        self.assertIsNone(complete)

    def test_decode_aggregates_reason_into_public_json(self) -> None:
        parsed = {
            "replay_name": "synthetic",
            "replay_file": "synthetic.0.vgr",
            "match_info": {"mode": "5v5", "map_name": "Sovereign's Rise", "team_size": 5},
            "teams": {"left": [{"name": "p"}], "right": []},
        }
        player = DecodedPlayer("p", "left", "Alpha", 1, 0)
        with patch("vg.core.unified_decoder.VGRParser") as parser_cls, patch.object(
            UnifiedDecoder, "_make_player", return_value=player
        ), patch.object(
            UnifiedDecoder, "_load_frames", return_value=[(index, b"x") for index in range(100)]
        ), patch.object(
            UnifiedDecoder, "_scan_kda_events", return_value=(None, {}, {}, 1000.0)
        ), patch.object(
            UnifiedDecoder, "_detect_crystal_death", return_value=(700.0, 2000)
        ), patch("vg.decoder_v2.player_state.decode_player_state", return_value=SimpleNamespace(
            players=(), field_status={'kda': SimpleNamespace(status='unknown', reason='fixture')},
            as_of_game_time=None, to_dict=lambda: {},
        )), patch("vg.core.stat_evidence.inspect_native_clock", return_value=ClockAudit(True, "accepted", "valid")), patch("vg.core.unified_decoder.WinLossDetector") as win_cls:
            parser_cls.return_value.parse.return_value = parsed
            win_cls.return_value.detect_winner.return_value = None
            result = UnifiedDecoder("synthetic.0.vgr").decode()

        self.assertIsNone(result.data_complete)
        self.assertEqual(
            result.completeness_reason,
            "Recording coverage alone does not confirm a terminal match end.",
        )
        self.assertEqual(json.loads(result.to_json())["completeness_reason"], result.completeness_reason)


if __name__ == "__main__":
    unittest.main()
