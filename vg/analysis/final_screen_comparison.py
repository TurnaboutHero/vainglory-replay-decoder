import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re

from vg.core.native_stats import read_native_stats
from vg.core.replay_output import validate_replay_output, write_replay_output
from vg.core.stat_evidence import frame_scope, inspect_replay_evidence
from vg.core.unified_decoder import _le_to_be
from vg.core.vgr_parser import VGRParser
from vg.decoder_v2.completeness import load_frames


FIELDS = {'kills': 'kills', 'deaths': 'deaths', 'assists': 'assists', 'cs': 'minion_kills'}


def _count(value, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f'{label} must be a non-negative integer')
    return value


def _validate_observation(observation: dict) -> None:
    if not isinstance(observation, dict):
        raise ValueError('Observation must be an object')
    if observation.get('schema_version') != 'vg.final-screen-observation.v1':
        raise ValueError('Unsupported observation schema_version')
    if observation.get('capture_stage') != 'final_screen':
        raise ValueError('Observation must identify a final_screen capture')
    for key, pattern in [('replay_scope', r'sha256:[0-9a-f]{64}'),
                         ('screenshot_sha256', r'[0-9a-f]{64}')]:
        value = observation.get(key)
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ValueError(f'Missing or invalid {key}')
    provenance = observation.get('provenance')
    if not isinstance(provenance, dict) or provenance.get('transcription_method') != 'manual_visual':
        raise ValueError('provenance must identify manual_visual transcription')
    if not isinstance(provenance.get('observed_at_utc'), str) or not provenance['observed_at_utc'].strip():
        raise ValueError('provenance requires observed_at_utc')
    mapping = observation.get('screen_side_to_team')
    if (not isinstance(mapping, dict) or set(mapping) != {'blue', 'orange'}
            or not all(isinstance(value, str) for value in mapping.values())
            or set(mapping.values()) != {'left', 'right'}):
        raise ValueError('screen_side_to_team must map blue/orange to distinct left/right teams')
    winner = observation.get('winner_screen_side')
    if 'winner_screen_side' not in observation or (winner is not None and (
            not isinstance(winner, str) or winner not in mapping)):
        raise ValueError('winner_screen_side must be an observed side or explicit null')
    if 'result_display' in observation and (
            not isinstance(observation['result_display'], str) or not observation['result_display'].strip()):
        raise ValueError('result_display must retain nonempty displayed text')
    duration = observation.get('duration_display')
    if not isinstance(duration, str) or not re.fullmatch(r'[0-9]+:[0-5][0-9]', duration):
        raise ValueError('duration_display must retain the displayed minutes:seconds')
    rows = observation.get('players')
    if not isinstance(rows, list) or not rows:
        raise ValueError('players must contain the complete observed roster')
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Player observation must be an object')
        eid = _count(row.get('entity_id_be'), 'entity_id_be')
        if not 0 < eid <= 0xFFFF or eid in ids:
            raise ValueError('Player entity IDs must be unique nonzero uint16 values')
        ids.add(eid)
        if not isinstance(row.get('screen_side'), str) or row['screen_side'] not in mapping:
            raise ValueError('Player screen_side is missing or unsupported')
        for key in FIELDS:
            _count(row.get(key), key)
        gold = row.get('gold_display')
        if not isinstance(gold, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?k?', gold):
            raise ValueError('gold_display must retain the displayed number')


def compare_final_screen(replay_file: str, observation_file: str, screenshot_file: str) -> dict:
    replay = Path(replay_file)
    if not replay.is_file() or not replay.name.endswith('.0.vgr'):
        raise ValueError('Use one explicit .0.vgr replay file')
    raw_observation = Path(observation_file).read_bytes()
    observation = json.loads(raw_observation)
    _validate_observation(observation)
    screenshot_hash = hashlib.sha256(Path(screenshot_file).read_bytes()).hexdigest()
    if screenshot_hash != observation['screenshot_sha256']:
        raise ValueError('screenshot hash does not match the observation')
    frames = load_frames(replay_file)
    evidence = inspect_replay_evidence(frames)
    if not evidence.recording_valid or not evidence.native_clock.valid:
        raise ValueError(f'Recording invalid: {evidence.recording_reason}; {evidence.native_clock.reason}')
    if evidence.replay_scope != observation['replay_scope']:
        raise ValueError('Replay scope does not match the observation')
    parsed = VGRParser(replay_file, auto_truth=False).parse()
    roster = {}
    for side in ('left', 'right'):
        for player in parsed['teams'][side]:
            entity = _count(player.get('entity_id'), 'Recorded entity_id')
            if not 0 < entity <= 0xFFFF:
                raise ValueError('Recorded player entity ID is invalid')
            eid = _le_to_be(entity)
            if eid in roster:
                raise ValueError('Recorded player entity IDs are duplicated')
            roster[eid] = (side, player)
    if frame_scope(load_frames(replay_file)) != evidence.replay_scope:
        raise ValueError('Replay changed during roster extraction')
    if set(roster) != {row['entity_id_be'] for row in observation['players']}:
        raise ValueError('Observed player IDs do not cover the exact recorded roster')
    mapping = observation['screen_side_to_team']
    for row in observation['players']:
        side, player = roster[row['entity_id_be']]
        if mapping[row['screen_side']] != side:
            raise ValueError('Observed screen side contradicts the recorded roster mapping')
        if 'name' in row and row['name'] != player['name']:
            raise ValueError('Observed name does not match its recorded entity')
    native = read_native_stats(frames, roster)
    by_id = {player.entity_id: player for player in native.players} if native.valid else {}
    players = []
    matched = 0
    for row in observation['players']:
        eid = row['entity_id_be']
        fields = {}
        for observed_key, native_key in FIELDS.items():
            actual = getattr(by_id[eid], native_key) if eid in by_id else None
            status = 'unavailable' if actual is None else ('matched' if actual == row[observed_key] else 'mismatch')
            matched += status == 'matched'
            fields[observed_key] = {'native': actual, 'observed': row[observed_key], 'status': status}
        players.append({'entity_id_be': eid, 'name': roster[eid][1]['name'],
                        'team': roster[eid][0], 'screen_side': row['screen_side'], 'fields': fields,
                        'gold': {'display': row['gold_display'], 'exact_value': None, 'status': 'observation_only'}})
    total = len(players) * len(FIELDS)
    status = 'unavailable' if not native.valid else ('matched' if matched == total else 'mismatch')
    winner_side = observation['winner_screen_side']
    return {'schema_version': 'vg.final-screen-comparison.v1',
            'scope': 'recording_specific_final_screen', 'accepted_for_index': False,
            'comparison_status': status, 'matched_fields': matched, 'compared_fields': total,
            'replay_scope': evidence.replay_scope, 'screenshot_sha256': screenshot_hash,
            'observation_sha256': hashlib.sha256(raw_observation).hexdigest(),
            'provenance': observation['provenance'],
            'transcription_status': 'caller_asserted_manual_visual',
            'native_status': native.status, 'native_reason': native.reason,
            'as_of_game_time': native.as_of_game_time, 'recording_evidence': asdict(evidence),
            'players': players,
            'observed_winner': {'screen_side': winner_side, 'recorded_team': mapping.get(winner_side),
                                'status': 'observation_only' if winner_side is not None else 'not_observed'},
            'observed_result': {'display': observation.get('result_display'),
                                'status': 'observation_only' if 'result_display' in observation else 'not_observed'},
            'observed_duration': {'display': observation['duration_display'], 'native_seconds': None, 'status': 'observation_only'}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Compare native EOF counters with one hash-bound, manually transcribed final screen.')
    parser.add_argument('replay', help='Explicit numbered .0.vgr file')
    parser.add_argument('--observation', required=True)
    parser.add_argument('--screenshot', required=True)
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)
    try:
        if args.output:
            output = Path(args.output)
            validate_replay_output(Path(args.replay), output)
            for path in (Path(args.observation), Path(args.screenshot)):
                if output.resolve() == path.resolve() or (output.exists() and output.samefile(path)):
                    raise ValueError('Output aliases an observation or screenshot input')
        result = compare_final_screen(args.replay, args.observation, args.screenshot)
        payload = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
        if args.output:
            write_replay_output(Path(args.replay), Path(args.output), payload)
        else:
            print(payload, end='')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0 if result['comparison_status'] == 'matched' else 1


if __name__ == '__main__':
    raise SystemExit(main())
