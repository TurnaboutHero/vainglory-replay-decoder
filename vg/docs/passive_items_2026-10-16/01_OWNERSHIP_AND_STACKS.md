# Item ownership, shared passive buffs and stack lifecycle

## Starting basis and scope

Selected artifact: Windows x86 LAA SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. Addresses are preferred-image VAs; offsets below are hexadecimal. This is static supplied-client evidence, not current-service behavior or a matched historical recording build.

Reuse [named stack conditions](../sequential_rea_2026-10-16/05_NAMED_STACKS.md) and [interval/combat limits](../sequential_rea_2026-10-16/09_STACK_COMBAT_EXTENSION.md): Bonesaw's qualifying callback, timeout decrement, Dragon's qualifying-exchange clock and interval/decay branches, generic application/reapply/setter and local cap bridge were already established. The new question is how distinct owned item instances attach to and release those buff instances. This reviewer read the parent's serialized REA outputs005/006/025/050/051 without starting another session. No production code or replay decoder is changed.

## Attach input, queued output and item ownership ledger

`00865e30` takes the item object in ECX and returns immediately when literal global `0209e204==0` (`00865e5a`). Under the opposite mode, it walks the pointer list at item definition `+30`. For each entry it derives a buff-name key through `0096c7a0/004c4450`, follows item `+8 -> +8` to the owner actor and finds its buff-manager component by type global `01ef0b4c`. Valid owner, definition list and manager are preconditions; the body dereferences the manager after lookup without an independent null guard.

At `00865ed0..00865edf` it searches manager head `+14`, walking buff links `+260`, for the same definition-name hash at buff `+228` and active state `+224==0`. If found, `0086600d` reads that buff's instance ID `+220`. Otherwise `00865eef..00865ef8` obtains a new ID from global `01a73d14` and increments the counter. This lookup compares neither the inventory item instance ID nor an item slot.

Assembly050 recovers the inline queued action omitted by pseudocode005: vtable `0127c6f8` (ActionApplyBuff), owner actor ID as both source and target, chosen buff instance ID, definition resolved through `00937c80`, duration operand `-1.0`, stack operand `1`, zero header byte, NULL override handle and generation sentinel. It forwards through virtual `+0c` at `00865f90` (pseudocode resolves `0092d8d0`) to queue `020db890`. This is a construction/enqueue fact; apply eligibility, loaded definition, before-receive/reapply vetoes and queue ordering still matter.

At `00865fa3` the chosen buff ID is appended to the item object's ledger at `+1c + 4*n`, where `n=(item word+36)&7fff`. The following packed-word update increments that 15-bit ledger count in item `+34` high bits; it preserves the low16 inventory quantity and bit31. Inventory quantity, inventory instance ID `+30`, ledger count and buff stack count are distinct values.

The known grant path `0092f980` calls this helper only under mode nonzero. The ordinary received inventory grant path may run under mode zero; its item observation alone is not evidence these local attach actions executed.

## Removal: another copy can preserve a cap-one active buff

`00870c30` also takes the item in ECX and is locally gated by `0209e204!=0` (`00870c60`). It finds the owner's buff manager (`01ef0b4c`) and inventory component (`02093f14`), gathers live inventory instance IDs, then iterates this item's tracked buff IDs. For each it checks other inventory instances, excluding this item's `+30`, for the same tracked buff ID. This is an ownership-ledger comparison across item instances, not a same-definition count heuristic. The routine assumes coherent components and inventory lookups; it is not a validated malformed-input no-op.

After finding the matching active buff by `+220` and state `+224==0`, assembly051 selects:

| Current low16 stack count at buff+250 | Additional condition | Queued output |
|---|---|---|
| Exactly1 | cap at+252 equals1 and another item ledger references the same buff ID | Preserve it: skip cancel/decrement for this ledger entry (`00870e16..00870e22`) |
| Exactly1 | Otherwise | Inline ActionCancelBuff vtable `0127c784`, owner/buff ID, header0; forward `0092dc00` at `00870e59` |
| Any value other than1 | Active matching instance exists | Inline ActionDecrementBuffStack vtable `0127c7e4`, owner/buff ID, operand1, header0; forward `0092dda0` at `00870e98` |
| Missing or nonactive instance | — | No selected cancel/decrement output for that ledger entry |

These branches are not instantaneous cancellation or successful count mutation. Existing generic action application/removal rules still decide the result. After processing, `00870ee0` replaces this item's tracked IDs with `ffffffff`; `00870efb` clears the packed ledger count while preserving low16 quantity and bit31.

The committed `00872340` removal caller reaches this helper only in mode nonzero and when its separate `param3` flag is nonzero. A sell request, a removed inventory pointer, and execution of this cleanup are therefore separate evidence. The helper does not prove every sale invokes it or that death calls it.

## Selected local policy0 and the duplicate boundary

[NAMES_AND_DEFINITIONS.json](NAMES_AND_DEFINITIONS.json) binds selected installed resource bytes and reports:

| Local buff definition | Definition index | cap u16 at+24 | reuse policy u32 at+28 |
|---|---:|---:|---:|
| Buff_Item_Bonesaw |264|1|0|
| Buff_Item_BonesawDebuff |265|5|0|
| Buff_Item_Bonesaw_Pen |332|1|0|
| Buff_Item_DragonsEye_Control |336|1|0|
| Buff_Item_DragonsEye_CrystalBonus |337|15|0|

The table resource SHA-256 is `e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79`. These caps/policies are local declarations, not proof that identical bytes were loaded during a recording.

Prior `00863050` shows policy0 normal reuse matching the active definition-name hash without its policy1 additional bestower-actor check; policy2 bypasses that reuse. The supplied policy0 values thus support the selected conditional shared-instance route and do not authorize one independent stack state per inventory copy. In particular, an already-active cap-one control buff can be recorded in two item ledgers and preserved when one referencing item is cleaned up.

There is an important ordering limit: attach sees currently active buffs, not all pending create actions. If two attachments run before queued application, both may allocate different candidate IDs; later policy0 application may reuse an existing buff. These five exports do not establish queue drain ordering or reconcile every item ledger after that case. Do not assert that every pair of copies always records the same ID, invent a new lifetime for each queued ID, or classify that unobserved ordering as a demonstrated gameplay bug.

The resource data names Bonesaw/Dragon's Eye and their buff references, but Dragon's CrystalBonus is applied through the Control factory's lifetime declaration. Preserving/removing the cap-one Control is not itself proof that the child bonus count persists/resets: actual lifetime apply/inverse behavior and accepted child removal must be bound. Bonesaw target debuff cap5 is likewise distinct from the owner's cap-one passive. Neither duplicate ownership nor the matching item MAX declaration doubles a buff cap.

## Deferred lifecycle is not the reset trigger

New `00967ca0` walks manager `+14` via buff `+260`. Only entries already in state `+224==2` are unlinked; it repairs head/tail and forward/back links, decreases manager `+1c`, then calls `0112a080`. The previously inspected helper marks pool bitmap state; it does not by itself prove immediate destruction or storage reuse. Registration of `00967ca0` as the manager's stage4 callback was already recovered in `00954e40`.

This closes deferred list cleanup after ending state, not the trigger that sets state2. It does not zero active stacks, implement a death reset, prove an on-death callback ran, or guarantee frame-level timing. Creation, reapply, cancellation/decrement, ending state, list unlink and final pool release remain distinct lifecycle steps.

## Closure, falsifiers and replay measurement

Closed statically: mode-gated attach reads the passive-name list, chooses an existing active buff ID or a candidate new one and records per-item ownership; cleanup tests other item ledgers and conditionally preserves a cap-one shared buff; local policy0 corroborates definition-based reuse; the manager unlinks already-ending buffs later.

Falsify/extend on a matched build by observing: same active definition choosing a different ID despite these predicates; cap-one/current-one cleanup with another coherent item reference still queuing cancel; actual loaded policy/cap differing from the selected resource; or a traced separate cleanup overriding this path. Changed actor/buff generation, queued-before-apply attachments and stale/missing ledgers invalidate a simplistic same-ID prediction and must be recorded rather than discarded.

A matched trace needs actor lifetime, inventory instance/definition and ledger IDs/count before and after attachment; actual loaded buff policy/cap; buff instance/generation/state/current count; queue action header/ID and accepted apply result; Control-to-CrystalBonus linkage; lastDamage/lastStack clocks and interval debt. Compare one copy, two copies, sell one, sell last, rebuy, death/revival and two pending attachments before queue drain. Separate attempted combat qualification, absorbed damage, queued adjustment and final attribute state.

Historical inventory grant/consume observations cannot alone recover these hidden ledgers or Dragon clocks. Native043e/043f payload16/34 remain distinct from unmatched historical22/38. No named stack reducer, suffix-stripping rule, per-copy cap, death-reset rule or accepted-gameplay label is enabled by this report.

## Fresh receipts

The parent acquired the following exact-build REA JSON envelopes under task-private `private-evidence/passive-items`. Hashes bind the complete envelopes, not decompiler text alone. Raw exports remain external.

| Export | SHA-256 | Evidence ID |
|---|---|---|
| `005-procedure_pseudo_code-0x00865e30.json` | `16d4f2238f5e8e1b931c604243a6349f5ac1bfad70e4ee5aaf2e1ced8bf651ec` | `ev_131b2b24e829c8f669a235459f8dd18bf407aeb9a9286aaee64ee55568c7b61f` |
| `006-procedure_pseudo_code-0x00870c30.json` | `d0f1d440bb7d5e86e867476f59602572e499126742b49a2022e9cb8639093f03` | `ev_ac2387fd5373dd40477388e7e3f5faa4024c1545843fc7c36e2819268b38aae3` |
| `025-procedure_pseudo_code-0x00967ca0.json` | `332fe9bb7459b8bc37ca7418fed59aacacdd7f28d58634e8d965b6334845704e` | `ev_22f07985f549ec5a5a8a76b04095f67454d235ae9d5ba2f82ed8d4aa1c4cdc16` |
| `050-procedure_assembly-0x00865e30.json` | `4c1b1a120cfcc51c88227b091c47687cfdefa449a8d58d5e02abbfe8dc0bf462` | `ev_fce640f44f461292576756ebbc794d83653b13faac455a1c75c0fc12cd907ca9` |
| `051-procedure_assembly-0x00870c30.json` | `5a9fec7bdadb63c1662bd36b1889b79fb99423e0b9b5110d46008e23ddec7194` | `ev_13c612edf209d67efe559bf7d2913f35d305db3eb83bc2068497123166ff83d8` |

Selected name/definition data SHA-256: `daeec7c1f86d8e39f7aa5364239dac2b513da67749eb274b259efb1ed452c668`. Item Bonesaw resource SHA-256: `9ebd8b1a6e0ec873e3f5e2477086f56857bb1f2d90b273b924d62677dcbaa8bc`; Dragon's Eye: `d3edad89a9234cd21408a0c3a5fbc2b3fcaa7041754ba305a9bf6e5141649bf6`.

## Follow-up: selected cancel/decrement handlers and lifetime construction

Fresh exports085/086 extend the queue boundary to two selected action-handler bodies. `0094cf40` takes its action in ECX, resolves actor ID at action `+10` through `00857970`, then walks the actor buff-manager head (`actor+30 -> +14`) through buff `+260`. On the first matching instance ID (`buff+220 == action+14`) it calls `00870780` and returns. A missing actor or missing matching ID returns without that call. This body contains no explicit `0209e204` guard and no `buff+224==0` test; those predicates must not be copied from the upstream item cleanup into this handler. The called cancellation helper's resulting state transition, callbacks and immediate-versus-deferred completion are not established by085 alone.

`0094d220` uses the same actor/instance-ID lookup and first-match return. On a match, the decompiled result of `011b8a40` is passed to the already-known stack setter `0095f4d0(result,1)`. A nonzero result returns; a zero result also returns when the byte at buff-definition `+1e` is zero, otherwise it calls `0092d6a0`. Export086 does not recover arguments to `011b8a40`, so this slice alone does not justify an exact subtraction formula, underflow rule, or interpreting the later call as completed deletion. The upstream cleanup explicitly constructs operand1; the setter still enforces its established count/cap and delta behavior. No missing-instance mutation or unconditional accepted stack loss follows from these bodies.

Exports087/088 close construction rather than the Control-to-CrystalBonus execution bridge. `0052ec60` allocates a pooled object, initializes `BuffBehavior_ApplyBuffToBearer` and its embedded `BehaviorHelper_ApplyBuff<BuffBehaviorContext>` vtables, and updates pool counters. Its body does not execute the helper, identify a recipient, or implement inverse removal. `00810930` allocates/initializes a `BuffCallback_Lifetime` node and appends its link to the context object's list at `+28/+2c`, incrementing `+30`; the empty-list and nonempty-list branches are explicit. It does not invoke a lifetime callback or prove that removing Dragon's Control cancels, preserves or resets CrystalBonus. The previously configured callback/list graph remains a declaration until its virtual execution and accepted child action are observed.

These facts narrow the next measurement: bind the matched action's actor/buff ID to the selected handler and record the called helper's resulting buff state/count, then trace the registered lifetime callback's execution and child instance linkage. A handler call alone cannot falsify deferred cleanup; a constructor/list node alone cannot establish child lifetime. A differing dispatch, failed lookup or rejected downstream operation falsifies a prediction of accepted mutation. No additional replay-observable field or production reducer is introduced.

Additional complete-envelope receipts (same selected EXE):

| Export | SHA-256 | Evidence ID |
|---|---|---|
| `085-procedure_pseudo_code-0x0094cf40.json` | `a034a544a584362673e2f8d2b862f5d469d1117dd83956cea415f297aee7f3e6` | `ev_6bb4bd5c6977adfa3f257f3e745a735756c59e28441faa1cfdc5e7f752fc0847` |
| `086-procedure_pseudo_code-0x0094d220.json` | `44210913dc49ca6175cb58fc1b4d688c725ea8db847e48dfa39d24696198ae14` | `ev_90952e34623aef285751814df0dfc330bd9f5ef2d22765b9c1e13b74014e5b30` |
| `087-procedure_pseudo_code-0x0052ec60.json` | `124c6d8dac30d0b470d6e2244e6b9cb7dcdbb5e639bfaa18ccf84d85ccca0d84` | `ev_7e564e01f4aef2ea9fd173dabd814110c5f000f7eda5d6d2ea8a59bb5adaa717` |
| `088-procedure_pseudo_code-0x00810930.json` | `28588cd2da66f95ea79d1897f52d89a012cf19a880896e19c1d319048064fc17` | `ev_417f260dc1304e217ff0699d932613e421bae236f517ac6f807a0eae8c7a2401` |
