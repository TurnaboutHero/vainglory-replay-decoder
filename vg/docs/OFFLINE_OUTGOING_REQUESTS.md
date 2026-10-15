# Offline outgoing request decoder

`vg.core.outgoing_requests` decodes exactly one explicitly plaintext,
untransformed Windows gameplay request. It is a separate API and format from
VGR replay records and incoming messages. It does not send requests, decrypt
traffic, find keys, launch a client, identify the source client build, or infer
server acceptance or match results.

## Evidence scope

The reference is the supplied Windows x86 executable with SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
The bounded schema derives from the existing local research deliverables
`server-gameplay-parameters/schemas.json`, `REPORT.md`, and
`ITEM_TARGET_SEMANTICS.md` (2026-10-15). Those local receipts are not required at
runtime and are not copied into this change. The module contains a minimal
field schema, no native-code excerpts, client binary, traffic or credentials.

This evidence establishes client-side serializer fields. It does not establish
current service compatibility, availability of an item, whole-program/live
execution, authoritative validation, or request/outcome correlation. A parsed
frame's source build remains `unverified`; the reference hash identifies the
schema evidence only. The input's SHA-256 identifies the supplied bytes.

## Explicit format and exact sizes

The required input format is `windows-untransformed-request-v1`:

`BE16(content_size) + BE16(opcode) + payload`

The content size counts the opcode and payload, excluding the initial length
word. Every multibyte field is big-endian. Payload offsets start after both
header words. No timestamps, actor envelope, mode byte, padding, suffix or
replay trailer is silently added or removed.

| Opcodes | Payload bytes | Content bytes | Full frame bytes | Fields in order |
| --- | ---: | ---: | ---: | --- |
| `03f4`, `03f5`, `03f6` | 8 | 10 | 12 | Destination component 0 bits, component 2 bits |
| `0424` | 5 | 7 | 9 | Target actor ID, raw u8 flag |
| `0411` | 5 | 7 | 9 | Target actor ID or sentinel, u8 ability-array index |
| `0412` | 13 | 15 | 17 | Three vector words, u8 ability-array index |
| `0413` | 17 | 19 | 21 | Raw target word, three vector words, u8 ability-array index |
| `0448` | 4 | 6 | 8 | Item-instance ID |
| `0449` | 8 | 10 | 12 | Target actor ID, item-instance ID |
| `044a` | 16 | 18 | 20 | Three vector words, item-instance ID |

The inspected conditional transport transform rounds content to 8-byte blocks;
its output is outside this format. Unknown/encrypted input must not be declared
plaintext to try decoding it. The API does not detect encryption or authenticate
a caller's format declaration. It rejects unknown formats, unsupported opcodes,
truncation, inconsistent lengths, block-rounded frames, trailing bytes and
concatenated frames. No fallback, key search or network path exists.

## Python API

Run from the repository root with the project's Python 3.12+ environment:

```python
from vg.core.outgoing_requests import INPUT_FORMAT, decode_outgoing_request

# Synthetic 0449 fixture, not captured traffic: actor 7, item instance 2000.
frame = bytes.fromhex("000a044900000007000007d0")
request = decode_outgoing_request(frame, input_format=INPUT_FORMAT)
assert request.field("target_actor_id").value == 7
assert request.field("item_instance_id").value == 2000
report = request.to_dict()
```

The immutable result exposes `opcode`, typed `fields`, and `input_sha256`.
Each `DecodedField` has `name`, `kind` (`u8`, `u32`, or `f32_bits`) and integer
`value`. A float32 field's value is its unsigned bit pattern, preserving negative
zero, infinities and NaN payloads without producing nonstandard JSON numbers.
It does not assign coordinate units or map axes. The raw flag remains a byte,
not a Boolean or an invented meaning; ability indices have no A/B/C UI mapping.
`0411` cannot distinguish its two constructor modes by opcode alone. Movement
omits component 1 and carries no explicit actor ID.

`0449` is actor-bearing, not proof of a fresh player-selected-target gesture.
`item_instance_id` is not an inventory slot/index or item definition ID. No item
name, current shop availability, effect recipient or consumption is inferred.
The returned provenance marks `request_intent_only`, `caller_declared`
plaintext, unverified source build/server acceptance, and unestablished response
correlation.

`REQUEST_SCHEMAS` is an immutable opcode-to-schema registry;
`request_schema_document()` returns a fresh JSON-safe description including
field widths, offsets, endian rules and semantic limits. Invalid frames raise
`RequestDecodeError` subclasses (`UnsupportedInputFormat`,
`MalformedRequestFrame`, `UnsupportedRequestOpcode`). An omitted format keyword
or non-bytes-like input raises `TypeError`.

## Offline CLI

```sh
python -B -m vg.core.outgoing_requests --schema
python -B -m vg.core.outgoing_requests --input-format windows-untransformed-request-v1 --hex 000a044900000007000007d0
python -B -m vg.core.outgoing_requests --input-format windows-untransformed-request-v1 --frame request.bin
```

The CLI prints one JSON document to stdout. Errors exit 2 with stderr only;
there is no partial decoded output. A local file is read for at most 22 bytes
(the largest supported frame is 21), is never modified, and must contain
exactly one complete supported frame. `--schema` does not decode input and
therefore needs no format declaration. The module uses only the standard library.

## Request, replay and response boundaries

The existing VGR reader uses a timestamp plus BE32 content length. Historical
item request records have different observed payload lengths: 6/14/22 bytes
for `0448`/`0449`/`044a`, versus compact outgoing payloads of 4/8/16 bytes here.
Do not strip those extra bytes and claim verified source direction/build.
The VGR timeline's existing anonymous `native_request_arguments` remain
unchanged; this API's stronger Windows outgoing field names do not relabel them.

Incoming `044c` is a separate item-activation message with its own envelope.
It is unsupported here and is not a general acknowledgement of `0448`–`044a`.
Neither an outgoing request nor a nearby incoming message proves success,
damage, inventory decrement or a one-to-one response relationship. The replay
state, winner and definitive-analysis eligibility paths are untouched.

## Verification

```sh
python -X utf8 -B -m unittest tests.test_outgoing_requests -v
python -X utf8 -B -m unittest tests.test_item_activation_timeline tests.test_analysis_eligibility -v
```

Fixtures are synthetic and portable. Coverage includes all ten schemas,
asymmetric big-endian words, unsigned values, every truncation point, exact
schema lengths, altered length/opcode endianness, unknown opcodes/formats,
block-rounded content, extra/concatenated bytes, raw flag/index values,
nonfinite float bit patterns, CLI success/failure, build-scoped provenance,
and unchanged VGR versus incoming-message interpretation. These are software
and static-schema checks, not native-client or server runtime tests.
