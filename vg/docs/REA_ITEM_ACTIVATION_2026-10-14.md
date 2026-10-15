# REA item activation timeline

Baseline: main `7d1e0e982d24bf48a11de6debbaeab7b7db090ba` after PR #26.
REA 6.4.0 / Ghidra 12.1.4 inspected the reference x86 Windows client with
SHA-256 `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`.

The default lossless timeline now includes three activation request layouts and
the mode-bearing `044c` message. Requests and messages remain distinct from the
existing inventory reducer's `044b` consumption update.

```sh
python -B -m vg.analysis.event_timeline /path/to/match.0.vgr \
  --opcode 0x0448 --opcode 0x0449 --opcode 0x044a --opcode 0x044c \
  -o /path/to/activation.jsonl
```

## Recorded field contract

| Opcode | Exact payload / content length | Exposed prefix |
| --- | --- | --- |
| `0448` | 6 / 8 | `item_activation_request`; BE32 `native_item_instance_id`; opaque two-byte suffix. |
| `0449` | 14 / 16 | `item_activation_request`; two unsigned BE32 `native_request_arguments`; opaque six-byte suffix. |
| `044a` | 22 / 24 | `item_activation_request`; three unsigned BE32 `native_vector_bits`, one raw BE32 argument; opaque six-byte suffix. |
| `044c` | 22 / 24 | `item_activation_message`; BE32 actor `ref0`, item instance, raw target word, two coordinate bit patterns, mode byte; opaque one-byte suffix. |

Request rows have `native_semantic_scope=serializer_prefix` and no actor refs.
The anonymous arguments of `0449`/`044a` do not acquire actor, target or item
identity from numeric coincidence. Vector words retain their bits without a
claimed coordinate system or units. The native request mode is not an extra
mode byte in these recorded payloads.

`044c` has `native_semantic_scope=receiver_prefix` and `native_conditional=true`.
All modes retain `native_target_raw`, `native_coordinate_bits` and
`native_activation_mode`. Mode-active fields are:

| Mode | Native constructor / active fields |
| --- | --- |
| 0 | `0081b7f0` retains the target; output `ref1` denotes this active entity reference. No position is emitted. |
| 1 | `0081b790` replaces the action's target with `ffffffff`, copies the two coordinates and stores mode 1. Output `native_position` contains finite floats or null; no `ref1`. |
| 2 | `0081b740` sets target to `ffffffff`, clears coordinates and stores mode 2. Output has no semantic target or position. |
| Other | `unsupported_mode` retains the bounded envelope and raw mode without mode-dependent target/position fields. |

The item's instance is never an entity reference. Therefore entity filtering
matches the activation actor, or the active mode-0 target, but not item-only
requests, inactive target words or item instances. Prior identity enrichment
retains its existing observed/sentinel scope. A raw word does not establish a
live target or successful ability execution.

NaN and infinity in an active position become JSON null while their original
float32 bits remain available; negative zero is preserved. Inactive coordinate
slots retain bits only. No rounding or inferred map-boundary rejection is added.
Unsupported lengths, including shorter native serializer layouts, remain
`unexpected_content_length`; inconsistent direct `VGRRecord` payloads retain
`unexpected_payload_length`. All timeline rows retain complete source payload,
record locator and outer record time.

## Native trace and limits

The [native receipt](evidence/2026-10-14-rea-activation/native-receipt.json)
retains 17 REA call identities/hashes and bounded observations:

- Receiver `004d3e39` copies 21 bytes and selects constructors for mode 0/1/2;
  another mode does not select one of those constructors in this build.
- Apply `0094ee90` is guarded by client/server mode, actor/component resolution,
  matching item instance and ability type. Mode 0 uses an entity target, mode 1
  sets targeting coordinates/state, and mode 2 follows the untargeted path.
  The traced apply eventually dispatches `onPlayAbility` on eligible paths;
  this is not proof of an inventory decrement or every downstream side effect.
- All three request wrappers have observed caller `00529ff0`. Its internal
  mode 3 forwards action+`14` through `0095bda0` to the four-byte `00813dc0`
  serializer; mode 0 forwards two words through `0095bea0` / `00813fc0`; mode 1
  forwards three words plus an argument through `0095bdd0` / `00813ec0`.
  Serialized lengths are 4/8/16; recorded lengths remain separately 6/14/22.

Class names, serializer presence and packet proximity do not authenticate
network direction, producer build, request/outcome pairing, successful item use,
cooldown completion, consumption or refund. Reference-build evidence hashes do
not certify the recording client's identity. Existing
[inventory](NATIVE_INVENTORY_2026-10-04.md) and
[event atlas](EVENT_SEMANTICS_2026-10-04.md) retain their separate state and
whole-variant runtime gates. No new inventory mutation is inferred here.

## Actual replay verification

An original development-corpus rescan used strict framing: 56 recordings,
7,870 sections and 30,729,156 records, excluding AppleDouble metadata. Every
activation timeline row was compared with original payload bytes, BE32 values,
float bit patterns, mode-active references, source time and record locator.

| Opcode | Original / matching rows | Recordings |
| --- | ---: | ---: |
| `0448` | 11,711 / 11,711 | 55 |
| `0449` | 31 / 31 | 14 |
| `044a` | 6,084 / 6,084 | 54 |
| `044c` | 17,438 / 17,438 | 55 |

Total: 35,264 matching rows. Observed activation modes were 655 mode-0,
6,077 mode-1 and 10,706 mode-2 messages. The corpus had no unsupported mode or
nonfinite coordinate slot; those boundaries are covered by synthetic regressions.
All 7,870 original section hashes remained unchanged. Four real timeline CLI
cases returned strict JSONL with exit 0. The path-free
[corpus receipt](evidence/2026-10-14-rea-activation/corpus-verification.json)
binds source hashes and the changed decoder module.

This verifies offline field extraction using the shared strict record parser;
it is not independent validation of framing or native runtime execution. No game
or replay slot was modified, and no held-out recording was used for tuning.
Game-screen playback and native execution validation were explicitly excluded
from this increment because the operator cannot perform them currently. They
remain separate follow-up evidence, not part of the 35,264 matching-row claim.

The later [live boots follow-up](COOLDOWN_LIVE_2026-10-14.md) exercised normal
practice UI actions with passive native observations. It supplies separate
runtime evidence for those three scenarios, not replay-frame alignment or
whole-opcode validation of this corpus.

Focused tests cover exact layouts, unsigned/raw fields, mode-active refs,
nonfinite/negative-zero floats, unknown modes, entity filtering, real CLI
success/truncation and unchanged inventory baselines/transitions until a separate
consume record. All 78 focused tests passed on macOS Python 3.14.7 and Windows
Python 3.13.2. The full macOS suite passed 919 tests with no skips. Base event
atlas validation passed without promoting pending per-opcode runtime controls.
