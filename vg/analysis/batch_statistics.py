"""Conservative nullable statistics and their terminal presentation."""

from collections import Counter, defaultdict
from typing import TypedDict
from vg.core.export_rows import _complete_sum
from vg.core.unified_decoder import DecodedMatch


class StatisticsReport(TypedDict):
    match_stats: dict
    duration_provenance_coverage: dict
    objective_aggregation_scope: str
    game_mode_distribution: dict
    duration_distribution: dict
    objective_stats: dict
    hero_stats: list[dict]


def _duration_text(seconds: int | None) -> str:
    return 'N/A' if seconds is None else f'{seconds // 60}m {seconds % 60}s'


def generate_report(matches: list[DecodedMatch]) -> StatisticsReport:
    # === Hero Statistics ===
    hero_stats = defaultdict(lambda: {
        'picks': 0, 'wins': 0, 'kills': 0, 'deaths': 0,
        'assists': 0, 'minion_kills': 0, 'gold_earned': 0,
        'known_samples': Counter(),
    })

    for match in matches:
        for player in match.all_players:
            h = hero_stats[player.hero_name]
            h['picks'] += 1
            h['known_samples']['wins'] += match.winner is not None
            for metric in ('kills', 'deaths', 'assists', 'minion_kills', 'gold_earned'):
                h['known_samples'][metric] += getattr(player, metric) is not None
            if match.winner is None:
                h['wins'] = None
            elif h['wins'] is not None and player.team == match.winner:
                h['wins'] += 1
            for metric in ('kills', 'deaths', 'assists', 'minion_kills'):
                h[metric] = _complete_sum((h[metric], getattr(player, metric)))
            h['gold_earned'] = _complete_sum((h['gold_earned'], player.gold_earned))

    total_matches = len(matches)
    hero_table = []
    for name, s in sorted(hero_stats.items(), key=lambda x: -x[1]['picks']):
        n = s['picks']
        hero_table.append({
            'hero': name,
            'picks': n,
            'total_samples': n,
            'known_samples': dict(s['known_samples']),
            'pick_rate': round(n / total_matches * 100, 1),
            'win_rate': round(s['wins'] / n * 100, 1) if n and s['wins'] is not None else None,
            'avg_kills': round(s['kills'] / n, 1) if s['kills'] is not None else None,
            'avg_deaths': round(s['deaths'] / n, 1) if s['deaths'] is not None else None,
            'avg_assists': round(s['assists'] / n, 1) if s['assists'] is not None else None,
            'avg_minion_kills': round(s['minion_kills'] / n, 1) if s['minion_kills'] is not None else None,
            'avg_gold': round(s['gold_earned'] / n) if s['gold_earned'] is not None else None,
        })

    # === Match Statistics ===
    durations = [m.duration_seconds for m in matches if m.duration_seconds is not None]
    all_players = [p for m in matches for p in m.all_players]
    total_kills = _complete_sum(p.kills for p in all_players)
    total_gold = _complete_sum(p.gold_earned for p in all_players)

    match_stats = {
        'total_matches': total_matches,
        'total_players': len(all_players),
        'total_kills': total_kills,
        'duration_known_samples': len(durations),
        'duration_total_samples': total_matches,
        'duration_aggregation_scope': 'observed_values_not_verified_final',
        'known_player_samples': {metric: sum(getattr(p, metric) is not None for p in all_players)
                                 for metric in ('kills', 'deaths', 'assists', 'minion_kills', 'gold_earned')},
        'avg_duration_s': round(sum(durations) / len(durations)) if durations else None,
        'min_duration_s': min(durations) if durations else None,
        'max_duration_s': max(durations) if durations else None,
        'avg_kills_per_match': round(total_kills / total_matches, 1) if total_kills is not None else None,
        'avg_gold_per_player': round(total_gold / len(all_players)) if all_players and total_gold is not None else None,
        'left_wins': sum(1 for m in matches if m.winner == 'left'),
        'right_wins': sum(1 for m in matches if m.winner == 'right'),
        'no_winner': sum(1 for m in matches if not m.winner),
    }

    # === Game Mode Distribution ===
    mode_dist = Counter(m.game_mode for m in matches)

    # === Duration Distribution ===
    buckets = {'<10min': 0, '10-15min': 0, '15-20min': 0,
               '20-25min': 0, '25-30min': 0, '>30min': 0}
    for d in durations:
        mins = d / 60
        if mins < 10:
            buckets['<10min'] += 1
        elif mins < 15:
            buckets['10-15min'] += 1
        elif mins < 20:
            buckets['15-20min'] += 1
        elif mins < 25:
            buckets['20-25min'] += 1
        elif mins < 30:
            buckets['25-30min'] += 1
        else:
            buckets['>30min'] += 1

    # === Objective Events ===
    obj_counts = Counter()
    for m in matches:
        for evt in m.objective_events:
            obj_counts[evt.event_type] += 1

    obj_stats = {
        'total_gold_mine_captures': obj_counts.get('GOLD_MINE_CAPTURE', 0),
        'total_kraken_deaths': obj_counts.get('KRAKEN_DEATH', 0),
        'total_kraken_waves': obj_counts.get('KRAKEN_WAVE', 0),
        'total_minion_waves': obj_counts.get('MINION_WAVE', 0),
        'avg_gold_mines_per_match': round(obj_counts.get('GOLD_MINE_CAPTURE', 0) / total_matches, 2) if total_matches else None,
        'avg_krakens_per_match': round(obj_counts.get('KRAKEN_DEATH', 0) / total_matches, 2) if total_matches else None,
    }

    return {
        'match_stats': match_stats,
        'duration_provenance_coverage': {status: {
            'total_samples': sum(m.duration_provenance['status'] == status for m in matches),
            'known_samples': len(values := [m.duration_seconds for m in matches
                if m.duration_provenance['status'] == status and m.duration_seconds is not None]),
            'avg_duration_s': round(sum(values) / len(values)) if values else None,
        } for status in ('unknown', 'estimated', 'supplied_truth')},
        'objective_aggregation_scope': 'historical_observed_events',
        'game_mode_distribution': dict(mode_dist),
        'duration_distribution': buckets,
        'objective_stats': obj_stats,
        'hero_stats': hero_table,
    }


def _stat_text(value, width):
    return f"{'N/A':>{width}}" if value is None else f"{value:{width}.1f}"


def print_report(report: StatisticsReport) -> None:
    ms = report.get('match_stats', {})
    print(f"\n{'='*70}")
    print(f"  BATCH REPLAY ANALYSIS REPORT")
    print(f"{'='*70}")

    print(f"\n  Match Statistics:")
    print(f"  {'─'*50}")
    print(f"  Total matches:       {ms.get('total_matches', 0)}")
    print(f"  Total players:       {ms.get('total_players', 0)}")
    print(f"  Avg duration (observed): {_duration_text(ms.get('avg_duration_s'))}")
    print(f"  Duration range:      {_duration_text(ms.get('min_duration_s'))} - {_duration_text(ms.get('max_duration_s'))}")
    print(f"  Avg kills/match:     {ms.get('avg_kills_per_match', 0)}")
    print(f"  Avg gold/player:     {ms.get('avg_gold_per_player', 0)}")
    print(f"  Winners (L/R/none):  {ms.get('left_wins',0)}/{ms.get('right_wins',0)}/{ms.get('no_winner',0)}")
    print(f"    (Note: left/right labels are non-deterministic)")

    print(f"\n  Game Mode Distribution:")
    print(f"  {'─'*50}")
    for mode, cnt in sorted(report.get('game_mode_distribution', {}).items(), key=lambda x: -x[1]):
        print(f"  {mode:30s} {cnt}")

    print(f"\n  Duration Distribution:")
    print(f"  {'─'*50}")
    for bucket, cnt in report.get('duration_distribution', {}).items():
        bar = '#' * cnt
        print(f"  {bucket:12s} {cnt:3d} {bar}")

    obj = report.get('objective_stats', {})
    print(f"\n  Objective Events (historical observed):")
    print(f"  {'─'*50}")
    print(f"  Gold Mine captures:  {obj.get('total_gold_mine_captures', 0)} (avg {obj.get('avg_gold_mines_per_match', 0)}/match)")
    print(f"  Kraken deaths:       {obj.get('total_kraken_deaths', 0)} (avg {obj.get('avg_krakens_per_match', 0)}/match)")
    print(f"  Kraken waves:        {obj.get('total_kraken_waves', 0)}")
    print(f"  Minion waves:        {obj.get('total_minion_waves', 0)}")

    heroes = report.get('hero_stats', [])
    print(f"\n  Hero Statistics (top 20):")
    print(f"  {'─'*80}")
    print(f"  {'Hero':20s} {'Picks':>5s} {'Pick%':>6s} {'Win%':>6s} {'K':>5s} {'D':>5s} {'A':>5s} {'MK':>6s} {'Gold':>7s}")
    print(f"  {'─'*80}")
    for h in heroes[:20]:
        print(f"  {h['hero']:20s} {h['picks']:5d} {h['pick_rate']:5.1f}% {_stat_text(h['win_rate'], 5)}%"
              f" {_stat_text(h['avg_kills'], 5)} {_stat_text(h['avg_deaths'], 5)} {_stat_text(h['avg_assists'], 5)}"
              f" {_stat_text(h['avg_minion_kills'], 6)} {_stat_text(h['avg_gold'], 7)}")

    if len(heroes) > 20:
        print(f"  ... and {len(heroes) - 20} more heroes")


