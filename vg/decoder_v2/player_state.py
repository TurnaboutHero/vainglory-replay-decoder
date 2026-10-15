"""Recording-scoped native player state, without final-match or truth overrides."""

from dataclasses import asdict, dataclass, field
import hashlib
import math
from pathlib import Path

from vg.core.definition_catalog import SUPPORTED_BUILD_SHA256
from vg.core.analysis_eligibility import evaluate_definitive_analysis
from vg.core.display_values import build_display_values
from vg.core.native_gold import read_native_gold
from vg.core.native_inventory import NativeInventoryItem, read_native_inventory
from vg.core.native_query import GameTime, RecordTime, select_native_query
from vg.core.native_roster import read_native_roster
from vg.core.recording_identity import RecordingIdentitySummary, summarize_recording_identity
from vg.core.native_stats import read_native_stats
from vg.core.replay_input import replay_sections, select_replay
from vg.core.replay_output import ReportInputs, ReplayOutputError
from vg.core.stat_evidence import end_match_requests, frame_scope


EVIDENCE_VERSION = 'native_player_state.windows_2026_10_04.v1'
REQUIRED_FIELDS = ('name', 'hero', 'kda', 'minion_kills', 'items', 'gold_balance', 'net_worth')


@dataclass(frozen=True, slots=True)
class RecordingClient:
    """Which client wrote the recording. Recordings carry no build identifier (2026-10-05 probe: dev,
    Steam and VGNA corpora share every early-record layout), so this is never verified in-band."""
    status: str = 'unverified'
    reason: str = ('recordings carry no client build identifier; support reflects record-layout '
                   'conformance of consumed opcodes and catalog provenance only')


@dataclass(frozen=True, slots=True)
class RecordBoundary:
    section: int
    record_offset: int


@dataclass(frozen=True, slots=True)
class StateSource:
    section: int
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class FieldProvenance:
    reader: str
    evidence_version: str
    replay_scope: str
    record_boundary: RecordBoundary | None
    native_fields: tuple[str, ...]
    source_records: tuple[RecordBoundary, ...] = ()
    resource_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class StateFieldStatus:
    status: str
    reason: str
    provenance: FieldProvenance | None = None


@dataclass(frozen=True, slots=True)
class StateItem:
    definition_id: int
    instance_id: int
    quantity: int
    name: str
    definition_name: str
    hud_hidden: bool


@dataclass(frozen=True, slots=True)
class PlayerState:
    native_actor_id: int
    name: str | None
    hero_name: str | None
    definition_index: int
    definition_name: str | None
    skin_hash: int
    team_id: int
    team: str | None
    kills: int | None
    deaths: int | None
    assists: int | None
    minion_kills: int | None
    items: tuple[StateItem, ...] | None
    native_items: tuple[StateItem, ...] | None
    inventory_capacity: int | None
    gold_balance: float | None
    net_worth: float | None
    field_status: dict[str, StateFieldStatus]

    spawn_skin_hash: int | None = None


@dataclass(frozen=True, slots=True)
class EndRequest:
    """Raw native ActionEndMatch (03f1) inside the query boundary; not a server or completed result."""
    record_boundary: RecordBoundary
    record_time: float
    winning_team_raw: int
    winning_team_id: int  # low byte, same space as PlayerState.team_id
    end_reason: int  # 2 takes the native surrender path; others are unclassified
    request_status: str


@dataclass(frozen=True, slots=True)
class PlayerStateResult:
    schema_version: str
    replay_name: str
    replay_file: str
    replay_scope: str
    scope: str
    query_clock: str
    requested_game_time: float | None
    requested_record_time: float | None
    as_of_game_time: float | None
    record_boundary: RecordBoundary | None
    support_status: str
    support_reason: str
    players: tuple[PlayerState, ...]
    field_status: dict[str, StateFieldStatus]
    source_files: tuple[StateSource, ...]
    first_game_time: float | None
    last_game_time: float | None
    evidence_version: str = EVIDENCE_VERSION
    # Reference build the native layouts and catalogs were derived from, not the recording's client.
    supported_client_sha256: str = SUPPORTED_BUILD_SHA256
    recording_client: RecordingClient = RecordingClient()
    end_requests: tuple[EndRequest, ...] = ()
    display_values: dict = field(default_factory=dict)
    player_selection: dict = field(default_factory=dict)
    query_timing: dict = field(default_factory=dict)
    recording_identity: RecordingIdentitySummary | None = None
    definitive_analysis: dict = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'definitive_analysis',
                           evaluate_definitive_analysis({'recording_client': asdict(self.recording_client)}))

    def to_dict(self) -> dict:
        result = asdict(self)
        result['definitive_analysis'] = evaluate_definitive_analysis(result)
        return result


def _boundary(value: tuple[int, int] | None) -> RecordBoundary | None:
    return RecordBoundary(*value) if value is not None else None


def _items(values: tuple[NativeInventoryItem, ...]) -> tuple[StateItem, ...]:
    return tuple(StateItem(item.definition_id, item.instance_id, item.quantity, item.name,
                           item.definition_name, item.hud_hidden) for item in values)


def _query_timing(query, sources) -> dict:
    applied = following = None
    for frame in query.frames:
        for record in frame.records:
            if (frame.number, record.offset) == query.record_boundary:
                applied = (frame, record)
            elif applied is not None:
                following = (frame, record)
                break
        if following is not None:
            break

    def observation(pair):
        if pair is None:
            return None
        frame, record = pair
        mapped = query.valid and query.audit.game_time_mapping_valid
        return {'record_boundary': asdict(RecordBoundary(frame.number, record.offset)),
                'record_time': record.timestamp,
                'projected_game_time': frame.game_time(record.timestamp) if mapped else None,
                'anchor_record_time': frame.anchor_record_time if mapped else None,
                'anchor_game_time': frame.anchor_game_time if mapped else None}

    selected, next_record = observation(applied), observation(following)
    requested = query.cutoff.seconds if query.cutoff is not None else None
    applied_time = (selected['record_time'] if isinstance(query.cutoff, RecordTime) else
                    selected['projected_game_time']) if selected else None
    return {
        'status': query.status, 'reason': query.reason,
        'clock_audit': {'status': query.audit.status, 'reason': query.audit.reason,
                        'game_time_mapping_valid': query.audit.valid and query.audit.game_time_mapping_valid},
        'game_time_basis': 'anchor_game_time + record_time - anchor_record_time',
        'applied': selected, 'next_record': next_record,
        'cutoff_relation': ('unavailable' if selected is None else
                            'recorded_end' if query.cutoff is None else
                            'exact_record_boundary' if applied_time == requested else 'preceding_record'),
        'seconds_before_requested': (requested - applied_time
                                     if requested is not None and applied_time is not None else None),
        'bracketing_record_interval_seconds': (next_record['record_time'] - selected['record_time']
                                               if next_record is not None else None),
        'coverage': {'first_game_time': query.audit.first_game_time,
                     'last_game_time': query.audit.last_game_time,
                     'first_section': sources[0].section, 'last_section': sources[-1].section,
                     'section_count': len(sources), 'starts_at_section_zero': sources[0].section == 0},
        'state_interpolated': False, 'native_game_clock_observed': False,
        'note': 'State ends at the inclusive recorded boundary. Game times are anchor projections; '
                'record intervals alone do not prove missing data or continuous gameplay.',
    }


def decode_player_state(
    replay_file: str | Path,
    *,
    at_game_time: float | None = None,
    at_record_time: float | None = None,
    player_ids: tuple[int, ...] | list[int] | None = None,
    runtime_evidence: dict | None = None,
    playback_speed: float | None = None,
) -> PlayerStateResult:
    """Decode every field at one inclusive native boundary.

    The ordinary query traverses every record, even when paused-clock events
    project past the last frame's game time. RecordTime selects replay-record
    seconds; GameTime selects game-clock seconds. Numeric values describe recorded
    native resources, not cached final-screen labels or completed gameplay.
    ``items`` filters native HUD-hidden definitions; ``native_items`` retains
    them. Item array indices are provenance, not rendered slot positions.
    ``player_ids`` selects unique recording-scoped native actor IDs, in roster
    order, after decoding the common boundary. Support still audits the full roster.
    """
    if at_game_time is not None and at_record_time is not None:
        raise ValueError('choose one game-time or record-time cutoff')
    for name, value in (('at_game_time', at_game_time), ('at_record_time', at_record_time)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or value < 0):
            raise ValueError(f'{name} must be finite and non-negative')
    if player_ids is not None:
        if (not isinstance(player_ids, (tuple, list)) or not player_ids
                or any(type(actor) is not int or not 0 < actor < 0xffffffff for actor in player_ids)):
            raise ValueError('player_ids must be a nonempty list or tuple of positive native actor IDs below 0xffffffff')
        if len(set(player_ids)) != len(player_ids):
            raise ValueError('player_ids must be unique')
        player_ids = tuple(player_ids)
    cutoff = (GameTime(at_game_time) if at_game_time is not None else
              RecordTime(at_record_time) if at_record_time is not None else None)
    replay = select_replay(replay_file)
    sections = replay_sections(replay)
    inputs = ReportInputs(files=tuple(path for _, path in sections), replays=(replay,))
    frames = [(number, path.read_bytes()) for number, path in sections]
    identities = {identity.path: identity.digest for identity in inputs.identities if identity is not None}
    sources = tuple(StateSource(number, str(path), hashlib.sha256(data).hexdigest(), len(data))
                    for (number, path), (_, data) in zip(sections, frames))
    for source, (_, path) in zip(sources, sections):
        if identities.get(path) != source.sha256:
            raise ReplayOutputError(path, 'Loaded replay differs from preflight bytes', 'input_changed')
    replay_scope = frame_scope(frames)
    query = select_native_query(frames, cutoff)
    boundary = _boundary(query.record_boundary)
    roster = read_native_roster(frames, cutoff)
    end_requests = tuple(
        EndRequest(RecordBoundary(request.frame_index, request.record_offset), request.record_time,
                   request.winning_team_raw, request.winning_team_raw & 0xff, request.end_reason, request.request_status)
        for request in end_match_requests(frames)
        if query.record_boundary is not None and (request.frame_index, request.record_offset) <= tuple(query.record_boundary))

    def finish(status, reason, players=(), fields=None):
        if query.valid and not query.audit.game_time_mapping_valid:
            reason = reason + '; ' + query.reason
        if replay_sections(replay) != sections:
            raise ReplayOutputError(replay, 'Replay section set changed after preflight', 'input_changed')
        inputs.recheck()
        display = build_display_values(query, players, replay_scope,
            'recorded_end' if cutoff is None else 'capture',
            runtime_evidence=runtime_evidence, playback_speed=playback_speed)
        selection_status = 'all' if player_ids is None else 'unavailable'
        missing = []
        if player_ids is not None:
            if players:
                missing = [actor for actor in player_ids if actor not in {p.native_actor_id for p in players}]
                selection_status = 'player_not_found' if missing else 'selected'
                if missing:
                    status, reason = 'player_not_found', f'native actor IDs absent at this boundary: {missing}'
            players = tuple(p for p in players if p.native_actor_id in player_ids) if not missing else ()
            display['gold'] = [row for row in display['gold']
                               if row['native_actor_id'] in {p.native_actor_id for p in players}]
        return PlayerStateResult(
            'decoder_v2.player_state.v3', replay.name[:-6], str(replay), replay_scope,
            'recorded_end' if cutoff is None else 'capture',
            'recorded_end' if cutoff is None else 'game_time' if isinstance(cutoff, GameTime) else 'record_time',
            query.requested_game_time, at_record_time, query.applied_game_time, boundary,
            status, reason, tuple(players), fields or {}, sources,
            query.audit.first_game_time, query.audit.last_game_time,
            end_requests=end_requests,
            display_values=display,
            player_selection={'mode': 'all' if player_ids is None else 'selected',
                'status': selection_status, 'requested_ids': list(player_ids) if player_ids is not None else None,
                'missing_ids': missing, 'returned_count': len(players),
                'support_scope': 'all_recorded_players_before_selection'},
            query_timing=_query_timing(query, sources),
            recording_identity=summarize_recording_identity(roster.recording_identity),
        )

    if not query.valid:
        fields = {field: StateFieldStatus(query.status, query.reason) for field in REQUIRED_FIELDS}
        return finish(query.status, query.reason, fields=fields)

    roster_boundary_ok = roster.record_boundary == query.record_boundary
    ids = [player.entity_id for player in roster.players
           if player.actor_identity_status == 'corroborated' and 0 < player.entity_id < 0xffffffff]
    identity_unique = len(ids) == len(set(ids))
    ids = ids if identity_unique and roster_boundary_ok else []
    counters = read_native_stats(frames, ids, cutoff)
    gold = read_native_gold(frames, ids, cutoff)
    inventory = read_native_inventory(frames, ids, cutoff)

    def reader_status(reader):
        if not reader.valid:
            return reader.status, reader.reason
        if reader.record_boundary != query.record_boundary:
            return 'boundary_mismatch', 'native reader did not apply the common query boundary'
        returned_ids = [player.entity_id for player in reader.players]
        if len(returned_ids) != len(ids) or set(returned_ids) != set(ids):
            return 'identity_mismatch', 'native reader returned a different actor set'
        return 'supported', 'native recorded state at the common query boundary'

    counter_status, counter_reason = reader_status(counters)
    gold_status, gold_reason = reader_status(gold)
    counter_players = {player.entity_id: player for player in counters.players} if counter_status == 'supported' else {}
    gold_players = {player.entity_id: player for player in gold.players} if gold_status == 'supported' else {}
    inventory_boundary_ok = inventory.record_boundary == query.record_boundary
    inventory_ids = [player.entity_id for player in inventory.players]
    inventory_identity_ok = len(inventory_ids) == len(ids) and set(inventory_ids) == set(ids)
    inventory_players = {player.entity_id: player for player in inventory.players} if inventory_boundary_ok and inventory_identity_ok else {}
    players = []
    for identity in roster.players:
        actor = identity.entity_id
        linked = actor in ids
        stat = counter_players.get(actor) if linked else None
        resource = gold_players.get(actor) if linked else None
        held = inventory_players.get(actor) if linked else None
        held_ok = held is not None and held.valid
        records = tuple(RecordBoundary(row.section, row.record_offset) for row in identity.observations)

        def field(status, reason, reader, native_fields, *, source_records=(), resource_sha256=None):
            version = (roster.evidence_version if reader == 'native_roster' else
                       inventory.evidence_version if reader == 'native_inventory' else
                       f'{reader}.windows_2026_10_04.v1')
            return StateFieldStatus(status, reason, FieldProvenance(
                reader, version, replay_scope, boundary, tuple(native_fields),
                tuple(source_records), resource_sha256,
            ))

        identity_status = 'supported' if linked else 'identity_unproved'
        identity_reason = 'framed 03ee actor corroborated by first native spawn definition; skin audited separately' if linked else (
            'roster/query boundary mismatch' if not roster_boundary_ok else identity.actor_identity_status)
        name_ok = identity.name is not None and roster_boundary_ok
        hero_ok = linked and identity.hero_name is not None
        hero_status = ('supported' if hero_ok else identity_status if not linked else
                       'unsupported_catalog' if identity.hero_status == 'unsupported_catalog' else 'unresolved_definition')
        first_spawn = identity.spawn_observations[0] if identity.spawn_observations else None
        skin_conflict = first_spawn is not None and first_spawn.skin_hash != identity.skin_hash
        statuses = {
            'native_actor_id': field(identity_status, identity_reason, 'native_roster', ('03ee.actor', '03f3.actor'), source_records=records),
            'name': field('supported' if name_ok else identity.name_status, identity.name_status,
                          'native_roster', ('03ee.name_utf8_bmp',), source_records=records),
            'hero': field(hero_status, identity.hero_status,
                          'native_roster', ('03ee.definition', '03f3.definition', 'original_hero_localization'),
                          source_records=records, resource_sha256=identity.hero_resource_sha256),
            'skin': field('conflicting_skin' if skin_conflict else 'unverified_rendered_skin',
                          'roster and first-spawn skin hashes differ; rendered skin is not certified'
                          if skin_conflict else 'recorded skin hashes do not certify the rendered skin',
                          'native_roster', ('03ee.skin_hash', 'first_spawn.skin_hash'),
                          source_records=records + ((RecordBoundary(first_spawn.section, first_spawn.record_offset),)
                                                    if first_spawn else ())),
            'team_id': field('supported' if linked else identity_status, 'recorded low nibble; no inferred UI side',
                             'native_roster', ('03ee.team_byte & 15',), source_records=records),
            'team': field('unresolved_team_side', 'native team ID does not establish a left/right label',
                          'native_roster', ('03ee.team_byte & 15',), source_records=records),
        }
        for name, native_fields in {
            'kda': ('attribute41', 'attribute42', 'resource11'),
            'kills': ('attribute41',), 'deaths': ('attribute42',),
            'assists': ('resource11',), 'minion_kills': ('resource14', 'native_scoreboard_cs'),
        }.items():
            statuses[name] = field(counter_status if linked else identity_status,
                                   counter_reason if linked else identity_reason, 'native_stats', native_fields)
        for name, native_field in (('gold_balance', 'resource6'), ('net_worth', 'resource7')):
            statuses[name] = field(gold_status if linked else identity_status,
                                   gold_reason if linked else identity_reason, 'native_gold', (native_field,))
        held_status = 'supported' if held_ok else held.status if held else inventory.status
        held_reason = held.reason if held else inventory.reason
        if not linked:
            held_status, held_reason = identity_status, identity_reason
        elif inventory.valid and not inventory_boundary_ok:
            held_status, held_reason = 'boundary_mismatch', 'inventory did not apply the common query boundary'
        elif not inventory_identity_ok and inventory.players:
            held_status, held_reason = 'identity_mismatch', 'inventory returned a different actor set'
        for name in ('items', 'native_items'):
            statuses[name] = field(held_status, held_reason, 'native_inventory',
                                   ('03f3.baseline', '043d.grant', '044b.consume', '0444.stack'),
                                   source_records=(_boundary(held.record_boundary),) if held and held.record_boundary else ())
        players.append(PlayerState(
            actor, identity.name if name_ok else None, identity.hero_name if hero_ok else None,
            identity.definition_index, identity.definition_name, identity.skin_hash, identity.team_id, None,
            stat.kills if stat else None, stat.deaths if stat else None, stat.assists if stat else None,
            stat.minion_kills if stat else None, _items(held.visible_items) if held_ok else None,
            _items(held.items) if held_ok else None, held.capacity if held_ok else None,
            resource.gold_balance if resource else None, resource.net_worth if resource else None, statuses,
            spawn_skin_hash=first_spawn.skin_hash if first_spawn else None,
        ))
    fields = {}
    for name in REQUIRED_FIELDS:
        failures = [player.field_status[name] for player in players if player.field_status[name].status != 'supported']
        fields[name] = (failures[0] if failures else StateFieldStatus(
            'supported' if players else roster.status,
            'supported for every recorded player' if players else '; '.join(roster.issues) or roster.reason,
        ))
    supported = roster.valid and roster_boundary_ok and identity_unique and bool(players) and all(
        player.field_status[name].status == 'supported'
        for player in players for name in (*REQUIRED_FIELDS, 'native_actor_id', 'team_id')
    )
    reasons = list(roster.issues)
    if not roster_boundary_ok:
        reasons.append('roster/query boundary mismatch')
    reasons.extend(f'{name}: {status.reason}' for name, status in fields.items() if status.status != 'supported')
    return finish('supported' if supported else 'partial' if players else roster.status,
                  'native recorded state; match completion and cached final-screen values are not asserted'
                  if supported else '; '.join(dict.fromkeys(reasons)) or 'native identity is unsupported',
                  players, fields)
