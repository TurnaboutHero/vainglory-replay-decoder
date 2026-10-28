"""Exact-layout native field decoding, shared by timeline consumers."""
import math
import struct
from typing import Final, Literal, TypeGuard, TypedDict, assert_never
from vg.core.vgr_records import VGRRecord

NATIVE_EVIDENCE_SHA256: Final = "c23b2e9eb201f47694c7e71ab39d2c8c96850beb4ddf489745def23927fcd891"
NATIVE_EVIDENCE: Final = "gamekindred-c23b2e9e"
END_MATCH_EVIDENCE_SHA256: Final = "659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642"
END_MATCH_EVIDENCE: Final = "windows-659f9eed"
ITEM_EVENT_EVIDENCE: Final = "rea-item-events.windows_2026_10_14.v1"
ITEM_ACTIVATION_EVIDENCE: Final = "rea-item-activation.windows_2026_10_14.v1"
COOLDOWN_EVENT_EVIDENCE: Final = "rea-cooldown-events.static_2026_10_14.v1"
COOLDOWN_EVENT_EVIDENCE_SHA256: Final = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
IMPACT_EVENT_EVIDENCE: Final = "rea-impact-wire.windows_2026_10_16.v1"
IMPACT_EVENT_EVIDENCE_SHA256: Final = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
ATTRIBUTE_STATS: Final[dict[int, str]] = {0x29: "kills", 0x2A: "deaths"}
type KnownOpcode = Literal[
    0x03F1, 0x040B, 0x041C, 0x041D, 0x041E, 0x0428, 0x0429, 0x042B, 0x0430, 0x0431,
    0x0448, 0x0449, 0x044A, 0x044C, 0x044D, 0x048A, 0x048F,
]
DEFAULT_OPCODES: Final = frozenset({
    0x03F1, 0x041C, 0x041D, 0x041E, 0x0428, 0x0429, 0x042B, 0x0430, 0x0431,
    0x0448, 0x0449, 0x044A, 0x044C, 0x044D, 0x048A, 0x048F,
})
EXPECTED_CONTENT_LENGTH: Final[dict[KnownOpcode, int]] = {
    0x03F1: 8,
    0x040B: 8,
    0x041C: 24,
    0x041D: 16,
    0x041E: 24,  # Observed payload22; receiver consumes16, suffix6 stays opaque.
    0x0428: 16,
    0x0429: 16,
    0x042B: 16,
    0x0430: 16,  # Two opcode bytes plus the observed 14-byte payload.
    0x0431: 8,
    0x0448: 8,
    0x0449: 16,
    0x044A: 24,
    0x044C: 24,
    0x044D: 16,
    0x048A: 24,
    0x048F: 8,
}

class DecodedFields(TypedDict, total=False):
    decoding_status: str
    expected_content_length: int
    expected_payload_length: int
    ref0: int
    ref1: int
    value: float | None
    value_bits: int
    code: int
    remaining_hex: str
    uninterpreted_bytes: list[int]
    native_evidence: str
    native_evidence_sha256: str
    native_label: str
    native_victim_id: int
    native_source_raw: int
    native_source_is_sentinel: bool
    native_class: str
    native_winning_team_id: int
    native_winning_team_raw: int
    native_requested_team_raw: int
    native_requested_team_id: int
    native_result_scope: str
    native_end_reason: int
    native_surrender: bool
    native_type: str
    native_index: int
    native_layer: int
    native_operation: str
    native_stat: str | None
    native_flags: list[int]
    native_state_bits: int
    native_mask_a: int
    native_mask_b: int
    native_state_from: int
    native_state_to: int
    native_conditional: bool
    native_item_instance_id: int
    native_callback: str
    native_semantic_scope: str
    native_request_arguments: list[int]
    native_vector_bits: list[int]
    native_activation_mode: int
    native_target_raw: int
    native_coordinate_bits: list[int]
    native_position: list[float | None]
    native_lookup_key: int
    native_ability_slot_index: int
    native_operand_raw: int
    native_mode_raw: int
    native_config_value: float | None
    native_config_value_bits: int
    native_byte16_raw: int
    native_code_raw: int
    native_byte14_raw: int
    native_byte15_raw: int
    native_byte17_raw: int
    native_byte18_raw: int
    native_byte19_raw: int
    native_byte20_raw: int
    native_byte21_raw: int
    native_byte18_masked: int
    native_byte19_equals_one: bool
    native_byte20_equals_one: bool
    native_byte21_equals_one: bool
    native_charge_setter_input: int
    native_base_charge_creation_input: int
    native_config_apply_scope: str
    native_charge_apply_scope: str
    native_input_apply_order: list[str]


def _is_known_opcode(opcode: int) -> TypeGuard[KnownOpcode]:
    return opcode in EXPECTED_CONTENT_LENGTH


def _float_fields(payload: memoryview, offset: int) -> tuple[float | None, int]:
    raw_bits = struct.unpack_from(">I", payload, offset)[0]
    value = struct.unpack_from(">f", payload, offset)[0]
    return (value if math.isfinite(value) else None, raw_bits)


def decode_fields(record: VGRRecord) -> DecodedFields:
    """Decode only structurally confirmed fields for an exact known layout.

    ActorDie preserves the raw death source, not a credited killer. Only the
    observed 14-byte payload is decoded; its final six bytes remain opaque.
    An end-match action records a queued request, not completed-match proof.
    Reasons 5/6/7 enter validation-error paths and 8 is a no-op in this build.
    native_surrender is only the consumer's reason == 2 boolean; team IDs have
    no screen-side mapping here. Timestamp always belongs to the outer record.
    Item requests/notifications decode only a traced receiver or serializer
    prefix. Activation-mode semantics do not establish successful consumption.
    Suffixes, callback side effects and purchase outcomes remain unverified.
    Impact source is a raw actor reference, not credited damage ownership.
    Its serialized operand is not an accepted resource4/5 decrement.
    """
    if not _is_known_opcode(record.opcode):
        return {"decoding_status": "unknown_opcode"}

    expected_length = EXPECTED_CONTENT_LENGTH[record.opcode]
    if record.content_length != expected_length:
        return {
            "decoding_status": "unexpected_content_length",
            "expected_content_length": expected_length,
        }

    payload = record.payload
    if len(payload) != expected_length - 2:
        return {
            "decoding_status": "unexpected_payload_length",
            "expected_payload_length": expected_length - 2,
        }
    match record.opcode:
        case 0x03F1:
            winning_team_raw = struct.unpack_from(">I", payload, 0)[0]
            return {
                "decoding_status": "decoded",
                "native_type": "end_match_action",
                "native_class": "Nuo::Kindred::ActionEndMatch",
                "native_winning_team_raw": winning_team_raw,
                "native_winning_team_id": winning_team_raw & 0xFF,
                # Legacy winning_team names remain compatible; these are end
                # request operands, not a certified match winner or UI color.
                "native_requested_team_raw": winning_team_raw,
                "native_requested_team_id": winning_team_raw & 0xFF,
                "native_result_scope": "end_request",
                "native_end_reason": payload[4],
                "native_surrender": payload[4] == 2,
                "remaining_hex": payload[5:].hex(),
                "native_evidence": END_MATCH_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x040B:
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "native_label": "ActionEntityDestroy",
                "native_class": "Nuo::Kindred::ActionEntityDestroy",
                "native_type": "entity_destroy_action",
                "remaining_hex": payload[4:].hex(),
                "native_evidence": END_MATCH_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x041C:
            value, raw_bits = _float_fields(payload, 8)
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "ref1": struct.unpack_from(">I", payload, 4)[0],
                "value": value,
                "value_bits": raw_bits,
                "code": payload[12],
                "remaining_hex": payload[13:].hex(),
                "native_evidence": NATIVE_EVIDENCE, "native_type": "attribute_update",
                "native_index": payload[12], "native_layer": payload[13],
                "native_operation": "set" if payload[14] != 0 else "add",
                "native_stat": ATTRIBUTE_STATS.get(payload[12]),
            }
        case 0x041D:
            value, raw_bits = _float_fields(payload, 4)
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "value": value,
                "value_bits": raw_bits,
                "code": payload[8],
                "remaining_hex": payload[9:].hex(),
                "native_evidence": NATIVE_EVIDENCE, "native_type": "resource_update",
                "native_index": payload[8], "native_operation": "set" if payload[9] != 0 else "add",
                "native_flags": [payload[10], payload[11]],
                "native_stat": "assists" if payload[8] == 0x0B else None,
            }
        case 0x041E:
            # Serializer may bound the operand before emission. Apply then
            # splits it using local actor state; it is not a resource4/5 delta.
            value, raw_bits = _float_fields(payload, 8)
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "ref1": struct.unpack_from(">I", payload, 4)[0],
                "value": value, "value_bits": raw_bits,
                "native_code_raw": struct.unpack_from(">H", payload, 12)[0],
                "native_byte14_raw": payload[14], "native_byte15_raw": payload[15],
                "remaining_hex": payload[16:].hex(),
                "native_type": "impact_health_action",
                "native_class": "Nuo::Kindred::ActionImpactHealth",
                "native_semantic_scope": "raw_impact_operand",
                "native_evidence": IMPACT_EVENT_EVIDENCE,
                "native_evidence_sha256": IMPACT_EVENT_EVIDENCE_SHA256,
            }
        case 0x0428 | 0x0429:
            # The lookup key and ability-array index are distinct namespaces.
            fields: DecodedFields = {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "native_mode_raw": payload[12],
                "native_operation": "direct" if payload[12] != 0 else "relative",
                "remaining_hex": payload[13:].hex(),
                "native_conditional": True,
                "native_semantic_scope": "static_event_fields",
                "native_evidence": COOLDOWN_EVENT_EVIDENCE,
                "native_evidence_sha256": COOLDOWN_EVENT_EVIDENCE_SHA256,
            }
            if record.opcode == 0x0428:
                fields["native_type"] = "cooldown_change_event"
                fields["native_lookup_key"] = struct.unpack_from(">I", payload, 4)[0]
                fields["value"], fields["value_bits"] = _float_fields(payload, 8)
            else:
                fields["native_type"] = "ability_charge_change_event"
                fields["native_ability_slot_index"] = struct.unpack_from(">I", payload, 4)[0]
                # Retain unsigned wire bits; receiver signedness is not established.
                fields["native_operand_raw"] = struct.unpack_from(">I", payload, 8)[0]
            return fields
        case 0x042B:
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "uninterpreted_bytes": list(payload[4:]),
                "native_evidence": NATIVE_EVIDENCE, "native_type": "indexed_state_bits",
                "native_index": payload[4], "native_state_bits": payload[5],
                "native_mask_a": payload[6], "native_mask_b": payload[7],
            }
        case 0x0430:
            victim, source = struct.unpack_from(">II", payload, 0)
            return {
                "decoding_status": "decoded",
                "ref0": victim,
                "ref1": source,
                "native_label": "ActionActorDie",
                "native_class": "Nuo::Kindred::ActionActorDie",
                "native_type": "actor_die_action",
                "native_victim_id": victim,
                "native_source_raw": source,
                "native_source_is_sentinel": source == 0xFFFFFFFF,
                "remaining_hex": payload[8:].hex(),
                "native_evidence": END_MATCH_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x0431:
            return {
                "decoding_status": "decoded",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "remaining_hex": payload[4:].hex(),
                "native_evidence": NATIVE_EVIDENCE, "native_type": "actor_state_transition",
                "native_state_from": 3, "native_state_to": 4,
                "native_conditional": True,
                "native_stat": None,
            }
        case 0x0448:
            return {
                "decoding_status": "decoded",
                "native_type": "item_activation_request",
                "native_item_instance_id": struct.unpack_from(">I", payload, 0)[0],
                "native_semantic_scope": "serializer_prefix",
                "remaining_hex": payload[4:].hex(),
                "native_evidence": ITEM_ACTIVATION_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x0449:
            return {
                "decoding_status": "decoded",
                "native_type": "item_activation_request",
                "native_request_arguments": list(struct.unpack_from(">II", payload, 0)),
                "native_semantic_scope": "serializer_prefix",
                "remaining_hex": payload[8:].hex(),
                "native_evidence": ITEM_ACTIVATION_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x044A:
            return {
                "decoding_status": "decoded",
                "native_type": "item_activation_request",
                "native_vector_bits": list(struct.unpack_from(">III", payload, 0)),
                "native_request_arguments": [struct.unpack_from(">I", payload, 12)[0]],
                "native_semantic_scope": "serializer_prefix",
                "remaining_hex": payload[16:].hex(),
                "native_evidence": ITEM_ACTIVATION_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x044C:
            actor, instance, target = struct.unpack_from(">III", payload, 0)
            mode = payload[20]
            activation_fields: DecodedFields = {
                "decoding_status": "decoded" if mode in (0, 1, 2) else "unsupported_mode",
                "native_type": "item_activation_message",
                "ref0": actor,
                "native_item_instance_id": instance,
                "native_activation_mode": mode,
                "native_target_raw": target,
                "native_coordinate_bits": list(struct.unpack_from(">II", payload, 12)),
                "native_conditional": True,
                "native_semantic_scope": "receiver_prefix",
                "remaining_hex": payload[21:].hex(),
                "native_evidence": ITEM_ACTIVATION_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
            if mode == 0:
                activation_fields["ref1"] = target
            elif mode == 1:
                x, _ = _float_fields(payload, 12)
                y, _ = _float_fields(payload, 16)
                activation_fields["native_position"] = [x, y]
            return activation_fields
        case 0x044D:
            actor, instance = struct.unpack_from(">II", payload, 0)
            return {
                "decoding_status": "decoded",
                "ref0": actor,
                "native_item_instance_id": instance,
                "native_type": "item_sell_request",
                "native_class": "Nuo::Kindred::ActionSellItem",
                "native_conditional": True,
                "native_semantic_scope": "receiver_prefix",
                "remaining_hex": payload[8:].hex(),
                "native_evidence": ITEM_EVENT_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case 0x048A:
            value, value_bits = _float_fields(payload, 8)
            config_value, config_bits = _float_fields(payload, 12)
            return {
                "decoding_status": "decoded",
                "native_type": "cooldown_sync_event",
                "ref0": struct.unpack_from(">I", payload, 0)[0],
                "native_lookup_key": struct.unpack_from(">I", payload, 4)[0],
                "value": value, "value_bits": value_bits,
                "native_config_value": config_value,
                "native_config_value_bits": config_bits,
                "native_byte16_raw": payload[16],
                "native_byte17_raw": payload[17],
                "native_byte18_raw": payload[18],
                "native_byte19_raw": payload[19],
                "native_byte20_raw": payload[20],
                "native_byte21_raw": payload[21],
                "native_byte18_masked": payload[18] & 3,
                "native_byte19_equals_one": payload[19] == 1,
                "native_byte20_equals_one": payload[20] == 1,
                "native_byte21_equals_one": payload[21] == 1,
                # Static receiver input roles, not observed application/results.
                # 0052aea0 skips configuration for an existing keyed state,
                # then dispatches 0095cf10 before 0095cd10 on both paths.
                "native_charge_setter_input": payload[16],
                "native_base_charge_creation_input": payload[17],
                "native_config_apply_scope": "new_state_only",
                "native_charge_apply_scope": "existing_or_new_state",
                "native_input_apply_order": ["timer_input", "charge_setter_input"],
                "native_conditional": True,
                "native_semantic_scope": "static_event_fields",
                "native_evidence": COOLDOWN_EVENT_EVIDENCE,
                "native_evidence_sha256": COOLDOWN_EVENT_EVIDENCE_SHA256,
            }
        case 0x048F:
            return {
                "decoding_status": "decoded",
                "native_type": "item_buy_reject_notification",
                "native_class": "Nuo::Kindred::ActionRejectBuyItem_Client",
                "native_callback": "method_onRejectBuyItem",
                "uninterpreted_bytes": [payload[0]],
                "native_semantic_scope": "receiver_prefix",
                "remaining_hex": payload[1:].hex(),
                "native_evidence": ITEM_EVENT_EVIDENCE,
                "native_evidence_sha256": END_MATCH_EVIDENCE_SHA256,
            }
        case unreachable:
            assert_never(unreachable)


