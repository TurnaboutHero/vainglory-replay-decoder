# Temporary-resource removal, timeout and reset boundaries

Baseline `1e8099c463359a322b704c92388a9ee81ddb64ab`. All new checks use the
same selected Windows PE32/LAA SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
This is offline static analysis on the cloud computer, with a copied Ghidra
project and existing tools. No game/server execution or new screen observation.

## Result

There is a concrete **negative remaining-instance cleanup action**, and the
ordinary buff timeout route can reach it through the zero-stack notification.
This closes an additional lifecycle edge; it does **not** justify zeroing a
replay actor's resource4/5 on every death, timeout or respawn. A negative `041d`
still does not identify which instance ended, or even identify expiry as its
cause. Current aggregate resource values remain unreconstructable reliably from
these observations alone.

## Removal action and component lifetime

Assembly `00858a70–00858b09` takes an actor and temporary-resource instance.
It reads instance `+20`, XORs its sign bit with `80000000`, and builds the same
inline action layout as the creation/increment paths:

- vtable `0127c9b4`, actor ID from actor `+178`
- resource ID from instance `+1c`, operand equal to sign-flipped instance `+20`
- local header 0, ADD byte 0, presentation bytes 1/0
- clone/enqueue `0092e950` at `00858aee`, then `0112a080(instance)` at `00858af5`

For ordinary positive remaining amount this is a negative ADD. It removes the
remaining instance amount, not its original grant or the aggregate resource.
The helper does not encode the instance ID, source, timer, death flag or reason.
It also does not itself check actor liveness or synchronously apply the scalar.

`0112a080` computes the component's pool slot and ORs its bit into the pool
bitmap at type `+178`. It is a marking operation, not immediate freeing or an
actor resource SET. The later generic cleanup route has separate virtual calls;
this report does not equate marking with completed destruction. The temporary
component constructor `00958cf0` installs `CKinTemporaryResource` vtable
`01284eb8`, initializes resource ID to 16 and amount to zero; the producer
subsequently overwrites them. Constructor defaults are not an active shield.

A depleted instance may have `+20=+0`. The removal helper then constructs `-0`.
Under the already traced ordinary-finite serializer gate, zero ADD is negligible
and emits no `041d`; component marking still occurs after queueing. Thus absence
of a negative record does not demonstrate absence of removal. This is a static
conditional consequence, not an observed disappearance in a live session.

## Timeout to stack hook to cleanup

The class-linked `BuffBehavior_GrantTemporaryResource` vtable is `0127db6c`;
slot `+0c` at `0127db78` is `00860cb0`. Its selected behavior:

1. Requires global `0209e204!=0`
2. Reads buff current count as unsigned low16 at `+250`
3. When count is zero, requires a non-null stored handle, matching generation,
   and nonzero virtual resolution before calling removal at `00860d97`
4. Clears its stored handle and generation after that path (a generation
   mismatch clears the stale handle without this removal call)

For nonzero counts this same body can create or increment a resource, or reduce
an existing cached amount. Its resource4/5 positive-stack calculation passes
through the previously documented zero-return helper. That limitation must not
be extended into a claim that zero-stack cleanup is also a no-op.

`0095f4d0` stores bounded current count and, only when notify is true and the
count changes, dispatches virtual `+0c` on the buff behavior list at `0095f566`.
`0092d6a0` calls this setter with `(0,1)` at `0092d6a8` before end callbacks and
setting ending-state `+224=2`. Ordinary lifetime timeout `00966410` tail-jumps
to `0092d6a0` at `00966568` after timeout callbacks, if remaining lifetime is
still nonpositive and the special flag branches do not apply.

This gives a bounded route:

`timeout -> ordinary end -> changed count to zero -> registered +0c hook -> valid handle -> negative remainder ADD -> pool mark`

There are real exclusions. Timeout callbacks can renew lifetime; packed flags
select decrement/restart, count-zero/suspend, or increment/restart behavior;
ending states 1/2 return. Setting a count already zero does not invoke the
changed-count hook. A different behavior list, missing handle, mode0, or failed
lookup does not establish the same cleanup. No universal duration or all-buffs
expiry rule follows.

## Death and respawn are not blanket zeroing rules

Selected `00841f00` is a separate resource-instance decay callback. After its
mode, lookup and positive-remaining checks it tests the actor's state-table
entry for numeric state4; CALL `00842053` then reaches `00858a70`. The alternate
elapsed-time branch computes a bounded negative delta and calls `00858230`.
This is one selected callback, not a generic rule that every actor's resource4
and resource5 reset on entering state4. The state number is kept native-neutral.

Generic death helper `0092c110` requests state3 and dispatches `onActorDie`
callbacks. It contains no direct resource4/5 reset in the inspected body;
state-entry callbacks and scripts can have further effects. Receiving `0430`
is therefore not permission for a decoder to invent zero resource4/5.

Respawn `009572b0–0095764a` writes current resources0/2 from bounded maxima,
clears attribution and movement fields, requests state1, and dispatches respawn
callbacks. The inspected direct stores do not blanket-clear resources4/5.
Callbacks prevent turning that local observation into a universal preservation
claim. Existing-actor snapshots also retain their known apply guard, and raw
snapshot candidates cannot be promoted to unconditional reset writes.

## Replay implication and falsifiers

The prior saved three-recording audit has negative resource4/5 ADD observations:
H5810 218/1, C16 247/203, normal17 1/0. H5810 was re-read locally:
663,517 framed records and all 168 section receipts reproduce the saved counts
and hashes. C16/normal17 are saved raw counts, not re-extractions of their
unavailable originals. None is assigned to this cleanup route. Negative cached adjustment, full remaining cleanup and
other producers can share the same actor/index/operand wire representation.

Damage apply also changes resources4/5 directly and updates per-instance
bookkeeping. Applying only `041d` misses these mutations. The newly closed
cleanup edge does not repair that gap, the unresolved per-resource impact
calculation, or actor/instance generation and snapshot-application boundaries.
No production reducer or inferred cause is added.

To establish reliable current values, a matched-build trace must bind each
instance/generation to its actor, capture original and remaining amount plus
aggregate before/after, distinguish timeout/stack-change/state callback/pool
cleanup, and record queue/serializer/apply outcomes. Include already-depleted
expiry, multiple simultaneous instances, same-count zero, stale generation,
state3/state4, death/respawn and existing-ID snapshots. A timer label or nearest
negative record cannot substitute for this identity and writer coverage.

## Reproduce and inspect evidence

`python -m vg.research.resource_lifecycle_pe --binary <selected executable> --output <receipt.json>`

`python -m unittest tests.test_resource_lifecycle_pe tests.test_resource_wire_observations tests.test_resource_wire_evidence`

[LIFECYCLE_PE.json](LIFECYCLE_PE.json) records selected direct CALL/JMP targets,
slot/operand checks and bounded span hashes. The verifier refuses other binary
hashes. Tests check instruction decoding, rejection and receipt scope; they are
not execution tests of the native lifecycle. All 11 lifecycle/wire tests and
73 tests including native gold/stats regressions passed. The verifier output
was reproduced byte-for-byte. Pytest is not installed in this environment;
validation uses unittest without installing software. Full unittest discovery
also passed: 1,228 tests in 75.633 seconds. These remain Linux offline checks.
[LIFECYCLE_RECEIPTS.json](LIFECYCLE_RECEIPTS.json) identifies fresh local export
hashes, including known decompiler caveats. Raw binaries, recordings, full
exports and Ghidra project are not committed.

Decompiler output for `00858a70` omits inline action construction, so assembly
is decisive. A timeout decompilation includes the shared end-body range and a
PIC warning; byte-checked CALL `009664f0` and JMP `00966568` retain their actual
instruction kinds. An exploratory interior-address query at `00841f10` split a
function; those exports are excluded, and a fresh corrected `00841f00` export
covers `00841f00–008420e5`. The inherited respawn function map also has an
interior-boundary artifact; contiguous bytes through `0095764a` are hashed and
read as assembly. These issues are not hidden by trusting pseudocode signatures.
