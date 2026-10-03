import unittest
from dataclasses import replace
from unittest.mock import patch

from vg.decoder_v2.kda import decode_kda_from_replay
from vg.decoder_v2.models import (
    CompletenessAssessment,
    CompletenessStatus,
    DurationEstimate,
    KDAExtractionResult,
    KDAPlayerSummary,
    ReplaySignalSummary,
)
from vg.decoder_v2.winner import decode_winner_from_replay


def incomplete_result() -> KDAExtractionResult:
    signals = ReplaySignalSummary(
        replay_name="match",
        replay_file="match.0.vgr",
        frame_count=85,
        max_frame_index=84,
        crystal_ts=None,
        max_kill_ts=471.5,
        max_player_death_ts=473.4,
        max_death_header_ts=846.3,
        max_item_ts=849.9,
    )
    assessment = CompletenessAssessment(
        status=CompletenessStatus.INCOMPLETE_CONFIRMED,
        reason="incomplete",
        signals=signals,
    )
    duration = DurationEstimate(
        estimate_seconds=None,
        source="unknown",
        assessment=assessment,
    )
    return KDAExtractionResult(
        accepted=False,
        reason="incomplete",
        assessment=assessment,
        duration_estimate=duration,
        players=(),
    )


class TestDecoderV2Stats(unittest.TestCase):
    def test_complete_kill_lead_does_not_establish_winner(self) -> None:
        base = incomplete_result()
        assessment = replace(base.assessment, status=CompletenessStatus.COMPLETE_CONFIRMED)
        for left, right in ((10, 20), (20, 10), (10, 10)):
            with self.subTest(left=left, right=right):
                kda = replace(
                    base, accepted=True, assessment=assessment,
                    duration_estimate=replace(base.duration_estimate, assessment=assessment),
                    players=(KDAPlayerSummary("a", "left", "Alpha", left, 0, 0, 0),
                             KDAPlayerSummary("b", "right", "Beta", right, 0, 0, 0)),
                )
                with patch("vg.decoder_v2.winner.decode_kda_from_replay", return_value=kda):
                    result = decode_winner_from_replay("match.0.vgr")
                self.assertFalse(result.accepted)
                self.assertIsNone(result.winner)
                self.assertEqual((result.left_kills, result.right_kills), (left, right))

    def test_decode_winner_rejects_incomplete_replay(self) -> None:
        with patch("vg.decoder_v2.winner.decode_kda_from_replay", return_value=incomplete_result()):
            result = decode_winner_from_replay("match.0.vgr")

        self.assertFalse(result.accepted)
        self.assertIsNone(result.winner)
        self.assertEqual(result.assessment.status, CompletenessStatus.INCOMPLETE_CONFIRMED)

    def test_decode_kda_rejects_incomplete_replay(self) -> None:
        with patch("vg.decoder_v2.kda.extract_replay_signals") as extract_signals:
            signals = ReplaySignalSummary(
                replay_name="match",
                replay_file="match.0.vgr",
                frame_count=85,
                max_frame_index=84,
                crystal_ts=None,
                max_kill_ts=471.5,
                max_player_death_ts=473.4,
                max_death_header_ts=846.3,
                max_item_ts=849.9,
            )
            extract_signals.return_value = signals

            result = decode_kda_from_replay("match.0.vgr")

        self.assertFalse(result.accepted)
        self.assertEqual(result.assessment.status, CompletenessStatus.INCOMPLETE_CONFIRMED)
        self.assertEqual(result.players, ())


if __name__ == "__main__":
    unittest.main()
