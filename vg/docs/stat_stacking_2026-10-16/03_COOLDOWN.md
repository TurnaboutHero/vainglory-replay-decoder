# Cooldown duration, rate and item declarations

This is static evidence for the selected LAA executable SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
Addresses are preferred x86 VAs. The installed assets are hash-checked local
declarations; an actual recording/server build match remains unknown.

## Duration calculation and units

The complete assembly in
`evidence/2026-10-14-cooldown-events/pass6/0086bbf0.txt` establishes this finite-input
operation order for a cooldown state supplied in ECX:

1. Read override at state+38. If negative, instead add base+2c and additive+30,
   then multiply by state+34.
2. If state+48 bit1 is set, evaluate effective stat25 and multiply duration by
   `(1 - r)`, where `r` is upper-clamped then lower-clamped.
3. If state+48 bit2 is set, evaluate effective stat15, clamp it, then divide
   duration by `max(1, s)`.

Thus `r=.2` means a fractional 20% duration reduction, not a flat 20 seconds and
not a haste-points formula `1/(1+.2)`. `s=1.2` produces division by1.2 only when
the separate flag is enabled. The two enabled factors compose in that order;
they are not added together. Each SSE arithmetic step rounds independently.
This finite description does not replace the native COMISS/MINSS/MAXSS behavior
for NaN, infinities or signed zero.

With `A` denoting the actor's component at validated handle+20, native inputs are:

```
r0 = ((A[+2a0] + 1) * A[+138] + A[+84]) * (A[+1ec] + 1)
r  = max(lower[01a760fc], min(upper[020e73ac], r0))
s0 = ((A[+278] + 1) * A[+110] + A[+5c]) * (A[+1c4] + 1)
s  = max(lower[01a760d4], min(upper[020e7384], s0))
```

These expressions read already accumulated actor fields. Item-entry raw operation
codes alone do not prove which accumulator receives a contribution. Fresh PE
verification corrects the earlier lower-bound attribution: stat25 lower01a760fc
is float32 zero, not -FLT_MAX. Stat15 lower01a760d4 is float32(.5). At0044e081,
bytes `c705ac730e023333b33e` initialize stat25 upper020e73ac to bits3eb33333,
approximately.35. [PE_CHECK.json](PE_CHECK.json) reproduces this SHA-gated store.
Fresh xrefs011 list0044e081,0086990d and0086bc42 for this upper global;
the last two are getter references. Lower-global xrefs012 list00869919 and
0086bc7d. This supports the selected static initialization/read graph, not an
immutable35% server cap: the function reads writable globals every evaluation,
and direct xrefs do not exclude indirect writes. A different write, patched
startup, or runtime bound value falsifies a universal35% claim.

The output is a nominal duration. `00956380` calls `0086bbf0` when constructing
a replacement recharge timer and writes it to timer initial+20 and remaining+24.
`009686d0` subtracts engine delta from remaining+24 only when pause+28 is zero.
The duration unit is the same engine-time unit as that delta; the selected timer
code alone does not certify its wall-clock-to-seconds calibration.
See [the timer closure](../sequential_rea_2026-10-16/01_COOLDOWN.md).

## Applicability is per state/definition

The complete `0093f270` extraction at
`evidence/2026-10-14-cooldown-followup/ability-identity/receipts/0093f270.txt`,
instructions0093f44b..0093f46c, initializes state+48 bit0 from definition+6d bit0,
bit1 from definition+24 bit0, and bit2 from definition+25 bit0. Existing shared
state reuse bypasses this initialization. It is unsafe to classify every item,
every ultimate, or every later same-key state using a universal slot number.
Prior RingoC/KrulC examples have low bits3, enabling stat25 but not stat15.
This is a definition example, not an all-hero ultimate rule.

The new93-item pinned scan finds32 active inline ability declarations. All32
have ability+25=0. Ordinary active boots, Fountain487, Crucible488, WarTreads497,
Atlas498, Contraption516, Nullwave521 and scout items have ability+24=0 as well.
Their newly initialized states therefore bypass both modifier factors through
this calculation. This remains true even when an item grants stat25 to its owner:
HalcyonChargers490 and Nullwave521 are concrete examples. Infusions493/494 and
candies514/515 declare+24=1; several developer/helper definitions also do so.
Do not generalize ordinary-item behavior to every catalog entry. Nonactive keyed
item state creation in00940230 explicitly clears state+48's low three bits.
External-ability declarations require their external definition instead of inline
bytes. Later state changes/shared reuse still require separate evidence.

## Pinned local item attributes

`vg.research.cooldown_item_declarations` decodes only the93 existing metadata
resources, checks the selected executable, each resource SHA-256 and exact item
symbol/name, and follows relocations. Item+2c is a null-terminated pointer array;
each entry has statID+0, raw float+4, raw secondary+8 and raw operation+c.
It emits exact bits, resource IDs/hashes, quantity rules and inline flags without
inferring effective values. Allocated empty external strings select the same
inline branch as null strings. Catalog metadata normalized-LF SHA-256 is
`e40df722ee5eaff7ff63e21403944bbf6de35eb84126f8fe0ce27e7bc66d0783`;
its original executable attribution remains distinct from selected LAA validation.

All ordinary stat25 declarations below have secondary bits00000000 and raw
operation2. Decimal values are readable approximations of the exact bits.

| Definition | Index | Stat25 value | Float32 bits |
|---|---:|---:|---|
| Hourglass |473|.075|3d99999a|
| Chronograph |475|.15|3e19999a|
| Clockwork |476|.20|3e4ccccd|
| HalcyonChargers |490|.10|3dcccccd|
| Aftershock |492|.15|3e19999a|
| Contraption |516|.20|3e4ccccd|
| Stormcrown |519|.20|3e4ccccd|
| NullwaveGauntlet |521|.15|3e19999a|
| Spellsword |524|.20|3e4ccccd|
| SuperScout2000 |527|.20|3e4ccccd|
| ScoutPak |529|.10|3dcccccd|
| RooksDecree |531|.05|3d4ccccd|
| CapacitorPlate |534|.15|3e19999a|

VideoHelper541 and CooldownDamageSelf547 instead declare stat25 value1200
(44960000), raw operation1. These helper definitions are not ordinary loadout
recommendations. Stat15 declarations include SwiftShooter460=.1,
BlazingSalvo463=.2, TornadoTrigger466=.4, Bonesaw482=.3, Shiversteel484=.2,
BreakingPoint507=.2, AlternatingCurrent509=.4 and PoisonedShiv520=.35;
their presence does not turn stat15 into stat25 or enable the duration flag.

All13 ordinary stat25 items declare quantity `stackable=false,max_stack=1,
grant_skip=false,unique=false`. Those are inventory declarations, not proof of
two-slot purchase permission, repeated grant execution or independent passive
stacks. Fresh020 assembly resolves0092f980's constructor arguments. Gated by
0209e204, it walks item+2c and queues0092e8e0 when entry+4>0. The constructed
ActionModifyActorAttribute has +18=entry statID, +1c=1, +20=entry+4, +24=false.
The alternative positive entry+8 branch uses +1c=2. Crucially, neither branch
copies entry+c: raw declaration2 is not action layer2. Fresh021 clones this
action, and0690094f1d0 resolves the actor and dispatches +24=false to0093e850.
Fresh0870093e850 forwards to0093e940 with its final argument zero.
Fresh0270093e940 adds the operand to the layer selected by00937480, then calls
0095c710/0095c590 to store it. Layer1 and layer2 are distinct accumulators;
this grant evidence must not be replaced by a guessed raw operation-code mapping.
Fresh110 assembly at0093e870 loads the attribute-component pointer from
actor+20 before0093e940. Fresh111 at0093ea94 then uses
`LEA ECX,[component+20]` before00937480. This closes the otherwise misleading
offset difference: generic layer1 stat25 is payload+b4+25*4=payload+118,
therefore component+138, exactly the input read by0086bbf0. Generic layer1
stat15 similarly corresponds to component+110. The ADD operand is rounded back
to float before the setter call. Ordinary accepted grants thus add into the
layer1 input before its layer3 scaling in this expression, rather than multiplying
independent `(1-itemFraction)` factors.00872340 contains the corresponding
removal walk.

Conditional numeric witnesses use neutral other actor layers, each accepted
ordinary item grant exactly once and unchanged startup bounds. Two accepted
Clockwork contributions add .20+.20 before effective stat25 clamp. The capped
fraction is float32(.35), not.40 or multiplicative.36. A base90 duration yields
bits4269ffff, approximately58.499996, because SUBSS(1,float32(.35)) rounds before
MULSS; the double-precision simplification58.5 loses that one-ULP distinction.
A single effective.20 gives90->72. An override50 still receives the flagged.20
factor and becomes40. With both flags,100*.8/1.25 becomes64, while speed.5 is
raised to1 and leaves100 unchanged. These are explicitly conditioned arithmetic
witnesses, not measured loadouts or permission to buy duplicate items.

## Direct duration edits and running time remain separate

Existing named ModifyMaxCooldown evidence (0081d600,0093f210,009618c0,
00962a90,009542d0; dictionary entryVGRE-cooldown-buff-duration-modifiers)
distinguishes additive state+30, multiplicative+34 and override+38. Inverse
removal subtracts/divides or resets override to-1; it does not restore a saved
prior override. Update uses new-minus-old or new-over-old. Selected multiplier
inverse/update methods have no local zero-divisor guard. The selected methods
do not write current timer remaining+24. A maximum-duration modifier therefore
does not itself prove an immediate subtraction from an already running timer.
ScoutPak/SuperScout/Standard3v3 declarations of -30/-30/-10 concern additive
nominal duration, not a universal direct remaining-time reduction. Fresh005
0093f210 constructs the target key hash and stores mode+18; fresh006/007/008
corroborate apply/remove/update. They scan up to0x4b0 states and choose the first
matching state+28 hash, not an inventory instance predicate. Apply evaluates
005f9280 and saves the operand+14; inverse/update reuse that saved operand.

## Reproduction, boundaries and falsifiers

Run with explicit local executable and Data paths:

```
python -X utf8 -B -m vg.research.cooldown_item_declarations --binary <selected-LAA-exe> --data-root <Data>
python -X utf8 -B -m unittest tests.test_cooldown_item_declarations -q
```

The focused9 tests check nonfinite raw bits, negative-zero secondary bits, raw
operation preservation, allocated-empty versus named external ability selection,
missing relocation rejection and inactive-item exclusion. The local93-resource
scan also completed with all input hashes checked. These tests validate extraction
boundaries and explicit finite float32 arithmetic witnesses, not gameplay
execution. The witness rejects nonfinite inputs while the extractor preserves
their bits; speed bounds must be supplied explicitly. The combined declaration,
existing cooldown model and cooldown timeline suites pass25 tests. Existing
production parsers remain stateless.

Falsifiers/remaining checks: a different item resource hash or relocated symbol
rejects the declaration; a runtime flag/bound write invalidates initialization-only
predictions; a running-timer write outside the named modifier methods can change
remaining time; duplicate inventory slots can share a key/passive or be rejected
before grant. Observing a hero's ultimate requires its exact definition and selected
state, not native slot2. Native execution, server rules, actual loadouts and all-hero
ultimate applicability are not established by this report.
