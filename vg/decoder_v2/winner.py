"""Conservative winner decoding scaffold for decoder_v2."""

from __future__ import annotations

from .kda import decode_kda_from_replay
from .models import CompletenessStatus, WinnerExtractionResult


def decode_winner_from_replay(replay_file: str) -> WinnerExtractionResult:
    """Retain kill totals without treating them as terminal winner evidence."""
    kda_result = decode_kda_from_replay(replay_file)
    if (not kda_result.accepted or kda_result.scope != "final"
            or kda_result.assessment.status != CompletenessStatus.COMPLETE_CONFIRMED):
        return WinnerExtractionResult(
            accepted=False,
            reason=f"Winner export is withheld: {kda_result.reason}",
            assessment=kda_result.assessment,
            duration_estimate=kda_result.duration_estimate,
            winner=None,
            left_kills=None,
            right_kills=None,
        )

    left_kills = sum(player.kills for player in kda_result.players if player.team == "left")
    right_kills = sum(player.kills for player in kda_result.players if player.team == "right")
    return WinnerExtractionResult(
        accepted=False,
        reason="Winner export is withheld: kill totals do not establish a terminal winner or its team mapping.",
        assessment=kda_result.assessment,
        duration_estimate=kda_result.duration_estimate,
        winner=None,
        left_kills=left_kills,
        right_kills=right_kills,
    )
