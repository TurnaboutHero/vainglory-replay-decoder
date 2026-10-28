# Temporary resources, queued actions, and opcode 041d

This follow-up starts from `cb89d4c`. All addresses are preferred Windows x86 VAs in the selected LAA executable, SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. The question is whether the per-instance temporary-resource delta in `00858230` becomes an `ActionModifyActorResource`, how that action reaches serialization/application, and what a replay record can retain. No native execution or production reducer change is part of this report.

Fresh assembly closes the omitted producer-to-action edge: `00858230` and creation helper `00858000` construct an `ActionModifyActorResource` ADD action with vtable `0127c9b4`, the target actor's ID, resource ID, and the instance delta/initial amount. Existing evidence then closes clone, queue, serializer, receiver, and scalar application. This is a static route under its recorded mode/lookup guards, not evidence that a particular game executed it. Source and per-instance provenance do not survive into the selected wire prefix, and other writers prevent `041d`-only aggregate reconstruction.

## Producer and per-instance boundary

The [previous value-path report](../effect_closure_2026-10-16/01_CAPACITOR.md) identifies a temporary-resource instance obtained by `00858000`. Its selected fields are `+1c` resource ID, `+20` instance amount, and `+24` associated buff value. This instance amount is separate from the actor's aggregate resource slot. Fresh assembly exposes the stack action construction omitted by the earlier decompiler.

For an existing instance, `00858230(source, target, instance, requested_delta)` computes `delta=max(-instance[+20], requested_delta)` for ordinary finite inputs, forwards an ADD action, and adds delta to instance `+20`. Positive delta separately calls `0086f4f0` with phase 6, source, target, and delta. In creation helper `00858000`, the positive-amount callback is outside the component-acquisition-success branch: when `01129d20` returns zero, JZ `0085803b` skips instance field writes and action construction to `008580a9`, then still tests the amount and can call phase 6 at `008580c3`. The cause of a zero return is not established; it must not be labelled out-of-memory or a definite allocation failure. Neither a positive callback nor the new instance amount is an observed aggregate actor barrier/fortified-health total. The queue can still defer application, the serializer can suppress a negligible emission, and the actor may be unresolved at apply time.

| Producer fact | Existing evidence and fresh assembly | Established action fields / limit |
| --- | --- | --- |
| Creation stores resource ID, instance amount, and buff-associated field | `stat-stacking/084` pseudo; `resource-wire/005` assembly `00858000` | On nonzero component return: target argument's actor ID at `+178`, passed resource ID and initial amount; vtable `0127c9b4`, ADD mode, header 0, flags 1/0. CALL `00858096` forwards to `0092e950`. |
| Increment bounds a negative delta to the instance amount and updates instance `+20` | `effect-closure/051` pseudo; `resource-wire/004` assembly `00858230` | Target argument's actor ID at `+178`, instance `+1c` resource ID, bounded delta; same vtable/header/mode/flags. CALL `008582b9` forwards to `0092e950`. |
| Positive delta emits phase 6 independently of scalar apply | Same producer bodies; `0086f4f0` | There is no evidence here that callback amount equals applied aggregate change or includes amplification. |

In both producer bodies, the action starts at stack `EBP-2c`. Stores at `-28/-24` clear action links, `-20` clears the received header, `-1c/-18/-14` supply actor/resource/operand, word `-10=0100` writes ADD byte `+1c=0` and presentation byte `+1d=1`, and byte `-0e=0` clears presentation `+1e`. The source argument and instance-associated `+24` value are not copied. No resource-instance pointer or generation is added to this action. Resource ID is passed through rather than hard-coded here, so the earlier caller evidence is still needed to identify a particular resource4/5 producer.

## Action clone and deferred dispatch

The constructor `0081b960` installs vtable `0127c9b4` and stores the following fields. Fresh assembly independently confirms the two temporary-resource producers initialize this layout inline.

| Action offset | Meaning established by constructor, serializer, and apply |
| --- | --- |
| `+04`, `+08` | Queue links, initially zero |
| `+0c` | Received/local dispatch header, initially zero |
| `+10` | One actor ID |
| `+14` | Resource ID word |
| `+18` | Float32 operand bits |
| `+1c` | Zero ADD / nonzero SET |
| `+1d`, `+1e` | Presentation flags, default 1 / 0 |

Vtable `+04` is serializer `0094b380`, `+08` apply `0094f210`, and `+0c` forwarding clone `0092e950`. The independently checked 16-byte vtable span SHA-256 is `5434c74695cc563a2be612b6c29022b203cc0c68cceb56b0c2342159c3464558`.

`0092e950` allocates a 0x20-byte clone, copies the header, actor/resource/operand and three flag bytes, then calls `0092f720`. Assembly restores the supplied queue in ECX before CALL `0092e9ae`. `0092f720` locks the queue, links the supplied action into its list, increments its count, and unlocks; neither body applies the resource synchronously.

Drain `00931bd0` walks queue `020db890`. At `00931c28` it tests action `+0c`. A nonzero received header calls virtual apply `+08` at `00931c40`. A zero local header calls virtual serializer `+04` at `00931c30`, followed by apply only if global mode byte `0209e204` is nonzero. Serialization and application are separate calls: suppressing a negligible serialized operand does not itself suppress the later local apply. The inspected mode guard is not a proof that an arbitrary runtime has that mode enabled.

## Serialization and incoming dispatcher

Serializer `0094b380` first requires `0209e204!=0` and a resolvable actor. Its comparison reference is zero for ADD and the current selected resource for SET. In the ordinary finite branch, it emits only when the absolute difference from that reference is at least `2^-23` (`0186c080`). This is a local emission condition, not a server acceptance or resource-allocation rule.

The emitted native payload has 12 bytes:

| Payload offset | Size | Native meaning |
| --- | --- | --- |
| `+00` | 4 | Actor ID, big-endian |
| `+04` | 4 | Float32 operand bits, big-endian |
| `+08` | 1 | Low byte of resource ID |
| `+09` | 1 | SET boolean |
| `+0a` | 1 | Boolean presentation flag from action `+1d` |
| `+0b` | 1 | Boolean presentation flag from action `+1e` |

Formatter `00816ec0` explicitly constructs BE16 content length 14, BE16 opcode `041d`, and those 12 payload bytes. Fresh assembly `resource-wire/006` confirms the untransformed branch passes 16 total bytes to `004cfea0` at `00816fa4`. If object `020e7344` is present and the formatter's second argument is zero, virtual `+04` receives length14, its result plus2 sets the buffer size passed onward, and virtual `+0c` receives the original opcode-plus-payload14 and returns an output length through a pointer. That returned length becomes the BE16 prefix; forwarding occurs at `00816f81`. This closes the branch's size/prefix plumbing without identifying the provider implementation, interpreting its transformed bytes, or establishing the eventual socket/file writer.

The incoming dispatcher is `004cfec0`; its `041d` branch is `004d2cf4`. Independently verified table arithmetic is `041d-03ea=33`, byte `[004d51e4+33]=2a`, then dword `[004d5000+4*2a]=004d2cf4`. CALL `004d2d6d` reaches constructor `0081b960`. The selected receiver copies 12 bytes, converts actor/operand byte order, supplies resource and SET mode, applies the two presentation-flag helpers, sets action header `+0c=1`, and forwards through `0092c240` to virtual `+0c`. This closes the received action to clone/queue/drain/apply route; it does not establish a causal source actor or resource-instance identifier in the payload.

The [receiver follow-up](../RESOURCE_RECEIVER_FOLLOWUP_2026-10-16.md) and [hash-gated PE receipt](../RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json) preserve the receiver/vtable checks. `vg.research.verify_respawn_pe` reproduces them for the selected executable only.

## Resource 4/5 scalar application

Apply `0094f210` resolves the one actor ID. Resource-6 presentation handling is separate from mutation. ADD calls `0093ead0`; SET calls `0095f160`. Both reach `0095f270`, which floors the scalar at zero and writes `actor.component+2f0+4*resource_id`.

| Resource | Scalar slot | Additional selected setter behavior |
| --- | --- | --- |
| 4 | Component `+300` | Updates stat32 base at component `+a0` and dirty bit `+334` |
| 5 | Component `+304` | No resource-5-specific upper-cap branch in the selected setter |

The ADD state-3/4 exclusion applies to resources 0/2; it is not a resource-4/5 exclusion. The scalar setters call generic resource-change notification `0086f300` and script notification `00539400`. The inspected incoming apply does not call the producer's phase-6 helper `0086f4f0`. Therefore replaying or receiving one `041d` resource4/5 update does not itself establish a Capacitor heal callback or movement-speed proc.

## Replay framing and provenance retained

[Real VGR framing](../RECORD_FRAMING_2026-09-06.md) is timestamp-f32 BE, content-length-u32 BE, opcode-u16 BE, then payload. The observed corpus has 4,606,221 `041d` records in 56 recordings, each with payload length 14 / content length 16. The selected native formatter instead constructs 12 payload bytes / content length 14. The known 12-byte prefix is useful, but those two extra recorded bytes and the recorder/transport envelope remain unresolved. No suffix stripping, direction/build match, or byte-for-byte full-frame equivalence is claimed.

The existing `native_event_fields.py` reader retains an anonymous actor reference, float bits/value, resource byte, SET flag, and remaining bytes. A `041d` payload has no proved source actor, temporary-resource handle/generation, buff instance, producer call site, or reason/reset cause. Multiple instances may affect the same actor resource. Their phase-6 amounts must not be summed and labelled applied barrier total. An ADD/SET sequence describes these selected scalar operations while still lacking the instance provenance needed to assign removal, expiry, reset, or amplification.

There is also a concrete **completeness blocker for aggregate reconstruction**. Existing `ActionImpactHealth` apply `0094e970` calls `0086eb50`, conditionally updates temporary-resource bookkeeping through `008577c0`, and calls `0093ead0` directly for resource4 and resource5. Assembly CALLs `0094ecdd` and `0094ed12` establish those two scalar writes independently of `041d`. Thus even a fully closed temporary-resource-to-`041d` bridge cannot make `041d`-only observations a complete resource4/5 state history. Recorded `041e` currently has 22 payload bytes; its atlas class connection is not a decoded scalar delta layout. Neither callback sums nor assigning an unproved `041e` operand repairs this gap. Other writers and lifetime/removal routes remain separate completeness questions, rather than being declared absent.

The minimal matched-build trace needed to close those fields records source/target actor ID plus generation, instance pointer/handle plus generation, instance resource ID and amount before/after, buff-associated field, requested and bounded delta, copied action fields, queue header/mode, emitted record offset/bytes, and aggregate scalar before/after application. Expiry/removal/reset cases require the same identity through negative ADD or SET; absence of those fields in the current wire prefix cannot be repaired by time proximity or callback sums.

## Evidence inventory and remaining scope

Raw exports remain private. Existing envelope paths relative to `private-evidence` are listed to make each selected body identifiable; their local receipt validation and an independent review of a public report are different checks.

| Edge | Existing export |
| --- | --- |
| Constructor, serializer, apply, forwarding clone | Root `010`, `011`, `009`, `012` pseudocode; `037`, `024`, `025` assembly |
| Clone queue and drain | Root `038` assembly `0092f720`, `039` assembly `00931bd0` |
| Native opcode formatter | Root `042` pseudocode `00816ec0` |
| Received presentation-flag helpers | Root `019` pseudo `0092d2f0`, `020` pseudo `0095ff00` |
| ADD, SET, floor/storage | `sequential-rea/038`, `039`, `040` pseudocode |
| Independent impact writes to resource4/5 | `extended-rea/106` pseudo and `108` assembly `0094e970`; CALLs `0094ecdd`, `0094ed12` |
| Existing-instance producer | `effect-closure/051` pseudocode `00858230` |
| Instance creation | `stat-stacking/084` pseudocode `00858000` |
| Fresh inline action fields and formatter branches | `resource-wire/004` assembly `00858230`, `005` assembly `00858000`, `006` assembly `00816ec0` |

The parent's single `resource-wire` REA session completed these three assembly queries and closed. The producer's ADD-action bridge is now established, while the provider's transformed format, recorder's two extra bytes, per-instance expiry/reset provenance, `041e` and other writer coverage, authoritative service behavior, and actual in-game totals remain open. No binary modification, network operation, native game execution, or public raw export is required or performed here.
