"""Nullable match rows and spreadsheet-safe CSV serialization."""

import csv
import io
from collections.abc import Iterable, Mapping
from typing import Dict, List

from vg.core.unified_decoder import DecodedMatch

CsvCell = str | int | float | bool | None
CsvRow = Mapping[str, CsvCell]

def _complete_sum(values):
    """A total is unavailable if any of its components is unavailable."""
    values = list(values)
    return None if not values or any(value is None for value in values) else sum(values)


def _analysis_columns(match: DecodedMatch) -> Dict:
    decision = match.definitive_analysis
    return {'definitive_analysis_eligible': decision['eligible'],
            'definitive_analysis_status': decision['status'],
            'definitive_analysis_reason_codes': ' | '.join(decision['reason_codes']),
            'definitive_analysis_reason': decision['reason']}


def match_to_csv_rows(match: DecodedMatch, match_idx: int = 0, input_id: str = '') -> List[Dict]:
    """Convert a decoded match to flat CSV rows (one row per player)."""
    rows = []
    for player in match.all_players:
        kda_ratio = None
        if all(value is not None for value in (player.kills, player.deaths, player.assists)):
            kda_ratio = round((player.kills + player.assists) / max(player.deaths, 1), 2)
        is_winner = (None if match.winner is None or player.team is None
                     else int(player.team == match.winner))
        row = {
            'match_idx': match_idx,
            'input_id': input_id,
            'replay_name': match.replay_name,
            'game_mode': match.game_mode,
            'map': match.map_name,
            'team_size': match.team_size,
            'duration_s': match.duration_seconds,
            'duration_status': match.duration_provenance['status'],
            'duration_source': match.duration_provenance['source'],
            'duration_reason': match.duration_provenance['reason'],
            'duration_accepted_for_index': match.duration_provenance['accepted_for_index'],
            'native_stats_status': match.native_stats_status,
            'final_validation_status': match.final_validation_status,
            'final_stats_reason': match.final_stats_reason,
            **_analysis_columns(match),
            'winner': match.winner or '',
            'player_name': player.name,
            'native_actor_id': player.native_actor_id,
            'team_id': player.team_id,
            'team': player.team,
            'is_winner': is_winner,
            'hero': player.hero_name,
            'kills': player.kills,
            'deaths': player.deaths,
            'assists': player.assists if player.assists is not None else '',
            'kda_ratio': kda_ratio,
            'minion_kills': player.minion_kills,
            'jungle_kills': player.jungle_kills,
            'gold_spent': player.gold_spent,
            'gold_earned': player.gold_earned,
            'gold_status': player.gold_status,
            'gold_balance': player.gold_balance,
            'net_worth': player.net_worth,
            'state_scope': player.state_scope,
            'as_of_game_time': player.as_of_game_time,
            'state_section': (player.record_boundary or {}).get('section'),
            'state_record_offset': (player.record_boundary or {}).get('record_offset'),
            'replay_scope': player.replay_scope,
            'items': ' | '.join(player.items) if player.items else '',
            'item_count': len(player.items) if player.items is not None else None,
        }
        if player.truth_kills is not None:
            row['truth_kills'] = player.truth_kills
            row['kill_match'] = None if player.kills is None else int(player.kills == player.truth_kills)
        if player.truth_deaths is not None:
            row['truth_deaths'] = player.truth_deaths
            row['death_match'] = None if player.deaths is None else int(player.deaths == player.truth_deaths)
        rows.append(row)
    return rows


def match_to_summary_row(match: DecodedMatch, match_idx: int = 0, input_id: str = '') -> Dict:
    """Convert a decoded match to a single summary row."""
    left_kills = _complete_sum(p.kills for p in match.left_team)
    right_kills = _complete_sum(p.kills for p in match.right_team)
    left_deaths = _complete_sum(p.deaths for p in match.left_team)
    right_deaths = _complete_sum(p.deaths for p in match.right_team)
    left_gold = _complete_sum(p.gold_earned for p in match.left_team)
    right_gold = _complete_sum(p.gold_earned for p in match.right_team)

    obj_counts = {}
    for evt in match.objective_events:
        obj_counts[evt.event_type] = obj_counts.get(evt.event_type, 0) + 1

    return {
        'match_idx': match_idx,
            'input_id': input_id,
        'replay_name': match.replay_name,
        'game_mode': match.game_mode,
        'map': match.map_name,
        'team_size': match.team_size,
        'duration_s': match.duration_seconds,
            'duration_status': match.duration_provenance['status'],
            'duration_source': match.duration_provenance['source'],
            'duration_reason': match.duration_provenance['reason'],
            'duration_accepted_for_index': match.duration_provenance['accepted_for_index'],
            'native_stats_status': match.native_stats_status,
            'final_validation_status': match.final_validation_status,
            'final_stats_reason': match.final_stats_reason,
            **_analysis_columns(match),
        'winner': match.winner or '',
        'left_kills': left_kills,
        'right_kills': right_kills,
        'left_deaths': left_deaths,
        'right_deaths': right_deaths,
        'left_gold': left_gold,
        'right_gold': right_gold,
        'gold_mine_captures': obj_counts.get('GOLD_MINE_CAPTURE', 0),
        'kraken_deaths': obj_counts.get('KRAKEN_DEATH', 0),
        'kraken_waves': obj_counts.get('KRAKEN_WAVE', 0),
        'crystal_death_ts': match.crystal_death_ts,
        'total_frames': match.total_frames,
        'total_players': len(match.all_players),
        **{f'{stat}_known_players': sum(getattr(p, stat) is not None for p in match.all_players)
           for stat in ('kills', 'deaths', 'assists', 'minion_kills', 'gold_earned')},
    }


def _csv_cell(value: CsvCell) -> CsvCell:
    if isinstance(value, str) and (value.lstrip().startswith(('=', '+', '-', '@'))
                                  or any(char in value for char in '\t\r\n')):
        return "'" + value
    return value


def serialize_csv(rows: Iterable[CsvRow], fields: Iterable[str] = ()) -> bytes:
    rows = list(rows)
    fieldnames = list(dict.fromkeys([*fields, *(key for row in rows for key in row)]))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows({key: _csv_cell(value) for key, value in row.items()} for row in rows)
    return stream.getvalue().encode('utf-8-sig')
