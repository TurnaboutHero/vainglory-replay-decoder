"""Bounded offline decoder for one explicitly untransformed outgoing request.

These Windows serializer layouts are not VGR records or incoming responses.
The caller must establish plaintext provenance outside this module. There is no
transport, decryption, request encoder, source-build detector or outcome logic.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping


INPUT_FORMAT = "windows-untransformed-request-v1"
SCHEMA_VERSION = "outgoing_request.v1"
REFERENCE_CLIENT_SHA256 = "d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc"
FieldKind = Literal["u8", "u32", "f32_bits"]


class RequestDecodeError(ValueError):
    """The input is outside this decoder's explicit format and schema contract."""


class UnsupportedInputFormat(RequestDecodeError):
    pass


class MalformedRequestFrame(RequestDecodeError):
    pass


class UnsupportedRequestOpcode(RequestDecodeError):
    pass


@dataclass(frozen=True)
class FieldSchema:
    name: str
    offset: int  # Relative to the payload, after the length and opcode words.
    kind: FieldKind
    note: str

    @property
    def width(self) -> int:
        return 1 if self.kind == "u8" else 4

    def to_dict(self) -> dict:
        return {
            "name": self.name, "offset": self.offset, "width": self.width,
            "kind": self.kind, "endianness": "n/a" if self.width == 1 else "big",
            "note": self.note,
        }


@dataclass(frozen=True)
class RequestSchema:
    opcode: int
    request_kind: str
    fields: tuple[FieldSchema, ...]
    note: str

    @property
    def payload_size(self) -> int:
        return sum(field.width for field in self.fields)

    @property
    def content_size(self) -> int:
        return self.payload_size + 2

    @property
    def frame_size(self) -> int:
        return self.payload_size + 4

    def to_dict(self) -> dict:
        return {
            "opcode": f"{self.opcode:04x}", "request_kind": self.request_kind,
            "payload_size": self.payload_size, "content_size": self.content_size,
            "frame_size": self.frame_size, "fields": [f.to_dict() for f in self.fields],
            "note": self.note,
        }


_VECTOR_NOTE = "Observed float32 bits; coordinate units and map-axis labels unproved"
_ITEM_NOTE = "Inventory item-instance ID; not a UI slot, array index or item definition ID"
_INDEX_NOTE = "Ability-array index; no universal A/B/C label or allowed-index range established"
_ACTOR_NOTE = "Actor-ID-bearing request field; does not establish manual UI target selection"


def _vector_fields(start: int = 0) -> tuple[FieldSchema, ...]:
    return tuple(FieldSchema(f"vector_component_{i}_bits", start + 4 * i,
                             "f32_bits", _VECTOR_NOTE) for i in range(3))


_MOVEMENT_FIELDS = (
    FieldSchema("destination_component_0_bits", 0, "f32_bits", _VECTOR_NOTE),
    FieldSchema("destination_component_2_bits", 4, "f32_bits", _VECTOR_NOTE),
)
_SCHEMAS = (
    *(RequestSchema(opcode, f"movement_variant_{opcode:04x}", _MOVEMENT_FIELDS,
                    "Component 1 is omitted; control-byte meanings and actor ownership unproved")
      for opcode in (0x03f4, 0x03f5, 0x03f6)),
    RequestSchema(0x0424, "basic_attack_target_selection", (
        FieldSchema("target_actor_id", 0, "u32", "Target-selection intent; not a hit or damage result"),
        FieldSchema("raw_flag", 4, "u8", "Meaning unassigned; retain the complete byte"),
    ), "A clearing producer also exists; no attack success is inferred"),
    RequestSchema(0x0411, "ability_actor_or_sentinel", (
        FieldSchema("target_actor_id_or_sentinel", 0, "u32",
                    "Actor target or sentinel; mode-3 constructor uses 0xffffffff"),
        FieldSchema("ability_array_index", 4, "u8", _INDEX_NOTE),
    ), "Shared by action modes 0 and 3; the frame does not distinguish them"),
    RequestSchema(0x0412, "ability_vector_bearing", _vector_fields() + (
        FieldSchema("ability_array_index", 12, "u8", _INDEX_NOTE),
    ), "Action mode 1; mode is selected by opcode, not an extra payload byte"),
    RequestSchema(0x0413, "ability_raw_target_and_vector", (
        FieldSchema("raw_target_word", 0, "u32", "Raw word; no concrete mode-2 UI producer established"),
    ) + _vector_fields(4) + (
        FieldSchema("ability_array_index", 16, "u8", _INDEX_NOTE),
    ), "Action mode 2 serializer branch; no live execution claim"),
    RequestSchema(0x0448, "item_activation_item_only", (
        FieldSchema("item_instance_id", 0, "u32", _ITEM_NOTE),
    ), "Action mode 3; does not identify eventual effect recipients"),
    RequestSchema(0x0449, "item_activation_actor_bearing", (
        FieldSchema("target_actor_id", 0, "u32", _ACTOR_NOTE),
        FieldSchema("item_instance_id", 4, "u32", _ITEM_NOTE),
    ), "Action mode 0; actor field, player gesture and effect recipients are different facts"),
    RequestSchema(0x044a, "item_activation_vector_bearing", _vector_fields() + (
        FieldSchema("item_instance_id", 12, "u32", _ITEM_NOTE),
    ), "Action mode 1; not proof of item availability, consumption or success"),
)
REQUEST_SCHEMAS: Mapping[int, RequestSchema] = MappingProxyType({s.opcode: s for s in _SCHEMAS})
MAX_FRAME_SIZE = max(s.frame_size for s in REQUEST_SCHEMAS.values())


@dataclass(frozen=True)
class DecodedField:
    name: str
    kind: FieldKind
    value: int  # f32_bits remains an unsigned bit pattern, including NaN/-0/Inf.

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value}


@dataclass(frozen=True)
class DecodedRequest:
    opcode: int
    fields: tuple[DecodedField, ...]
    input_sha256: str

    def field(self, name: str) -> DecodedField:
        """Look up an observed field; no aliases to slots or player identities."""
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)

    def to_dict(self) -> dict:
        schema = REQUEST_SCHEMAS[self.opcode]
        return {
            "schema_version": SCHEMA_VERSION, "input_format": INPUT_FORMAT,
            "opcode": f"{self.opcode:04x}", "request_kind": schema.request_kind,
            "frame_size": schema.frame_size, "content_size": schema.content_size,
            "payload_size": schema.payload_size,
            "fields": {field.name: field.to_dict() for field in self.fields},
            "provenance": {
                **_provenance(), "input_sha256": self.input_sha256,
                "source_client_build": "unverified", "plaintext": "caller_declared",
            },
        }


def _provenance() -> dict:
    return {
        "direction": "client_outgoing_request", "evidence_kind": "static_serializer",
        "reference_platform": "windows_x86", "reference_client_sha256": REFERENCE_CLIENT_SHA256,
        "semantic_scope": "request_intent_only", "server_acceptance": "unverified",
        "request_response_correlation": "unestablished",
    }


def request_schema_document() -> dict:
    """Return a fresh JSON-safe schema description, without native code excerpts."""
    return {
        "schema_version": SCHEMA_VERSION, "input_format": INPUT_FORMAT,
        "frame_layout": "BE16(content_size) + BE16(opcode) + payload",
        "content_size_includes": "opcode_and_payload_only",
        "provenance": _provenance(),
        "schemas": [schema.to_dict() for schema in REQUEST_SCHEMAS.values()],
    }


def decode_outgoing_request(
    frame: bytes | bytearray | memoryview, *, input_format: str,
) -> DecodedRequest:
    """Decode exactly one caller-declared, plaintext/untransformed request frame.

    The keyword is required: unknown/encrypted formats must never be guessed.
    Both the declared BE16 length and opcode-specific size must match exactly.
    VGR records, suffixes, concatenated frames and incoming responses are not
    accepted. This validates structure, not source build, transmission or success.
    """
    if input_format != INPUT_FORMAT:
        raise UnsupportedInputFormat(
            f"only explicit {INPUT_FORMAT!r} input is supported; no format detection or decryption"
        )
    if not isinstance(frame, (bytes, bytearray, memoryview)):
        raise TypeError("frame must be bytes, bytearray or memoryview")
    size = memoryview(frame).nbytes
    if not 4 <= size <= MAX_FRAME_SIZE:
        raise MalformedRequestFrame(f"expected one complete frame of 4..{MAX_FRAME_SIZE} bytes; got {size}")
    data = bytes(frame)
    content_size = int.from_bytes(data[:2], "big")
    if content_size != size - 2:
        raise MalformedRequestFrame(
            f"BE16 content length {content_size} does not match actual content size {size - 2}"
        )
    opcode = int.from_bytes(data[2:4], "big")
    schema = REQUEST_SCHEMAS.get(opcode)
    if schema is None:
        raise UnsupportedRequestOpcode(f"unsupported outgoing request opcode 0x{opcode:04x}")
    if content_size != schema.content_size:
        raise MalformedRequestFrame(
            f"opcode 0x{opcode:04x} requires exactly {schema.content_size} content bytes; got {content_size}"
        )
    fields = tuple(DecodedField(
        field.name, field.kind,
        int.from_bytes(data[4 + field.offset:4 + field.offset + field.width], "big"),
    ) for field in schema.fields)
    return DecodedRequest(opcode, fields, hashlib.sha256(data).hexdigest())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--hex", help="exactly one complete plaintext frame as hexadecimal bytes")
    source.add_argument("--frame", type=Path, help="local binary file containing exactly one plaintext frame")
    source.add_argument("--schema", action="store_true", help="print the bounded schema description")
    parser.add_argument("--input-format", choices=(INPUT_FORMAT,), help="required plaintext provenance declaration")
    args = parser.parse_args(argv)
    if args.schema:
        result = request_schema_document()
    else:
        if args.input_format is None:
            parser.error("decoding requires --input-format; unknown or encrypted input is unsupported")
        try:
            if args.hex is not None:
                if sum(not c.isspace() for c in args.hex) > 2 * MAX_FRAME_SIZE:
                    raise MalformedRequestFrame("hex input exceeds the maximum single-frame size")
                frame = bytes.fromhex(args.hex)
            else:
                with args.frame.open("rb") as stream:
                    frame = stream.read(MAX_FRAME_SIZE + 1)
            result = decode_outgoing_request(frame, input_format=args.input_format).to_dict()
        except (OSError, ValueError) as exc:
            parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
