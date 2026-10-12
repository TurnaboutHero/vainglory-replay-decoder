from dataclasses import asdict
import math
import re
import struct


MODEL = 'vg.client-display.windows_2026_10_11.v1'
CLIENT_SHA256 = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'


class DisplayEvidenceError(ValueError):
    pass


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def gold_label(value):
    """Candidate for one formatter call, never an EOF cache reconstruction."""
    return format(f32(value * f32(.001)), '.1f') + 'k'


def _number(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0)


def _float_bits(value):
    if not isinstance(value, dict) or not _number(value.get('value')):
        raise DisplayEvidenceError('invalid display observation float')
    try:
        encoded = struct.pack('<f', value['value'])
    except (OverflowError, struct.error) as error:
        raise DisplayEvidenceError('display observation float32 overflow') from error
    bits = struct.unpack('<I', encoded)[0]
    if struct.unpack('<f', encoded)[0] != value['value']:
        raise DisplayEvidenceError('display observation value is not exact float32')
    if type(value.get('bits')) is not int or value['bits'] != bits:
        raise DisplayEvidenceError('display observation float bits disagree')
    return value['value']


def _hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _observation(receipt, replay_scope, query, players, scope):
    if not isinstance(receipt, dict) or receipt.get('schema_version') != 'vg.terminal-display-observation.v1':
        raise DisplayEvidenceError('unsupported display observation schema')
    if scope != 'recorded_end' or not query.valid:
        raise DisplayEvidenceError('terminal display observations require supported recorded-end state')
    if receipt.get('client_sha256') != CLIENT_SHA256:
        raise DisplayEvidenceError('display observation client is outside the documented model')
    if not all(_hash(receipt.get(k)) for k in ('probe_sha256', 'guard_manifest_sha256')):
        raise DisplayEvidenceError('display observation requires collector hashes')
    cases = receipt.get('cases')
    if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
        raise DisplayEvidenceError('invalid display observation cases')
    cases = [c for c in cases if c.get('replay_scope') == replay_scope]
    if len(cases) != 1:
        raise DisplayEvidenceError('display observation must match exactly one replay scope')
    case = cases[0]
    if (case.get('trace_complete') is not True
            or case.get('source_sections_rehashed') != len(query.frames)
            or not all(_hash(case.get(k)) for k in ('trace_sha256', 'screenshot_sha256'))):
        raise DisplayEvidenceError('display observation is incomplete')
    counts = case.get('event_counts', {})
    if not isinstance(counts, dict) or any(counts.get(k) != 1 for k in ('terminal', 'final')):
        raise DisplayEvidenceError('display observation requires one terminal and final callback')
    rows = case.get('gold')
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise DisplayEvidenceError('invalid display observation gold rows')
    ids = [r.get('actor_id') for r in rows]
    if (any(type(i) is not int for i in ids) or len(ids) != len(set(ids))
            or set(ids) != {p.native_actor_id for p in players}):
        raise DisplayEvidenceError('display observation actor set differs from recorded state')
    by_actor = {r['actor_id']: r for r in rows}
    for p in players:
        row = by_actor[p.native_actor_id]
        if (p.field_status['net_worth'].status != 'supported'
                or _float_bits(row.get('native7')) != p.net_worth):
            raise DisplayEvidenceError('display observation raw gold differs from recorded state')
        value = _float_bits(row.get('format_input'))
        if row.get('label') != gold_label(value):
            raise DisplayEvidenceError('display observation label differs from formatter model')
        seqs = [row.get(k) for k in ('last_format_row_seq', 'format_seq', 'label_seq')]
        if any(type(n) is not int or n <= 0 for n in seqs) or not seqs[0] < seqs[1] < seqs[2]:
            raise DisplayEvidenceError('display observation gold call order is invalid')
        previous = row.get('last_format_previous_cache')
        if type(previous) is not int or int(f32(value * f32(.01))) <= previous:
            raise DisplayEvidenceError('display observation did not advance the cache bucket')
    clock = case.get('clock')
    if not isinstance(clock, dict) or clock.get('decoder_eof_seconds') != query.audit.last_game_time:
        raise DisplayEvidenceError('display observation recorded clock differs')
    if _float_bits(clock.get('last_anchor')) != query.frames[-1].anchor_game_time:
        raise DisplayEvidenceError('display observation last anchor differs')
    terminal = _float_bits(clock.get('terminal_clock'))
    formatted = _float_bits(clock.get('time_format_input'))
    if terminal != formatted:
        raise DisplayEvidenceError('terminal clock differs from time formatter input')
    seqs = [clock.get(k) for k in ('terminal_seq', 'final_seq', 'time_format_seq')]
    if (any(type(n) is not int or n <= 0 for n in seqs)
            or not (seqs[0] < seqs[1] < seqs[2] or seqs[2] < seqs[0] < seqs[1])):
        raise DisplayEvidenceError('display observation time call order is invalid')
    seconds = int(formatted)
    if clock.get('screenshot_duration_display') != f'{seconds // 60}:{seconds % 60:02d}':
        raise DisplayEvidenceError('time display differs from formatter input')
    return case, by_actor


def build_display_values(query, players, replay_scope, scope, *, runtime_evidence=None, playback_speed=None):
    if playback_speed is not None and (not _number(playback_speed) or playback_speed <= 0):
        raise DisplayEvidenceError('playback_speed must be finite and positive')
    case, observed = (None, {}) if runtime_evidence is None else _observation(
        runtime_evidence, replay_scope, query, players, scope)
    provenance = {'model': MODEL, 'replay_scope': replay_scope, 'scope': scope,
                  'record_boundary': list(query.record_boundary) if query.record_boundary else None,
                  'accepted_for_definitive_analysis': False}
    supplied_source = None if case is None else {
        'trace_sha256': case['trace_sha256'], 'screenshot_sha256': case['screenshot_sha256'],
        'client_sha256': runtime_evidence['client_sha256'],
        'probe_sha256': runtime_evidence['probe_sha256'],
        'guard_manifest_sha256': runtime_evidence['guard_manifest_sha256'],
        'authentication': 'supplied_receipt_not_independently_authenticated'}
    gold = []
    for player in players:
        raw = player.net_worth
        supported = player.field_status['net_worth'].status == 'supported' and _number(raw)
        row = observed.get(player.native_actor_id)
        gold.append({'native_actor_id': player.native_actor_id,
            'raw': {'value': raw, 'source': asdict(player.field_status['net_worth'])},
            'observed': None if row is None else {
                'status': 'supplied_runtime_observation', 'label': row['label'],
                'formatter_input': row['format_input'], 'format_seq': row['format_seq'],
                'label_seq': row['label_seq'], 'source': supplied_source},
            'reconstructed': None if row is None else {
                'status': 'reproduced_from_observed_formatter_input',
                'label': gold_label(row['format_input']['value']),
                'cache_bucket': int(f32(row['format_input']['value'] * f32(.01))),
                'format_seq': row['format_seq'], 'source': supplied_source},
            'direct_raw_candidate': None if not supported else {
                'status': 'estimated', 'label': gold_label(raw),
                'reason': 'Formats current resource 7; does not reconstruct cached game text.'},
            'reason': 'Gold refresh occurs only on an increasing 100-gold cache bucket; '
                      'EOF resources do not identify the last UI refresh.', **provenance})
    raw_time = query.applied_game_time if query.valid and query.audit.game_time_mapping_valid else None
    estimate = None
    if playback_speed is not None and raw_time is not None:
        selected = [(frame, record) for frame in query.frames for record in frame.records
                    if query.includes(frame, record)]
        anchors = [(frame, record) for frame, record in selected if record.opcode == 0x046f]
        if anchors:
            frame, anchor = anchors[-1]
            interval = selected[-1][1].timestamp - anchor.timestamp
            estimate = {'status': 'estimated', 'seconds': frame.anchor_game_time + interval * playback_speed,
                'last_anchor_seconds': frame.anchor_game_time, 'record_interval_seconds': interval,
                'playback_speed': playback_speed,
                'reason': 'Assumes constant speed and an open clock gate; actual frame deltas, '
                          'pauses, seeks and per-tick float32 rounding are unavailable.'}
    clock = None if case is None else case['clock']
    time = {'raw': {'seconds': raw_time, 'source': 'native_anchor_plus_record_interval',
        'status': 'recorded' if raw_time is not None else 'unknown', 'reason': query.reason,
        'last_anchor_seconds': next((frame.anchor_game_time for frame in query.frames
            if query.record_boundary is not None and frame.number == query.record_boundary[0]), None)
            if query.valid else None},
        'observed': None if clock is None else {
            'status': 'supplied_runtime_observation', 'label': clock['screenshot_duration_display'],
            'seconds': clock['time_format_input']['value'], 'format_seq': clock['time_format_seq'],
            'terminal_seq': clock['terminal_seq'], 'source': supplied_source},
        'reconstructed': None if clock is None else {
            'status': 'reproduced_from_observed_formatter_input',
            'label': clock['screenshot_duration_display'], 'source': supplied_source,
            'format_seq': clock['time_format_seq']},
        'playback_clock_estimate': estimate,
        'reason': 'Anchor resets and playback-speed accumulation determine the UI clock; '
                  'recorded time and client display are not certified match duration.', **provenance}
    return {'schema_version': MODEL, 'gold': gold, 'time': time,
            'server_final_result_certified': False}
