# Lifespring HP store boundary and Capacitor amplification

Selected client SHA-256: `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. All addresses are preferred x86 VAs. This is offline static analysis using the already cached executable, prior decompilation and fresh instruction-aligned `objdump` disassembly. No game execution, new REA session, live effect observation or independent replay validation was performed. No production decoder change is warranted.

## What this adds

The [Lifespring producer](../passive_items_2026-10-16/02_REGEN_AND_DEFENSE.md) and [generic resource bridge](../resource_wire_2026-10-16/01_NATIVE_BRIDGE.md) were already documented separately. Here their HP-specific chain is joined through the first actual storage operation. Unlike the older temporary-resource calculation that reaches the `004b7c00` zero stub, this branch has a nonstub HP add/clamp path. That does **not** establish a Capacitor 15% consumer.

1. `0083c4d0` uses missing HP, property0 and buff interval. At `0083c629..0083c63e`, the explicit amount is `(effectiveMaxHP-currentHP)*property0*buff[+23c]`, with single-precision operations. `COMISS` against the verified float32 `1.0` at `012142c4`, then `JBE 0083c693`, skips amounts at or below 1. Previous mode/time gates remain necessary.
2. The action built at `0083c647..0083c67b` has bearer actor ID at +10, resource0 at +14, the amount at +18, ADD mode0 at +1c and flags1/0 at +1d/+1e. CALL `0083c68e→0092e950` clones it. `0092e993..0092e996` copies +18 unchanged; CALL `0092e9ae→0092f720` appends it through the previously documented queue path. The queue must actually drain; cloning alone is not accepted healing.
3. Vtable slot `0127c9bc→0094f210` resolves the actor, then its ADD/resource0 branch requires current HP strictly above zero for ordinary finite values (`0094f2a1..0094f2ae`). It passes the original amount unchanged at `0094f2b0..0094f2bc` to `0093ead0`. The resource6 presentation branch is not entered for Lifespring resource0.
4. ADD's state3/4 exclusion for resource0 still applies. When admitted, `0093eb40..0093eb54` reads current HP, adds the operand once, and calls `0095f270` on the component.
5. `0095f270..0095f2eb` first stores `max(current+operand,0)`, then recomputes effective stat0/maxHP and clamps resource0 to that maximum and zero. This complete resource0 branch contains no calls and reads maxHP layers +20/+d4/+188/+23c, HP +2f0, and stat0 clamp globals. It does not read amp33..36. The earlier generic claim about nonnegative resource storage is therefore narrowed to an explicit HP upper-bound operation here.

For normal finite inputs, immediately after this setter returns:

```text
H = clamp(((layer3[0]+1)*layer1[0]+layer0[0])*(layer2[0]+1), lower0, upper0)
HPstored = max(min(max(HPold + requested, 0), H), 0)
```

This is notation for the inspected float32 operation sequence, not an unrounded mathematical replacement or an emulator. NaNs, infinities, subnormal/rounding modes, concurrent changes and callback effects are outside this formula's claim. H is recomputed at apply time; it need not equal H when the producer ran.

## Requested amount is not the accepted HP delta

After the setter returns, `0093eb60` takes `&[ebp+0c]`, the **original ADD operand**, and passes it to `0086f300` at `0093eb6b`. It does not reload HP or subtract old HP. The event key is the previously identified `onActorResourcesChangedName` global `01a73050`. Thus the notification argument is not proof of `HPstored-HPold`.

A simple counterexample illustrates the distinction: with apply-time HP=995, H=1000 and requested=10, the inspected store reaches 1000 while the original notification operand is 10. This is a synthetic arithmetic counterexample, not a Lifespring recording. Lifespring normally requests less than the missing HP at production time, but a queued action may see changed HP/maxHP at application. Do not assign that generic notification amount an accepted-heal meaning merely because it is positive.

`0086f300` includes indirect registered callbacks (`0086f3d0`); `00539400` later dispatches script notifications. Those may cause subsequent state changes. This report stops at the first store and the notification's entry argument, rather than asserting final post-callback HP or immutable callback data. It does not treat this generic notification as the distinct heal phase3/6 event `0086f4f0`.

## What this does and does not answer about Capacitor

With the producer's maxHP/currentHP/property/interval inputs and the queued action fixed, none of the explicit amount arithmetic, clone, resource0 apply, ADD or HP clamp above introduces a 1.15 factor or reads stat33..36. This closes one more candidate consumer boundary. It does not establish that Capacitor can never affect Lifespring on a live server, or rule out upstream input changes, other heal producers, scripts or later callbacks. The [actual accepted-amount amplification consumer](../effect_closure_2026-10-16/01_CAPACITOR.md) remains unresolved.

Capacitor's self-target exclusion belongs to its separate movement-speed callback. This HP chain never consults that predicate. Therefore the self-recipient in Lifespring is **not** evidence that its healing amount is excluded by the speed-only condition. Reim's self resource5 path, Phinn resource5 and Rook resource4 retain their earlier scoped conclusions; no new amount or live claim is inferred for them here.

## Reproduction

```sh
python -m vg.research.lifespring_hp_boundary --binary <selected-client> > result.json
VG_SELECTED_CLIENT=<selected-client> python -m unittest tests.test_lifespring_hp_boundary -v
```

[The receipt](LIFESPRING_HP_BOUNDARY.json) pins six instruction-aligned slices, eight byte checks, six direct-call edges and the apply vtable pointer. The whole-image SHA is checked before PE parsing. No private paths or client image are distributed. The opt-in exact-client tests reproduce this receipt and reject a one-byte mutation; portable tests reject wrong files before parsing and check report-to-script consistency. They are not native gameplay execution.

Fresh disassembly ranges: `0083c4d0..0083c6a4`, `0092e950..0092e9b8`, `0094f210..0094f2d7`, `0093ead0..0093ec36`, `0095f270..0095f468`, and `0086f300..0086f3fd`. Existing public decompiler excerpts: [resource ADD](../evidence/2026-10-03-gold-time/native-paths.txt), source `native2/function-0093ead0.c`; the cached `0095f270` body independently agrees with the HP branch. Function names are research labels, not recovered official symbols.

Validation in the cloud filesystem: `unittest` ran 4 tests successfully with the exact client set, including all four wrong-file subcases and the one-byte mutation. The generated receipt reproduced byte-for-byte in a second run. A separate run without the client environment variable passes the two portable tests and explicitly skips the two exact-client tests. The default Python environment has no pytest installed; these tests intentionally also run with the standard library and do not require installing it.
