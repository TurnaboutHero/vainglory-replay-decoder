# Reviewed buff and status research, 2026-10-15

This is a separate extension of combined reviewed baseline `52f1786d`. It adds
original static summaries and bounded synthetic models. It does not implement
historical buff/status decoding or change production replay state.

All native addresses refer to preferred VAs of the PE32/x86 image, base
`0x00400000`, SHA256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
Raw native exports, executable images and private recordings remain external.
The source manifest binds the reviewed reports and independent review receipts.

## Generic lifetime dispatch

The newly traced creation path checks action eligibility and factory lookup,
creates the buff and dispatches its callback slot +4. For the Lifetime callback,
this reaches contained behavior application methods. Removal zeros stack count,
dispatches callback +0x18 and therefore inverse modifier methods, then marks the
buff removed. This closes the generic outer apply/inverse dispatch gap recorded
in the earlier frozen cooldown summary.

Reapplication and stack-change notifications use different callback slots. For
Lifetime, both are stubs. They do not directly rerun modifiers or establish when
dynamic behavior-update methods execute. Buff stacks are distinct from cooldown
charges. Policy, source, duplicate-instance and zero-stack guards still matter.

Timer expiry does not universally imply removal. Removed state, suspension flag,
remaining duration, a mode byte and command-routing flag control whether the
timer path reaches the expiry handler. An optional predicate gates subtraction
only; an already-expired timer can still reach expiry when that predicate is
false. The model begins after the initial bit9 stack-reactivation phase, which
can clear suspension and reload duration. Other callbacks or
scripts can extend duration before that handler's final branch. Stack decrement,
zeroing and growth flags choose different reload/removal/suspension behavior;
branch priority is preserved in the synthetic tests.

Seven synthetic branch tests cover apply/inverse versus stub dispatch, local
versus submitted-command expiry, state/flag/predicate gates, callback extension,
conditional stack removal, growth and branch priority. These are normal-range
models of selected decisions, not a full buff emulator, native execution or
proof that any declared item buff was active in a recording.

## Jungle buffs and infusions (타격 강화제·수정 강화제)

Weapon Infusion means 타격 강화제; Crystal Infusion means 수정 강화제. Canonical
`Buff_Item_WeaponInfusion` and `Buff_Item_CrystalInfusion` identifiers are retained.

The 15 selected buff definitions retain exact resource identity, indices, icons,
stack capacities and factory registration. These are declaration candidates,
explicitly not production-ready decoders. Infusion capacity 12 is a buff stack
capacity, not twelve consumables or cooldown charges.

CrystalOrb links to `Effect_Blue_Buff`; WeaponOrb links to `Effect_Red_Buff`.
This establishes visual identity only. Actor resource localization GREEN/ORANGE
remains a separate observation, and older TreeEnt/CrystalMiner families are not
merged into these 5v5 families.

Infusion reapply script lists contain a real refresh handler restoring original
duration. This can run even though Lifetime's generic reapply slot is a stub.
TreeEnt Restore instead expands duration only when the incoming value exceeds
the remaining value. Its heal/recharge paths and infusion stat commands retain
mode gates. Tick cadence, delivered healing, dynamic stack/level ordering and
final stat aggregation remain unresolved.

Infusion item DURATION is 150; TIME 2.5 is a different property. Selected stat
intercept/delta declarations interpolate endpoints at stack 1 and 12 under the
stated algebraic model. They do not prove applied server totals. Selected orb
death factories declare a 90-second operand, but their ApplyBuffToSelection
helper setters and execute slot are stubs in this client. Successful acquisition,
automatic transfer, and observed duration are not established.

Five portable tests check candidate non-production status, resource-scoped
capacity, refresh flag handling, extension versus refresh and conditional
real-number interpolation. Build-bound native checks remain external evidence.

## Status flags, action gates and cleanse

Status contributions are stored as separately owned, generation-checked children.
The selected collector ORs up to 128 masks. Removing one contribution recomputes
the aggregate, so overlapping flags can survive. Pre-add callbacks receive a
mutable mask; factory declarations are not unconditional final actor flags.

Selected Stunned, Silence, ItemSilence and named roots configure different masks.
Movement, basic-attack selection, skill selection and the item-like definition
branch use different conditions and bypasses. A zero status-reason subset does
not establish readiness: other cooldown, energy, state and behavior checks remain.
An outer movement override does not guarantee success in the inner mover.

The selected slow collector takes a maximum per category, with directional
conditions and a cap. It does not sum equal-category slows. Its child collection
is bounded at 800, and removal can mark pending cleanup. A declared 0.5 operand
therefore does not prove an observed 50% movement reduction or immediate recovery.

Buff blockers match metadata and identities with mode and handle guards, among
at most 32 collected candidates. They are not unconditional immunity to every
status. Cleanse scans linked buff nodes, filters on definition metadata and queues
cancellation only in the selected mode; this is not synchronous erase-all.

Display records carry status text/enum and a buff identifier using their own
handle lifecycle. The identifier is not a remaining-time float. Display labels,
logical flags, particles and countdowns remain distinct. Effective inherited
item definitions and end-to-end countdown rendering are still unresolved.

Eleven producer-authored portable tests cover mask expansion/overlap, selected
skill/item/movement branches, maximum slow contributions and filtered cleanse.
They omit other readiness blockers and do not validate gameplay execution.
The catalog schema adds a status_effect category; production decoder code stays
unchanged.

## Wire-layout boundary

The native `043e` payload is 16 bytes and `043f` is 34. The common prefix contains
raw target/source actor IDs, half-float duration, instance and buff-definition
index. These IDs are not inferred object handles. Historical H5810 `043e` has
22 bytes; `043f` occurs with 34 and 38. The 22/38 variants remain unsupported.
Prefix-index comparisons are diagnostic only, and repeated section snapshots
prevent interpreting record counts as unique acquisitions or buff lifetimes.
No new production parser is introduced.

## Remaining evidence boundaries

The mode byte `0x0209e204` is intentionally not assigned an authoritative/client
semantic name. Exact historical active buff sets, observed capacities, dynamic
modifier updates and server behavior remain unresolved. Previously documented
Scout capacity/duration totals remain conditional on the declared controls
executing once against an unmodified base. Earlier research files remain frozen
historical snapshots; this extension closes only the generic dispatch gaps above.
