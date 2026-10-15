# Reviewed native research follow-up, 2026-10-15

These original summaries and test-only models extend the combined offline
baseline `709dd8bb`. They do not change a production decoder or certify a
historical replay result. Structured findings are in the adjacent additions
files and the parent catalog. New native exports remain external hash-pinned
references; no executable, recording, account value, or wholesale disassembly
is distributed here.

## Match result and identity

The primary terminal transition commits state 2 and invokes its entry callback
before requesting secondary state 3. Equal-state and transition-mask guards can
reject either transition. Repeated end requests overwrite raw team/reason fields
without necessarily refreshing the callback. Neither first nor last recorded
request universally proves the accepted result or displayed banner.

Normal and alternate perspectives supply different relative-win booleans to the
banner consumer. Reason 0 selects victory/defeat and reason 2 selects surrender;
other reasons skip that text assignment. Nested UI guards and rendering remain
separate. Final gold still has a monotonic row cache; final time still depends on
clock history and formatter cache. No exact final gold/time or winner is promoted.

The roster external string feeds a nested player/hero mastery cache and static
`getHeroMastery` service-method path. That establishes client dataflow only:
response binding, account authentication, uploader identity and modern service
compatibility are unresolved.

Seven synthetic terminal tests cover callback order, conflicting repeats,
independent primary/secondary rejection, unknown initial state, perspective and
banner reason domain. The model excludes apply guards, nested UI state machines,
scheduling and reentrancy; it is not a replay emulator or native execution.

## Combat/network

`041a` and `041b` consume native prefixes of 13 and 8 bytes. Historical observed
14-byte payloads leave respectively 1 and 6 opaque bytes. Their guarded helpers
insert/clear a 20-entry packed override table. Insertion uses the first free slot;
lookup uses the first matching active entry without recursive remapping; clear
removes all matches. Storage masks slot values to 15 bits, while lookup/clear
compare the full operand.

Override apply requires global `0x0209e204 != 0`; incoming play requires the
opposite gate. A verified initialization sets it to zero. Literal-address and
direct-call scans cannot exclude other alias/indirect writes or establish the
semantic name of this mode. Historical override records must not be applied
unconditionally to reconstructed replay state.

Play target/vector storage can use a remapped ability while state transitions
and notifications retain the original slot. A local handle generation guards
object lifetime; it is not a cast/request transaction key. Copied destination
handles can survive failed input validation, and target+vector mode retains
handle storage while replacing active coordinate/flag interpretation.

`0425` updates or clears the selected player actor's target handle only when
the selected actor and required child component resolve. After those guards,
an unresolved target clears selection. No request sequence, explicit attacker or success byte
is consumed, so this is not a confirmed attack acknowledgement or hit.

Five synthetic tests cover prefix bounds, opaque tails, duplicate mappings,
capacity, preserved bits and nonrecursive/full-operand lookup. These research
models are under `tests/` and never mutate production replay state.

## Cooldown modifiers and selection

Named capacity-modifier methods adjust the signed modifier separately from base
capacity and current charges. Positive deltas grant charges; negative deltas
clamp only above the resulting capacity. This arithmetic is byte-width bounded.
Duration-modifier methods update additive, multiplicative or override fields;
the inspected methods do not rewrite a running timer. Removing an override
resets the sentinel rather than restoring an earlier override, and multiplicative
inverse/update operations have no local zero-divisor guard.

ScoutPak, SuperScout and Standard3v3 factories declare concrete Cam-targeted
adjustments. Illustrative capacity/duration totals 3/120, 5/90 and 1/140 are
conditional on unmodified base 2/150 and the listed controls executing once.
Declarations and inventory association do not prove active buffs or recorded
capacity; outer activation/removal/refresh timing remains unresolved.

Initial Flask/Cam flags bypass the selected stat modifiers; initial Ringo C and
Krul C flags enable fractional cooldown reduction. Shared-state reuse and later
flag changes remain separate. A two-state selector considers charge-gated
remaining times at ability+0x11c/+0x120, not directly +0x124; it is not a universal
cast eligibility predicate. Eight finite normal-range synthetic tests cover
selected arithmetic, without native execution or general floating-point/byte
wrapping equivalence.

## Evidence boundary

All native addresses refer to PE32/x86 preferred virtual addresses, image base
`0x00400000`, in SHA256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
The historical producer build is not matched. H5810 remains development-seen,
not a fresh holdout. Hash checks establish artifact identity, synthetic tests
establish model properties, and neither establishes live server behavior.

Dynamic behavior callbacks, authoritative server decisions, authenticated
service responses and exact runtime display history require additional inputs.
No unique request/impact attribution or client-to-server behavioral equivalence
is asserted. Existing all-request provenance and `winner=None` behavior remain.
