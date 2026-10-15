"""Unauthenticated, recording-scoped identity/viewpoint observations.

Native 03ee +64 is a separate byte string, not authenticated account identity.
Native 03e9 selects an actor/team through a mode-dependent getter, not an uploader.
This historical diagnostic never changes roster state, support or result decisions.
"""

from collections import Counter
from dataclasses import dataclass
import hashlib
import struct
from typing import Sequence

from vg.core.native_query import GameTime, NativeQuery, RecordTime, select_native_query
from vg.core.stat_evidence import frame_scope


@dataclass(frozen=True, slots=True)
class IdentitySource:
    section: int
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ExternalIdObservation:
    section: int
    record_offset: int
    timestamp: float
    payload_length: int
    raw_actor_id: int | None
    native_actor_id: int | None
    status: str
    raw_field_hex: str | None
    raw_value_hex: str | None
    utf8_value: str | None
    raw_payload_hex: str


@dataclass(frozen=True, slots=True)
class ExternalIdCandidate:
    raw_value_hex: str
    utf8_value: str | None
    source_records: tuple[tuple[int, int], ...]
    shared_with_actor_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ExternalIdHistory:
    native_actor_id: int
    status: str
    observations: tuple[ExternalIdObservation, ...]
    candidates: tuple[ExternalIdCandidate, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SelectionObservation:
    section: int
    record_offset: int
    timestamp: float
    payload_length: int
    status: str
    raw_actor_id: int | None
    recording_selected_actor_id: int | None
    raw_team_byte: int | None
    team_id: int | None
    raw_payload_hex: str


@dataclass(frozen=True, slots=True)
class RecordingSelection:
    status: str
    recording_selected_actor_id: int | None
    recording_selected_team_id: int | None
    roster_consistency: str
    observations: tuple[SelectionObservation, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecordingIdentity:
    replay_scope: str | None
    query_status: str
    record_boundary: tuple[int, int] | None
    sources: tuple[IdentitySource, ...]
    external_id_histories: tuple[ExternalIdHistory, ...]
    unassigned_external_id_observations: tuple[ExternalIdObservation, ...]
    external_id_evidence_status: str
    selection: RecordingSelection
    issues: tuple[str, ...]
    evidence_version: str = 'recording_identity.windows_2026_10_15.v1'
    completeness_status: str = 'unknown'
    authenticated_account_id: None = None
    authenticated_uploader_identity: None = None
    recording_client_verified: bool = False



@dataclass(frozen=True, slots=True)
class ExternalIdCandidateSummary:
    raw_value_hex: str
    utf8_value: str | None
    observation_count: int
    first_source_record: tuple[int, int]
    last_source_record: tuple[int, int]
    shared_with_actor_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ExternalIdHistorySummary:
    native_actor_id: int
    status: str
    observation_count: int
    empty_observation_count: int
    candidates: tuple[ExternalIdCandidateSummary, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecordingSelectionSummary:
    status: str
    recording_selected_actor_id: int | None
    recording_selected_team_id: int | None
    roster_consistency: str
    observation_count: int
    first_source_record: tuple[int, int] | None
    last_source_record: tuple[int, int] | None
    status_counts: dict[str, int]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RecordingIdentitySummary:
    replay_scope: str | None
    query_status: str
    record_boundary: tuple[int, int] | None
    source_count: int
    external_id_histories: tuple[ExternalIdHistorySummary, ...]
    unassigned_external_id_observation_count: int
    unassigned_status_counts: dict[str, int]
    external_id_evidence_status: str
    selection: RecordingSelectionSummary
    issues: tuple[str, ...]
    evidence_version: str = 'recording_identity.windows_2026_10_15.v1'
    detail_level: str = 'summary'
    completeness_status: str = 'unknown'
    authenticated_account_id: None = None
    authenticated_uploader_identity: None = None
    recording_client_verified: bool = False


def summarize_recording_identity(evidence: RecordingIdentity) -> RecordingIdentitySummary:
    """Bound default state output by actors/candidates, not repeated snapshots.

    Full source hashes are already in player-state source_files. Full raw
    observations remain available through the native-roster diagnostic API/CLI.
    First/last pointers and counts do not stand in for the complete history.
    """
    histories = tuple(ExternalIdHistorySummary(
        history.native_actor_id, history.status, len(history.observations),
        sum(row.status == 'empty' for row in history.observations),
        tuple(ExternalIdCandidateSummary(
            candidate.raw_value_hex, candidate.utf8_value, len(candidate.source_records),
            candidate.source_records[0], candidate.source_records[-1], candidate.shared_with_actor_ids,
        ) for candidate in history.candidates), history.issues,
    ) for history in evidence.external_id_histories)
    selected = evidence.selection
    first = selected.observations[0] if selected.observations else None
    last = selected.observations[-1] if selected.observations else None
    selection = RecordingSelectionSummary(
        selected.status, selected.recording_selected_actor_id, selected.recording_selected_team_id,
        selected.roster_consistency, len(selected.observations),
        (first.section, first.record_offset) if first is not None else None,
        (last.section, last.record_offset) if last is not None else None,
        dict(Counter(row.status for row in selected.observations)), selected.issues,
    )
    # Do not duplicate the full per-record issue locations in default state JSON.
    issues = tuple(issue for issue in evidence.issues if issue == 'supplied_sections_do_not_start_at_zero')
    if evidence.query_status != 'accepted':
        issues += ('query_unavailable',)
    if evidence.unassigned_external_id_observations:
        issues += ('unassigned_external_id_observations',)
    return RecordingIdentitySummary(
        evidence.replay_scope, evidence.query_status, evidence.record_boundary, len(evidence.sources),
        histories, len(evidence.unassigned_external_id_observations),
        dict(Counter(row.status for row in evidence.unassigned_external_id_observations)),
        evidence.external_id_evidence_status, selection, issues,
    )


def _external_id(section, record) -> ExternalIdObservation:
    payload = bytes(record.payload)
    actor = native_actor = None
    field = value = text = None
    status = 'unsupported_layout'
    if len(payload) in (216, 222):
        actor = struct.unpack_from('>I', payload, 160)[0]
        native_actor = actor if actor not in (0, 0xffffffff) else None
        raw = payload[64:128]
        field = raw.hex()
        end = raw.find(b'\0')
        status = 'unterminated_field' if end < 0 else 'nonempty' if end else 'empty'
        if end >= 0:
            value = raw[:end].hex()
            try:
                text = raw[:end].decode('utf-8')
            except UnicodeDecodeError:
                pass  # Byte identity does not depend on successful text presentation.
        if native_actor is None:
            status = 'reserved_actor'
    return ExternalIdObservation(section, record.offset, record.timestamp, len(payload),
                                 actor, native_actor, status, field, value, text, payload.hex())


def _selection(section, record) -> SelectionObservation:
    payload = bytes(record.payload)
    actor = selected = raw_team = team = None
    status = 'unsupported_layout'
    if len(payload) == 101:
        actor = struct.unpack_from('>I', payload)[0]
        selected = actor if actor not in (0, 0xffffffff) else None
        raw_team = payload[100]
        team = raw_team & 15
        # The native getter returns team 1 for actor -1. It is not a selection.
        status = ('unresolved_actor' if selected is None else
                  'unsupported_team' if team not in (1, 2) else 'observed')
    return SelectionObservation(section, record.offset, record.timestamp, len(payload), status,
                                actor, selected, raw_team, team, payload.hex())


def _selection_summary(observations, roster_teams, roster_incomplete, partial_input):
    issues = list(dict.fromkeys(row.status for row in observations if row.status != 'observed'))
    pairs = {(row.recording_selected_actor_id, row.team_id) for row in observations if row.status == 'observed'}
    actor = team = None
    consistency = 'unavailable'
    if not observations:
        status = 'missing'
    elif any(row.status == 'unsupported_layout' for row in observations) or partial_input:
        status = 'incomplete'
    elif issues:
        status = 'unresolved'
    elif len(pairs) != 1:
        status = 'changing_selection'
        issues.append('changing_selection')
    else:
        candidate_actor, candidate_team = next(iter(pairs))
        teams = roster_teams.get(candidate_actor, set())
        if roster_incomplete:
            status, consistency = 'incomplete', 'incomplete'
        elif not teams:
            status, consistency = 'uncorroborated', 'missing_roster'
        elif teams != {candidate_team}:
            status, consistency = 'conflicting_roster', 'conflict'
        else:
            status, consistency = 'observed', 'consistent'
            actor, team = candidate_actor, candidate_team
        if consistency != 'consistent':
            issues.append('roster_' + consistency)
    if partial_input:
        issues.append('supplied_sections_do_not_start_at_zero')
    return RecordingSelection(status, actor, team, consistency, tuple(observations), tuple(issues))


def _recording_identity(frames: Sequence[tuple[int, bytes]], query: NativeQuery) -> RecordingIdentity:
    """Share the production query and its exact supplied-byte scope with roster."""
    sources = tuple(IdentitySource(number, len(data), hashlib.sha256(data).hexdigest())
                    for number, data in frames)
    try:
        scope = frame_scope(frames)
    except (struct.error, OverflowError):
        scope = None
    histories = {}
    unassigned = []
    selections = []
    roster_teams = {}
    issues = []
    partial_input = bool(frames and frames[0][0] != 0)
    if partial_input:
        issues.append('supplied_sections_do_not_start_at_zero')
    for section, record in query.records():
        if record.opcode == 0x03ee:
            row = _external_id(section, record)
            if row.native_actor_id is None:
                unassigned.append(row)
                issues.append(f'section {section} offset {record.offset}: {row.status}')
            else:
                histories.setdefault(row.native_actor_id, []).append(row)
                roster_teams.setdefault(row.native_actor_id, set()).add(record.payload[210] & 15)
        elif record.opcode == 0x03e9:
            selections.append(_selection(section, record))
    owners = {}
    for actor, rows in histories.items():
        for row in rows:
            if row.raw_value_hex:
                owners.setdefault(row.raw_value_hex, set()).add(actor)
    results = []
    for actor, rows in histories.items():
        candidates = {}
        for row in rows:
            if row.raw_value_hex:
                candidates.setdefault(row.raw_value_hex, []).append(row)
        values = tuple(ExternalIdCandidate(raw, rows_for_value[0].utf8_value,
                       tuple((row.section, row.record_offset) for row in rows_for_value),
                       tuple(sorted(owners[raw] - {actor})))
                       for raw, rows_for_value in candidates.items())
        problems = []
        if len(values) > 1:
            problems.append('conflicting_nonempty_candidates')
        if any(value.shared_with_actor_ids for value in values):
            problems.append('candidate_shared_across_actors')
        if any(row.status == 'unterminated_field' for row in rows):
            problems.append('unterminated_field')
        status = ('conflicting_candidates' if len(values) > 1 else
                  'shared_candidate' if any(value.shared_with_actor_ids for value in values) else
                  'incomplete' if problems else 'observed_single_candidate' if values else 'empty_only')
        results.append(ExternalIdHistory(actor, status, tuple(rows), values, tuple(problems)))
    if not query.valid:
        issues.append(query.reason)
    roster_incomplete = any(row.status == 'unsupported_layout' for row in unassigned)
    evidence_status = ('unavailable' if not query.valid else
                       'incomplete' if unassigned or partial_input or any(row.issues for row in results) else
                       'observed' if results else 'missing')
    selection = _selection_summary(selections, roster_teams, roster_incomplete, partial_input)
    if not query.valid:
        selection = RecordingSelection('unavailable', None, None, 'unavailable', (), (query.reason,))
    return RecordingIdentity(scope, query.status, query.record_boundary, sources, tuple(results),
                             tuple(unassigned), evidence_status, selection, tuple(issues))


def read_recording_identity(
    frames: Sequence[tuple[int, bytes]],
    cutoff: GameTime | RecordTime | None = None,
) -> RecordingIdentity:
    """Read historical evidence for exactly one recording, with inclusive cutoff.

    Like other low-level native readers, frames must be a single recording's
    numbered bytes. Use decode_player_state(path) for verified filename-family
    discovery; concatenating unrelated byte tuples cannot establish provenance.
    Scope binds all supplied bytes, even for an early query. It is not a match ID,
    an authenticity claim, or proof that every original section is supplied.
    """
    return _recording_identity(frames, select_native_query(frames, cutoff))
