"""Observed native gold resources at a recorded boundary, without final-screen claims."""

from dataclasses import dataclass
import math
import struct
from typing import Collection, Sequence

from vg.core.native_query import GameTime, RecordTime, select_native_query


@dataclass(frozen=True, slots=True)
class NativeGoldPlayer:
    entity_id: int
    gold_balance: float
    net_worth: float


@dataclass(frozen=True, slots=True)
class NativeGoldResult:
    valid: bool
    status: str
    reason: str
    players: tuple[NativeGoldPlayer, ...] = ()
    first_game_time: float | None = None
    last_game_time: float | None = None
    as_of_game_time: float | None = None
    requested_game_time: float | None = None
    applied_game_time: float | None = None
    record_boundary: tuple[int, int] | None = None


def _float32(value: float) -> float:
    try:
        rounded = struct.unpack('>f', struct.pack('>f', value))[0]
    except OverflowError as exc:
        raise ValueError('native float32 resource overflow') from exc
    if not math.isfinite(rounded):
        raise ValueError('nonfinite native resource value')
    return rounded


def read_native_gold(
    frames: Sequence[tuple[int, bytes]],
    player_ids: Collection[int],
    cutoff: GameTime | RecordTime | None = None,
) -> NativeGoldResult:
    """Restore resource 6 balance and resource 7 net worth at a recorded boundary.

    Full-input framing and clocks must be supported. Only the first actor spawn
    supplies a baseline; repeated spawns cannot clear prior semantic failures.
    Updates cannot create a missing baseline. Native positive resource-6 ADD also credits resource 7, while
    resource-6 SET and debits leave resource 7 unchanged. Each store rounds to
    float32. These values do not reconstruct the cached final-screen display.
    """
    query = select_native_query(frames, cutoff)
    audit = query.audit

    def invalid(status: str, reason: str) -> NativeGoldResult:
        return NativeGoldResult(False, status, reason,
                                first_game_time=audit.first_game_time,
                                last_game_time=audit.last_game_time,
                                requested_game_time=query.requested_game_time)

    if not query.valid:
        return invalid(query.status, query.reason)
    supplied = tuple(player_ids)
    if not supplied:
        return invalid('missing_baseline', 'no player identities supplied')
    if any(not isinstance(entity, int) or isinstance(entity, bool)
           or not 0 < entity <= 0xffffffff for entity in supplied):
        return invalid('invalid_query', 'player identities must be positive unsigned 32-bit integers')
    if len(set(supplied)) != len(supplied):
        return invalid('invalid_query', 'player identities must be unique')
    ids = sorted(supplied)
    wanted = set(ids)
    states: dict[int, tuple[float, float]] = {}
    problems: dict[int, str] = {}
    spawned: set[int] = set()
    destroyed: set[int] = set()
    for section, record in query.records():
        if record.opcode not in (0x03f2, 0x03f3, 0x041d, 0x040b):
            continue
        payload = record.payload
        ref_offset = 8 if record.opcode in (0x03f2, 0x03f3) else 0
        location = f'frame {section} offset {record.offset} opcode {record.opcode:04x}'
        if len(payload) < ref_offset + 4:
            for entity in ids:
                problems[entity] = f'{location}: cannot identify actor in short payload'
            continue
        entity = struct.unpack_from('>I', payload, ref_offset)[0]
        if entity not in wanted:
            continue
        try:
            if record.opcode == 0x040b:
                destroyed.add(entity)
                problems[entity] = f'{location}: actor destruction requested; native cleanup boundary unobserved'
                continue
            if entity in destroyed:
                continue
            if record.opcode == 0x03f2:
                if len(payload) not in (122, 126):
                    raise ValueError(f'unsupported spawn length {len(payload)}')
                spawned.add(entity)
                continue
            if record.opcode == 0x03f3:
                if len(payload) not in (746, 750):
                    raise ValueError(f'unsupported snapshot length {len(payload)}')
                if entity in spawned:
                    continue
                spawned.add(entity)
                if struct.unpack_from('>I', payload, 326)[0] != 0:
                    continue
                balance, worth = struct.unpack_from('>ff', payload, 286)
                if any(not math.isfinite(value) or value < 0 for value in (balance, worth)):
                    raise ValueError('snapshot resources must be finite and nonnegative')
                states[entity] = (balance, worth)
                problems.pop(entity, None)
                continue
            if len(payload) <= 8:
                raise ValueError('short resource payload lacks index')
            index = payload[8]
            if index not in (6, 7):
                continue
            if record.content_length != 16:
                raise ValueError(f'unsupported resource content length {record.content_length}')
            value = struct.unpack_from('>f', payload, 4)[0]
            if not math.isfinite(value):
                raise ValueError('nonfinite native resource value')
            if entity not in states:
                continue
            updated = list(states[entity])
            mode = payload[9]
            if mode == 0 and index == 6 and value > 0:
                updated[1] = _float32(updated[1] + value)
            slot = index - 6
            result = updated[slot] + value if mode == 0 else value
            updated[slot] = _float32(max(result, 0.0))
            states[entity] = (updated[0], updated[1])
        except ValueError as exc:
            problems[entity] = f'{location}: {exc}'
    if problems:
        return invalid('unsupported_state', '; '.join(problems[entity] for entity in sorted(problems)))
    missing = [entity for entity in ids if entity not in states]
    if missing:
        return invalid('missing_baseline', f'no applicable native baseline for actors {missing}')
    players = tuple(NativeGoldPlayer(entity, *states[entity]) for entity in ids)
    return NativeGoldResult(True, 'accepted', 'native state observed; match completion not asserted',
                            players, audit.first_game_time, audit.last_game_time, query.as_of_game_time,
                            query.requested_game_time, query.applied_game_time, query.record_boundary)
