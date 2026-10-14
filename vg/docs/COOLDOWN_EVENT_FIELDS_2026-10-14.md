# Bounded cooldown/charge event observations

This additive timeline decoder starts from item-activation commit
`33611314a29d2ad57a4c56a2f6da569b22ec9641`. It changes no player-state,
combat-statistics or inventory reducer. No native game execution was performed.

```sh
python -B -m vg.analysis.event_timeline /path/to/match.0.vgr \
  --opcode 0x0428 --opcode 0x0429 --opcode 0x048a
python -B -m unittest tests.test_cooldown_event_timeline -v
```

These opcodes are also included in the default timeline. Python `decode_fields`
and `iter_timeline` expose the same fields as CLI JSONL. All rows retain the
full payload and record locator. Only the owner is `ref0`; keys and slots never
become `ref1`, entity-filter matches, item instances or ability names.

## Exact recorded layouts

All words below are big-endian. Content lengths include the two-byte opcode.
Unsupported content lengths and inconsistent actual payload sizes are rejected
before reading any fields. The 13-byte native serialized prefix of `0428` and
`0429` does not replace their observed 14-byte recorded payload gate.

| Opcode | Payload/content bytes | Fields |
| --- | --- | --- |
| `0428` | 14/16 | owner u32 at 0; `native_lookup_key` u32 at 4; `value` float32 and `value_bits` u32 at 8; `native_mode_raw` byte 12; opaque byte 13 as `remaining_hex` |
| `0429` | 14/16 | owner u32 at 0; `native_ability_slot_index` u32 at 4; unsigned `native_operand_raw` u32 at 8; mode byte 12; opaque byte 13 |
| `048a` | 22/24 | owner/key u32 at 0/4; float32 `value` and `native_config_value` at 8/12, each with original bits; six individual `native_byte16_raw` through `native_byte21_raw` |

For `0428`/`0429`, mode zero means the static relative branch, any nonzero
byte the direct branch (`native_operation`). This describes the selected
native operation, not its successful execution or resulting value. The
`0429` receiver's decompiled `Ordinal_14()` call has a missing argument artifact;
we retain the wire operand as unsigned bits without promoting signed arithmetic
or resulting charge semantics. Its ability array index is not the `0428`/`048a`
lookup key even if their numbers coincide.

For `048a`, byte 18 additionally exposes `native_byte18_masked = raw & 3`.
Bytes 19–21 expose `native_byteNN_equals_one = raw == 1`, matching receiver
comparisons, not generic nonzero truthiness. Raw bytes are always retained.
Byte 16 is a charge setter input, not a resulting charge count; byte 17 and the
float at 12 feed configuration applied on new-state creation. The static apply
finds or creates a keyed object, sets the timer input and then the charge input;
it does not overwrite all configuration on each record. No reconstructed state
is updated here.

Float32 NaN/infinity becomes JSON null while all original bits survive, including
NaN payloads; finite negative zero remains negative zero. No seconds, remaining
time, resulting charges, successful activation, cancellation, item ownership or
server result is inferred. `native_conditional=true` and
`native_semantic_scope=static_event_fields` explicitly bound these observations.

## Evidence and limits

The [receipt](evidence/2026-10-14-cooldown-events/native-receipt.json) hashes the
included static constructor/apply excerpts and existing receiver snippets.
New fields cite actual analyzed executable SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
The older receiver excerpts cite
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`;
input evidence reports a PE LAA flag difference. These provenance labels do not
authenticate the originating build of a recording. The unrelated generic
`c23b2e9e` evidence tag is not used for these new fields.

- `0428`: constructor `0081bb60`, apply `00945cc0`, relative helper `00945d70`
- `0429`: constructor `0081b8d0`, apply `0094f170`, ability-index lookup at
  `0094f186–0094f193`; do not equate slot/key namespaces
- `048a`: constructor `0052ad40`, apply `0052aea0`, new-state initializer
  `009401f0`; mask and equality-to-one inputs retain their separate wire bytes
- Existing receiver snippets: [0428](evidence/2026-09-09-binary-events/branches/0428.c.txt),
  [0429](evidence/2026-09-09-binary-events/branches/0429.c.txt),
  [048a](evidence/2026-09-09-binary-events/branches/048a.c.txt)

[H5810 offline results](evidence/2026-10-14-cooldown-events/h5810.json): 168 sections,
663,517 framed records, zero framing errors; the receipt records each input SHA-256; all selected rows decode and serialize
with strict JSON. Counts: `0428` 1,859 (645 relative, 1,214 direct), `0429` 109,
`048a` 21,001. Every `0429` observation has owner 1504, slot 0, operand 4,
mode 1, so the corpus provides no diversity for its relative or signed cases.
Those wire boundaries are synthetic tests, not native runtime validation.
Configuration input tuples vary for 31 of 148 `048a` owner/key pairs; this is
another reason not to turn raw events into a naive state-overwrite reducer.
Timer clock, pause, HUD, ability identity and coupled charge reconstruction are
outside this patch, irrespective of separate ongoing static investigations.

Reproduce the private-corpus audit from the repository root (the corpus is not
bundled):

```sh
PYTHONPATH=. python -B vg/docs/evidence/2026-10-14-cooldown-events/audit_h5810.py /path/to/H5810
```

## Archived research and reproduction

The evidence directory also contains the completed [combat-state report](evidence/2026-10-14-cooldown-events/REPORT.ko.md),
[clock/pause/HUD follow-up](evidence/2026-10-14-cooldown-events/CLOCK-HUD.ko.md),
[reproduction instructions](evidence/2026-10-14-cooldown-events/REPRODUCE.md),
[historical flow map](evidence/2026-10-14-cooldown-events/FLOW-MAP.md),
[input acquisition receipt](evidence/2026-10-14-cooldown-events/acquisition-receipt.json),
and [H5810 baseline reproduction](evidence/2026-10-14-cooldown-events/h5810-reproduction/README.md).
These broader static findings do not expand this decoder's state semantics.
The package manifest hashes the portable text artifacts; binaries, replay data,
analysis databases, dependencies and execution logs are intentionally omitted.

## Follow-up: replay clock and ability identity

The [replay-clock report](evidence/2026-10-14-cooldown-followup/replay-clock/REPORT.ko.md)
connects the scheduling cursor to the previously published scaled delta, and the
stage-4 timer tick to the newly published delta on the analyzed main-loop path.
It also identifies intervening action queue drains. Recorded timestamps alone
do not supply the playback frame partition or apply/tick receipts needed for
exact remaining seconds. The included arithmetic witnesses are synthetic,
not observations of game execution.

The [identity/lifetime report](evidence/2026-10-14-cooldown-followup/ability-identity/IDENTITY-LIFECYCLE.md)
connects actor-owned keyed state to ability pointers and ordered ability slots.
Item instances can share a keyed state under the documented conditions. These
structural links do not establish concrete recording-specific slot/key/item
maps: matching definitions, overrides and owner/object lifetimes remain needed.

These are documentation and reproducibility artifacts only. No timer reducer,
countdown estimate, numeric identifier join or player-state change is introduced.
See each report's reproduction instructions and the
[package hashes](evidence/2026-10-14-cooldown-followup/package-sha256.json).

## Concrete definition evidence: Fountain of Renewal

The [build-specific Fountain example](evidence/2026-10-14-fountain-definition/README.md)
now derives definition 487's primary key 0x6f056481 from the matched embedded
ability resource and native fallback branch. H5810 owner/key records corroborate
that mapping, with 133 sync observations for owner 1500 and 73 for owner 1501.
This narrows the earlier missing-definition limitation for this one example.
Generic ability/slot/instance joins, runtime overrides, shared-key membership
and lifetime handling remain unresolved. Definition/configuration value 75.0
is not an observed running countdown or proof of successful application.
No automatic identity enrichment or reducer is introduced.
