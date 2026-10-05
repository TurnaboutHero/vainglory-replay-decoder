"""Fixed-build native item possession from framed records at one audited boundary.

Native instances and quantities are preserved, including system items. Native
array indices are provenance, not a claim about rendered inventory slot order.
"""

from dataclasses import dataclass, replace
import json
from pathlib import Path
import struct
from typing import Collection, Sequence

from vg.core.definition_catalog import SUPPORTED_BUILD_SHA256, SUPPORTED_MANIFEST_SHA256
from vg.core.native_query import GameTime, RecordTime, select_native_query


DEFINITIONS_PATH = Path(__file__).with_name('native_inventory_definitions.json')
EVIDENCE_VERSION = 'native_inventory.windows_2026_10_04.v1'
# Separately traced native serializer and actual recorded variants. A different
# length cannot borrow these offsets merely because its prefix looks familiar.
PAYLOAD_LENGTHS = {0x03f2: (122, 126), 0x03f3: (746, 750), 0x043d: (12, 14),
                   0x044b: (10, 14), 0x0444: (12,)}


@dataclass(frozen=True, slots=True)
class NativeInventoryItem:
    definition_id: int
    instance_id: int
    quantity: int
    name: str
    definition_name: str
    array_index: int
    hud_hidden: bool = False


@dataclass(frozen=True, slots=True)
class NativeInventoryPlayer:
    entity_id: int
    valid: bool
    status: str
    reason: str
    items: tuple[NativeInventoryItem, ...] | None = None
    capacity: int | None = None
    record_boundary: tuple[int, int] | None = None


    @property
    def visible_items(self) -> tuple[NativeInventoryItem, ...] | None:
        """HUD-eligible possession; array order is not rendered slot order."""
        if self.items is None:
            return None
        return tuple(item for item in self.items if not item.hud_hidden)


@dataclass(frozen=True, slots=True)
class NativeInventoryTransition:
    entity_id: int
    opcode: int
    section: int
    record_offset: int
    payload_length: int
    kind: str
    changed: bool
    before: tuple[NativeInventoryItem, ...] | None
    after: tuple[NativeInventoryItem, ...] | None
    status: str


@dataclass(frozen=True, slots=True)
class NativeInventoryResult:
    valid: bool
    status: str
    reason: str
    players: tuple[NativeInventoryPlayer, ...] = ()
    transitions: tuple[NativeInventoryTransition, ...] = ()
    first_game_time: float | None = None
    last_game_time: float | None = None
    as_of_game_time: float | None = None
    requested_game_time: float | None = None
    record_boundary: tuple[int, int] | None = None
    evidence_version: str = EVIDENCE_VERSION
    build_sha256: str = SUPPORTED_BUILD_SHA256


def _metadata() -> tuple[dict | None, str]:
    """Names and possession rules (stacking, uniqueness, capacity) share one provenance."""
    metadata = json.loads(DEFINITIONS_PATH.read_text(encoding='utf-8'))
    provenance = tuple(metadata.get(key) for key in ('schema_version', 'build_sha256', 'manifest_sha256'))
    if provenance != ('native-item-definitions.v1', SUPPORTED_BUILD_SHA256, SUPPORTED_MANIFEST_SHA256):
        return None, ('item definition catalog provenance mismatch: schema_version {}, '
                      'build_sha256 {}, manifest_sha256 {}'.format(*provenance))
    return metadata, ''


def _items(slots):
    return tuple(item for item in slots if item is not None)


def _grant(slots, definitions, definition_id, instance_id, quantity):
    metadata = definitions.get(definition_id)
    if metadata is None:
        raise ValueError(f'unresolved native item definition {definition_id}')
    if instance_id == 0xffffffff:
        for index, item in enumerate(slots):
            if (item is not None and item.definition_id == definition_id
                    and item.quantity < metadata['max_stack']):
                slots[index] = replace(item, quantity=(item.quantity + 1) & 0xffff)
                return
        return
    if metadata['grant_skip']:
        return
    can_grant = False
    for item in slots:
        if item is not None and item.definition_id == definition_id:
            if metadata['unique']:
                return
            if item.quantity < metadata['max_stack']:
                can_grant = True
                break
    if not can_grant and all(item is not None for item in slots):
        return
    if any(item is not None and item.instance_id == instance_id for item in slots):
        raise ValueError(f'duplicate native instance identity {instance_id}')
    index = next((i for i, item in enumerate(slots) if item is None), None)
    if index is None:
        # Native admission can allow a nonfull same-definition stack with no
        # vacant pointer, then increment occupied without storing the new item.
        # That inconsistent native case is not a supported possession snapshot.
        raise ValueError('native grant admitted without a vacant item pointer')
    slots[index] = NativeInventoryItem(definition_id, instance_id, quantity & 0xffff,
                                      metadata['name'], metadata['definition_name'], index,
                                      metadata['hud_hidden'])


def read_native_inventory(
    frames: Sequence[tuple[int, bytes]],
    player_ids: Collection[int],
    cutoff: GameTime | RecordTime | None = None,
    *,
    include_transitions: bool = False,
) -> NativeInventoryResult:
    """Restore inventory without interpreting purchases/prices as possession.

    A spawn for an existing actor is a no-op, not a replacement snapshot. A new
    explicit baseline grants its recorded instances into a fresh component.
    Unknown definitions/layouts or an unobserved lifetime remain per-actor
    failures. Known empty state is an empty tuple; unavailable state is None.
    """
    query = select_native_query(frames, cutoff)
    audit = query.audit

    def result(valid, status, reason, players=(), transitions=()):
        return NativeInventoryResult(valid, status, reason, players, transitions,
                                     audit.first_game_time, audit.last_game_time,
                                     query.applied_game_time, query.requested_game_time,
                                     query.record_boundary)

    if not query.valid:
        return result(False, query.status, query.reason)
    supplied = tuple(player_ids)
    if any(not isinstance(actor, int) or isinstance(actor, bool)
           or not 0 < actor < 0xffffffff for actor in supplied) or len(set(supplied)) != len(supplied):
        return result(False, 'invalid_query', 'player IDs must be unique nonreserved unsigned 32-bit integers')
    if not supplied:
        return result(False, 'missing_baseline', 'no player identities supplied')
    metadata, mismatch = _metadata()
    if metadata is None:
        return result(False, 'unsupported_catalog', mismatch)
    definitions = {int(index): value for index, value in metadata['definitions'].items()}
    modes = set()
    for frame in query.frames:
        anchor = next(record for record in frame.records if record.opcode == 0x046f)
        try:
            modes.add(bytes(anchor.payload[:64]).split(b'\0', 1)[0].decode('ascii'))
        except UnicodeDecodeError:
            return result(False, 'unsupported_configuration', 'invalid native game-mode name')
    if len(modes) != 1 or next(iter(modes)) not in metadata['game_modes']:
        return result(False, 'unsupported_configuration', 'unknown or changing native game-mode configuration')
    capacity = metadata['game_modes'][next(iter(modes))]['capacity']
    if not isinstance(capacity, int) or not 0 < capacity <= 10:
        return result(False, 'unsupported_configuration', 'native item capacity outside allocated array')
    wanted = set(supplied)
    spawned: set[int] = set()
    states: dict[int, list[NativeInventoryItem | None]] = {}
    problems: dict[int, str] = {}
    boundaries = {}
    transitions = []
    for section, record in query.records():
        if record.opcode not in (*PAYLOAD_LENGTHS, 0x040b):
            continue
        payload = record.payload
        actor_offset = 8 if record.opcode in (0x03f2, 0x03f3) else 0
        location = f'section {section} offset {record.offset} opcode {record.opcode:04x}'
        if len(payload) < actor_offset + 4:
            for actor in wanted:
                problems[actor] = f'{location}: short payload cannot identify affected actor'
            continue
        actor = struct.unpack_from('>I', payload, actor_offset)[0]
        if actor not in wanted:
            continue
        before = _items(states[actor]) if actor in states and actor not in problems else None
        kind = {0x03f2: 'spawn_without_baseline', 0x03f3: 'baseline', 0x043d: 'grant', 0x044b: 'consume',
                0x0444: 'modify_stack', 0x040b: 'destroy_request'}[record.opcode]
        boundaries[actor] = (section, record.offset)
        try:
            if record.opcode == 0x040b:
                # 0094d470 marks a pool removal bit through0112a1f0. The request
                # alone does not establish the later cleanup/identity boundary.
                raise ValueError('actor destruction requested; native cleanup boundary unobserved')
            if len(payload) not in PAYLOAD_LENGTHS[record.opcode]:
                raise ValueError(f'unsupported {kind} payload length {len(payload)}')
            if actor in problems:
                continue
            if record.opcode == 0x03f2:
                spawned.add(actor)
                continue
            if record.opcode == 0x03f3:
                if actor in spawned:
                    continue
                spawned.add(actor)
                flag = struct.unpack_from('>I', payload, 326)[0]
                count = struct.unpack_from('>I', payload, 350)[0]
                if flag != 0:
                    raise ValueError('spawn without explicit inventory baseline')
                if count > 10:
                    raise ValueError(f'native baseline item count exceeds array bounds: {count}')
                slots = [None] * capacity
                for index in range(count):
                    definition = struct.unpack_from('>I', payload, 354 + index * 4)[0]
                    instance = struct.unpack_from('>I', payload, 394 + index * 4)[0]
                    quantity = struct.unpack_from('>I', payload, 434 + index * 4)[0]
                    _grant(slots, definitions, definition, instance, quantity)
                states[actor] = slots
            elif actor not in states:
                # Updates cannot supply the unknown pre-recording inventory.
                continue
            elif record.opcode == 0x043d:
                definition, instance = struct.unpack_from('>II', payload, 4)
                _grant(states[actor], definitions, definition, instance, 1)
            else:
                instance = struct.unpack_from('>I', payload, 4)[0]
                slots = states[actor]
                index = next((i for i, item in enumerate(slots)
                              if item is not None and item.instance_id == instance), None)
                if index is None:
                    raise ValueError(f'unresolved native {kind} target instance {instance}')
                item = slots[index]
                if record.opcode == 0x0444:
                    quantity = struct.unpack_from('>I', payload, 8)[0] & 0xffff
                    slots[index] = replace(item, quantity=quantity)
                else:
                    quantity = item.quantity - 1 if item.quantity else 0
                    if definitions[item.definition_id]['stackable'] and quantity:
                        slots[index] = replace(item, quantity=quantity)
                    else:
                        slots[index] = None
        except ValueError as exc:
            problems[actor] = f'{location}: {exc}'
        finally:
            if include_transitions:
                after = _items(states[actor]) if actor in states and actor not in problems else None
                transitions.append(NativeInventoryTransition(
                    actor, record.opcode, section, record.offset, len(payload), kind,
                    before != after, before, after,
                    'unsupported_state' if actor in problems else 'accepted' if actor in states else 'missing_baseline'))
    players = []
    for actor in sorted(wanted):
        if actor in problems:
            players.append(NativeInventoryPlayer(actor, False, 'unsupported_state', problems[actor],
                                                  record_boundary=boundaries.get(actor)))
        elif actor not in states:
            players.append(NativeInventoryPlayer(actor, False, 'missing_baseline',
                                                  'no applicable native inventory baseline',
                                                  record_boundary=boundaries.get(actor)))
        else:
            players.append(NativeInventoryPlayer(actor, True, 'accepted',
                                                  'native possession; rendered slot order not asserted',
                                                  _items(states[actor]), len(states[actor]), boundaries[actor]))
    valid = all(player.valid for player in players)
    status = 'accepted' if valid else 'unsupported_state' if problems else 'missing_baseline'
    reason = ('native state observed; match completion not asserted' if valid else
              '; '.join(f'actor {player.entity_id}: {player.reason}' for player in players if not player.valid))
    return result(valid, status, reason, tuple(players), tuple(transitions))
