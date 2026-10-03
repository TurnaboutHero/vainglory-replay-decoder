"""Native statistic decoding with distinct final and capture scopes."""

from __future__ import annotations

import math
from typing import Optional

from vg.core.native_stats import GameTime, read_native_stats
from vg.core.stat_evidence import final_field_reason, inspect_replay_evidence
from vg.core.vgr_parser import VGRParser
from vg.core.unified_decoder import _le_to_be

from .completeness import extract_replay_signals, load_frames
from .duration import estimate_duration_from_signals
from .models import KDAExtractionResult, KDAPlayerSummary


def decode_kda_from_replay(replay_file: str, *, at_game_time: Optional[float] = None) -> KDAExtractionResult:
    """Export observed native statistics for an explicit capture; finals require separate validation."""
    signals = extract_replay_signals(replay_file)
    duration_estimate = estimate_duration_from_signals(signals)
    assessment = duration_estimate.assessment
    scope = 'capture' if at_game_time is not None else 'final'

    def reject(reason):
        return KDAExtractionResult(False, reason, assessment, duration_estimate,
                                   scope=scope, at_game_time=at_game_time)

    if at_game_time is not None and (not math.isfinite(at_game_time) or at_game_time < 0):
        return reject('Invalid game time: use a finite non-negative number of seconds.')
    if signals.native_clock_valid is False:
        return reject(assessment.reason)
    if at_game_time is None:
        return reject(final_field_reason('K/D/A'))
    if signals.recording_valid is False:
        return reject(signals.recording_reason or 'Recording framing or section sequence is invalid.')

    parser = VGRParser(replay_file, auto_truth=False)
    parsed = parser.parse()
    ordered_players = []
    for team_label in ('left', 'right'):
        for player in parsed['teams'][team_label]:
            entity_id = player.get('entity_id')
            if not isinstance(entity_id, int) or isinstance(entity_id, bool) or not 0 < entity_id <= 0xFFFF:
                return reject('Missing player entity ID; native statistics are withheld.')
            ordered_players.append((_le_to_be(entity_id), team_label, player))
    if not ordered_players:
        return reject('No player identities; native statistics are withheld.')
    ids = [eid for eid, _, _ in ordered_players]
    if len(ids) != len(set(ids)):
        return reject('Duplicate player entity IDs; native statistics are withheld.')
    frames = load_frames(replay_file)
    evidence = inspect_replay_evidence(frames)
    if not evidence.recording_valid:
        return reject(evidence.recording_reason)
    if not evidence.native_clock.valid:
        return reject(evidence.native_clock.reason)
    replay_scope = evidence.replay_scope
    if signals.replay_scope is not None and signals.replay_scope != replay_scope:
        return reject('Recording changed between evidence and capture extraction.')
    result = read_native_stats(frames, set(ids), cutoff=GameTime(at_game_time))
    if not result.valid:
        return reject(f'Native statistics withheld ({result.status}): {result.reason}')
    by_id = {player.entity_id: player for player in result.players}
    if any(eid not in by_id for eid, _, _ in ordered_players):
        return reject('Native statistics do not cover every player.')
    players = tuple(KDAPlayerSummary(
        player['name'], player.get('team', team), player.get('hero_name', 'Unknown'),
        by_id[eid].kills, by_id[eid].deaths, by_id[eid].assists, by_id[eid].minion_kills,
        entity_id_be=eid, replay_scope=replay_scope,
    ) for eid, team, player in ordered_players)
    return KDAExtractionResult(
        True, 'Native statistics exported for the requested capture.',
        assessment, duration_estimate, players, scope, at_game_time, result.as_of_game_time,
        replay_scope=replay_scope,
    )
