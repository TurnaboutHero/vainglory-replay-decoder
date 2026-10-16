# ImpactHealth: resource4/5 changes and opcode 041e

This follows baseline `ecfe6df` and the [temporary-resource wire report](../resource_wire_2026-10-16/01_NATIVE_BRIDGE.md). The selected Windows x86 executable SHA-256 is `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`; addresses are preferred VAs. The scope is the native action/serialization boundary, not a server damage formula or a reconstructed live barrier total.

The key distinction is that `041e` carries one signed ImpactHealth operand, not separate resource4 and resource5 deltas. Apply `0094e970` calculates those deltas using the target's current state through `0086eb50`, then writes resources4/5 directly through `0093ead0`. Serializer `0094af20` also calls the splitter and can change the action operand before serialization. A recorded negative operand therefore cannot be labelled an observed protective-resource decrement without the required state and matching execution path.

## Existing evidence and selected table

The [committed atlas branch](../evidence/2026-09-09-binary-events/branches/041e.c.txt) and existing fresh dispatcher export `extended-rea/059` identify constructor `0081b6b0`, vtable `0127c928`, and received header 1. The [previous combat extension](../sequential_rea_2026-10-16/09_STACK_COMBAT_EXTENSION.md) already establishes serializer/apply roles, the split, and notification order; these are reused rather than presented as new discoveries.

An independent selected-hash PE read corroborates the first 16 vtable bytes:

| Slot | Target | Role |
| --- | --- | --- |
| `+00` | `00529510` | Destructor slot; body not needed here |
| `+04` | `0094af20` | Serializer |
| `+08` | `0094e970` | Apply |
| `+0c` | `0092e690` | Forwarding clone, now checked in pseudo/assembly |

The 16-byte span at `0127c928` has SHA-256 `8603aec2960b15935e4579b9dc04a14946d3a03afd87679fb1d32bc343a47a30`. Existing [EXTENDED_PE_CHECK.json](../sequential_rea_2026-10-16/EXTENDED_PE_CHECK.json) independently binds the three serializer/apply/forwarding table targets and selected splitter/emitter CALLs. Fresh `impact-wire/009` pseudo and `010` assembly now close forwarding: `0092e690` acquires a 0x24-byte action, copies links/header, actor/source/operand/raw word, the `+20` word and both `+22/+23` bytes, installs vtable `0127c928`, and calls `0092f720` at `0092e6f5` with the supplied queue in ECX. It does not serialize or apply synchronously.

For opcode `041e`, selected table arithmetic is `041e-03ea=34` hex, `[004d5218]=2b`, and `[004d50ac]=004d2db0`. A bounded raw E8 scan finds `004d2e23→0081b6b0` and `004d2e37→0092c240`; these two raw candidates agree with dispatcher pseudocode but are not by themselves independent instruction-boundary validation.

## Serializer changes the operand before emitting

Existing `extended-rea/084` pseudocode and `095` assembly show this order in `0094af20`:

1. Resolve action actor `+10` and load signed float operand `+18`.
2. For an ordinary finite negative operand, call splitter `0086eb50` at `0094af60`, obtaining four prospective scalar deltas.
3. If action byte `+23==0` and target byte `+1f8` mask `10` is clear, adjust the main-health portion if current main health plus that portion would be nonpositive, leaving 1. Recombine the portions and write the resulting operand to action `+18` at `0094afba`.
4. Only then test global mode `0209e204`. When nonzero, serialize through `008167c0` at `0094b047`.

Thus the negative-operand preparation is outside the serializer's emission mode guard. It is a conditional nonlethal preparation rule, not universal immunity or a damage mitigation formula. The received-header queue branch calls apply without calling this serializer, so an incoming action uses its received operand directly. Conversely, a locally serialized action can reach apply with the rewritten operand. The shared queue guard/order is documented in [01_NATIVE_BRIDGE.md](../resource_wire_2026-10-16/01_NATIVE_BRIDGE.md).

The serializer writes this 16-byte native prefix:

| Payload offset | Width | Source/action field | Bounded interpretation |
| --- | --- | --- | --- |
| `+00` | 4 | `+10`, BE32 | Actor resolved as the mutation target in apply |
| `+04` | 4 | `+14`, BE32 | Second actor reference, used as source in selected damage notifications |
| `+08` | 4 | `+18`, BE float32 bits | Signed, possibly serializer-adjusted ImpactHealth operand |
| `+0c` | 2 | `+20`, BE16 | Opaque presentation-related word |
| `+0e` | 1 | Low byte of `+1c` | Opaque presentation-related byte |
| `+0f` | 1 | Boolean of `+22` | Opaque presentation-related boolean |

The selected apply passes `+1c/+20/+22` to a later presentation callback for negative operands. No ability ID, source-instance ID, damage type, mitigation stage, or reset reason is assigned to these fields. Action byte `+23`, which controls the selected local nonlethal preparation, is not serialized by this helper. Fresh constructor `0081b6b0` pseudo/assembly (`impact-wire/004`, `008`) confirms its seven parameters map to actor `+10`, operand `+18`, raw word `+1c`, word `+20`, byte `+22`, source `+14`, and byte `+23`. It clears queue links and received header and installs `0127c928` at `0081b6f6`.

## Native formatter versus recorded payload

Existing `extended-rea/096` pseudocode and `104` assembly close formatter `008167c0`: it constructs BE16 content length 18 (`0x12`), BE16 opcode `041e`, and copies 16 payload bytes. The untransformed branch passes 20 total bytes to `004cfea0` at `008168a4`. This content size excludes its two-byte length word.

When provider `020e7344` exists and formatter argument2 is zero, virtual `+04` receives18, its return plus2 supplies the forwarded buffer size, and virtual `+0c` receives the original opcode-plus-payload18 with an output-length pointer. That output length becomes a BE16 prefix, then the buffer is forwarded at `00816881`. The provider's implementation and transformed bytes are not identified by this wrapper. Existing transport reachability to `004eb3f0` and an installed transport virtual `+30` is static; no socket operation was executed for this research.

The atlas reports 2,146,087 historical `041e` records in 56 recordings with 22-byte payloads, whereas this selected native formatter copies 16. That six-byte difference is unresolved. It must not be replaced by the two-byte suffix found in the separate `041d` comparison. [VGR framing](../RECORD_FRAMING_2026-09-06.md) also has timestamp-f32 and content-length-u32 rather than this native BE16 transport prefix. The atlas's copy size is a known-prefix bound, not proof of a complete historical wire layout or a matched recording build.

## Received action and local application

The selected dispatcher branch copies 16 bytes, converts the two actor references, float operand and 16-bit word, then calls constructor `0081b6b0`. Its arguments include the byte at payload offset 14, word at offset 12, boolean of byte 15, second actor reference, and constant final argument 1, now confirmed to populate action `+23`. It sets received header 1 and forwards through `0092c240`. The checked vtable selects `0092e690`, which clones this header and all selected fields through `+23` into queue `0092f720`. Drain `00931bd0` consequently selects virtual apply `+08` without local serialization for this received-header path. A received actor/source pair and operand still do not establish a producer instance or cause.

Apply `0094e970` first resolves target actor `+10`. It returns if the actor is absent or its selected health pool is already nonpositive: component `+2f0` ordinarily, component `+2f4` when actor `+1f8` mask10 is set. Source actor lookup uses action `+14`. For a resolved source and negative operand, selected source attribution and `onTakeDamage`/`onDealDamage` notifications occur before final scalar allocation/mutation. These earlier notifications do not themselves establish health loss or protective-resource consumption.

At `0094eca5`, the apply calls splitter `0086eb50` using the operand from action `+18`. For each nonzero resource4/5 output, it calls bookkeeping helper `008577c0` and then actor ADD `0093ead0`:

| Calculated output | Bookkeeping CALL | Scalar ADD CALL | Aggregate storage after `0095f270` |
| --- | --- | --- | --- |
| resource4 | `0094ecc7` | `0094ecdd` | Actor component `+300` |
| resource5 | `0094ecfc` | `0094ed12` | Actor component `+304` |
| main health0 | none in this selected block | `0094ed33` | Actor component `+2f0` |
| alternate health1 | none in this selected block | `0094ed54` | Actor component `+2f4` |

The ADD/storage path is the previously checked `0093ead0→0095f270`, including floor0 and generic resource-change notifications. It does not require a separate `041d` for these writes.

Fresh bookkeeping `008577c0` pseudo/assembly (`impact-wire/006`, `011`) first requires `0209e204!=0`. It passes the target actor, type global `020e9cd4`, a local buffer and maximum count 64 to `0112a700`, then walks the returned entries in that enumerator's order. For entries whose resource kind `+1c` matches the selected kind, it consumes a budget `abs(delta)` from instance amount `+20`: subtract the budget and stop when the amount exceeds it; otherwise set amount 0 and continue with the unconsumed budget. These finite, nonnegative-instance arithmetic branches are amount consumption/zeroing, not a proved FIFO policy or instance deletion. The enumerator's ordering and coverage beyond that 64-entry request are not established here.

There is no explicit separate resource-action emitter, instance-deletion call, or phase-6 helper call in the selected bookkeeping body. This helper does not itself write the aggregate scalar; `0094e970` subsequently calls the actor ADD. The mode guard belongs to bookkeeping: an apply reaching the nonzero-output block can still perform its scalar ADD when that bookkeeping guard is false. The same action can therefore change aggregate resources without this helper updating local instance amounts. None of these branches establishes expiry, death reset, or a unique consumed buff instance from the wire record.

## What the splitter calculates

`0086eb50` (`extended-rea/030` pseudo, `083` assembly) clears four output slots and only calculates prospective deltas; it does not store aggregate resources. For ordinary finite values, positive input goes to main-health output. Negative input first consumes positive resource4 at component `+300`. For the remaining negative amount, the selected second protective allocation uses `min(component[+304], component[+2f0])` and factor 0.5 (`01213f9c`, binary32 `3f000000`). Residual health routes to pool0 or1 according to actor `+1f8` mask10.

Consequently, splitting requires the target's current resources0/4/5 and pool flag, in addition to the operand. Complete resource4 absorption, partial resource5 absorption, alternate-pool routing, and a target becoming absent/dead before apply are distinct paths. Serializer and apply call the splitter at different times and may observe different target state. The signed input is not a raw weapon/ability damage estimate, and this downstream split does not establish armor, penetration, amplification, or the authoritative pre-calculation pipeline.

For example, take the same ordinary finite input `-100`, main health 1000, and alternate-pool flag clear. The selected arithmetic gives different resource deltas solely from different pre-state:

| Input operand | Before resource4 / resource5 | Calculated delta4 / delta5 / main health |
| --- | --- | --- |
| `-100` | `0 / 0` | `0 / 0 / -100` |
| `-100` | `40 / 30` | `-40 / -30 / -30` |

These are arithmetic counterexamples from the selected split, not native execution or replay-derived accepted effects. Both have the same `041e` signed operand, so that operand alone cannot uniquely identify either protective-resource decrement. Here main health remains positive in both cases, so the serializer's selected nonlethal adjustment does not distinguish them.

## Snapshot, lifetime, and completeness boundary

The [existing snapshot extension](../sequential_rea_2026-10-16/08_REWARD_SNAPSHOT_EXTENSION.md) identifies producer `004ca310`, full serializer `004cbc90`, and receiver `004d5930` for `03f3`. The producer directly reads actor component `+300/+304` at `004ca374/004ca384`. Fresh receiver pseudo/assembly (`impact-wire/012`, `014`) confirms decoded payload offset 338 (`0x152`) is stored into temporary resource4 at `+2e0`, and offset 346 (`0x15a`) into temporary resource5 at `+2e4`; this baseline field block requires payload offset 326 (`0x146`) to be zero. Offsets338/346 are distinct and are not a consecutive two-float pair. Separately, fresh `0095c940` (`013`) copies all 16 resources from temporary `+2d0` to actor component `+2f0` in two groups of eight, rather than calculating impact deltas.

Those are a separate snapshot path. A snapshot field's availability does not establish that a historical `041e` record includes it, that an existing actor is overwritten, or that all mutations/lifetimes between snapshots are covered. The [replay report](02_REPLAY.md) preserves the projection's exact layout/lifetime limits. This report does not use snapshots as an implicit repair for missing ImpactHealth state.

Closing `041d` creation/increment and `041e` impact application establishes two kinds of scalar mutation, not a complete resource4/5 lifetime history. Buff lifetime/removal, actor destruction/reuse, explicit resets, other writers, initial state and exact record ordering remain separate coverage requirements. The directly connected bookkeeping body closes its selected amount-consumption loop, without adding a lifetime/removal/death path. Neither callback sums nor an unlabeled negative ADD establishes which temporary-resource instance was consumed.

## Receipts and falsification

Raw envelopes remain private; [REA_RECEIPTS.json](REA_RECEIPTS.json) binds their hashes, evidence IDs, and subjects. Source envelopes relative to `private-evidence`:

| Claim | Existing envelope |
| --- | --- |
| Fresh selected dispatcher `041e` body | `extended-rea/059-procedure_pseudo_code-0x004cfec0.json` |
| Splitter | `extended-rea/030-procedure_pseudo_code-0x0086eb50.json`, `083-procedure_assembly-0x0086eb50.json` |
| Serializer | `extended-rea/084-procedure_pseudo_code-0x0094af20.json`, `095-procedure_assembly-0x0094af20.json` |
| Formatter | `extended-rea/096-procedure_pseudo_code-0x008167c0.json`, `104-procedure_assembly-0x008167c0.json` |
| Apply and exact resource writes | `extended-rea/106-procedure_pseudo_code-0x0094e970.json`, `108-procedure_assembly-0x0094e970.json` |
| Fresh constructor | `impact-wire/004-procedure_pseudo_code-0x0081b6b0.json`, `008-procedure_assembly-0x0081b6b0.json` |
| Fresh forwarding clone and queue handoff | `impact-wire/009-procedure_pseudo_code-0x0092e690.json`, `010-procedure_assembly-0x0092e690.json` |
| Directly connected instance consumption | `impact-wire/006-procedure_pseudo_code-0x008577c0.json`, `011-procedure_assembly-0x008577c0.json` |
| Selected snapshot fields and resource copy | `impact-wire/012-procedure_pseudo_code-0x004d5930.json`, `014-procedure_assembly-0x004d5930.json`, `013-procedure_pseudo_code-0x0095c940.json` |

The parent's single serial `impact-wire` REA session completed and closed normally at export015. The constructor, forwarding clone and directly connected bookkeeping were checked against the new bodies; existing serializer, formatter, splitter and apply evidence was reused. No further native query is required for this selected local action bridge. Public receipt hashes bind local complete-envelope verification; independent review of the public report is a separate check.

A decisive matched-build trace preserves action generation, actor IDs/generations, original and serializer-adjusted operand, action bytes `+22/+23`, pool flag and resources0/1/4/5 at both split calls, calculated deltas, bookkeeping instance changes, final scalar stores, record bytes/offset, and recording build. Test full absorption, partial absorption, nonlethal preparation, already nonpositive pool, missing target, and changed state between serialization/application. These are proposed native comparisons, not performed experiments or software-test outcomes. No new game execution, network traffic, binary modification, installation, or production state reducer is used here.
