"""Framed, recording-scoped player identities for the audited Windows build.

03ee establishes player membership; entity spawns only corroborate its native
actor/definition/skin association. Repeated observations are retained, never
merged by display name. EOF describes recorded state, not match completion.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import struct
from typing import Final, Sequence

from vg.core.native_query import GameTime, RecordTime, select_native_query
from vg.core.definition_catalog import SUPPORTED_BUILD_SHA256


DEFINITIONS_PATH: Final = Path(__file__).with_name('native_roster_definitions.json')


@dataclass(frozen=True, slots=True)
class RosterObservation:
    section: int
    record_offset: int
    timestamp: float
    payload_length: int
    entity_id: int
    definition_index: int
    skin_hash: int
    name: str | None
    name_status: str
    raw_name_hex: str
    raw_team_byte: int
    team_id: int
    raw_payload_hex: str


@dataclass(frozen=True, slots=True)
class RosterSpawn:
    section: int
    record_offset: int
    opcode: int
    definition_index: int
    skin_hash: int
    raw_payload_hex: str


@dataclass(frozen=True, slots=True)
class NativeRosterPlayer:
    entity_id: int
    name: str | None
    name_status: str
    definition_index: int
    skin_hash: int
    hero_name: str | None
    definition_name: str | None
    hero_status: str
    team_id: int
    team: str | None
    association_status: str
    observations: tuple[RosterObservation, ...]
    spawn_observations: tuple[RosterSpawn, ...]
    hero_resource_sha256: str | None
    hero_localization_key: str | None
    hero_localization_sha256: str


@dataclass(frozen=True, slots=True)
class NativeRosterResult:
    valid: bool
    status: str
    reason: str
    players: tuple[NativeRosterPlayer, ...] = ()
    issues: tuple[str, ...] = ()
    as_of_game_time: float | None = None
    record_boundary: tuple[int, int] | None = None
    evidence_version: str = "native_roster.windows_2026_10_04.v1"
    build_sha256: str = SUPPORTED_BUILD_SHA256
    manifest_sha256: str = "7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c"


def _name(raw: bytes) -> tuple[str | None, str, str]:
    """Read the bounded UTF-8 name; native conversion supports BMP faithfully."""
    end = raw.find(b'\0')
    if end < 0:
        return None, 'unterminated_name', raw.hex()
    raw = raw[:end]
    try:
        value = raw.decode('utf-8')
    except UnicodeDecodeError:
        return None, 'unsupported_encoding', raw.hex()
    if any(ord(char) > 0xffff for char in value):
        return None, 'unsupported_native_codepoint', raw.hex()
    return value, 'decoded_utf8_bmp', raw.hex()


def read_native_roster(
    frames: Sequence[tuple[int, bytes]],
    cutoff: GameTime | RecordTime | None = None,
) -> NativeRosterResult:
    """Read one recording using the native reader clock and inclusive cutoff.

    A result can retain players and their raw evidence while invalid: unresolved
    joins or names must remain visible to callers instead of dropping actors.
    Team is the stored low nibble, with no inferred left/right assignment.
    """
    query = select_native_query(frames, cutoff)
    if not query.valid:
        return NativeRosterResult(False, query.status, query.reason)
    audit, parsed = query.audit, query.frames
    catalog = json.loads(DEFINITIONS_PATH.read_text(encoding='utf-8'))
    metadata = catalog['definitions']
    observations: dict[int, list[RosterObservation]] = {}
    spawns: dict[int, list[RosterSpawn]] = {}
    issues: list[str] = []
    as_of = None
    boundary = None
    for frame in parsed:
        for record in frame.records:
            game_time = frame.game_time(record.timestamp)
            if cutoff is not None and (
                (isinstance(cutoff, GameTime) and game_time > cutoff.seconds)
                or (isinstance(cutoff, RecordTime) and record.timestamp > cutoff.seconds)
            ):
                continue
            as_of = game_time if audit.game_time_mapping_valid else None
            boundary = (frame.number, record.offset)
            payload = bytes(record.payload)
            location = f'section {frame.number} offset {record.offset}'
            if record.opcode == 0x03ee:
                if len(payload) not in (216, 222):
                    issues.append(f'{location}: unsupported roster payload length {len(payload)}')
                    continue
                actor, definition, skin = struct.unpack_from('>III', payload, 160)
                if actor == 0xffffffff:
                    issues.append(f'{location}: reserved actor identity')
                    continue
                name, status, raw = _name(payload[:64])
                observation = RosterObservation(
                    frame.number, record.offset, record.timestamp, len(payload), actor,
                    definition, skin, name, status, raw, payload[210], payload[210] & 15,
                    payload.hex(),
                )
                observations.setdefault(actor, []).append(observation)
            if record.opcode in (0x03f2, 0x03f3):
                lengths = (122, 126) if record.opcode == 0x03f2 else (746, 750)
                if len(payload) not in lengths:
                    issues.append(f'{location}: unsupported spawn payload length {len(payload)}')
                    continue
                definition, skin, actor = struct.unpack_from('>III', payload)
                spawns.setdefault(actor, []).append(RosterSpawn(
                    frame.number, record.offset, record.opcode, definition, skin, payload.hex(),
                ))
    players = []
    for actor, history in observations.items():
        latest = history[-1]
        actor_spawns = spawns.get(actor, [])
        association = 'missing_spawn'
        if actor_spawns:
            spawn = actor_spawns[0]
            association = ('corroborated' if (spawn.definition_index, spawn.skin_hash) ==
                           (latest.definition_index, latest.skin_hash) else 'conflicting_spawn')
        definition = metadata.get(str(latest.definition_index))
        definition_name = definition['definition_name'] if definition else None
        hero_name = definition['hero_name'] if definition and association == 'corroborated' else None
        hero_status = 'resolved' if hero_name is not None else 'unresolved_definition'
        if association != 'corroborated':
            issues.append(f'actor {actor}: {association}')
        if latest.name is None:
            issues.append(f'actor {actor}: {latest.name_status}')
        if hero_name is None:
            issues.append(f'actor {actor}: {hero_status}')
        players.append(NativeRosterPlayer(
            actor, latest.name, latest.name_status, latest.definition_index, latest.skin_hash,
            hero_name, definition_name, hero_status, latest.team_id, None, association,
            tuple(history), tuple(actor_spawns),
            definition['resource_sha256'] if definition else None,
            definition['name_key'] if definition else None,
            catalog['localization']['resource_sha256'],
        ))
    if not players:
        issues.append('no framed player roster records')
    valid = not issues
    status = 'accepted' if valid else ('partial_roster' if players else 'missing_roster')
    return NativeRosterResult(valid, status, 'recorded roster; completion not asserted',
                              tuple(players), tuple(issues), as_of, boundary)


def main() -> int:
    """Emit raw-provenance roster reports for all replay families under a root."""
    import argparse
    from vg.core.replay_input import discover_replay_files, replay_sections
    from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    replays = discover_replay_files(args.replay_root)
    inputs = ReportInputs(files=(DEFINITIONS_PATH,), replays=replays)
    validate_report_outputs(inputs, (args.output,))
    reports = []
    for frame0 in replays:
        frames = [(number, path.read_bytes()) for number, path in replay_sections(frame0)]
        reports.append({'replay': str(frame0.relative_to(args.replay_root)),
                        'result': asdict(read_native_roster(frames))})
    write_report_output(inputs, args.output, json.dumps(reports, indent=2, ensure_ascii=False) + '\n')
    return 0 if reports and all(report['result']['valid'] for report in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
