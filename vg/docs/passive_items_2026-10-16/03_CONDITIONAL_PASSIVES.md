# Conditional passive item declarations and factory graphs

## Starting basis and checks

This report separates item possession, the buff names declared by an item, native
factory construction, callback execution and accepted effects. It uses the selected
Windows x86 LAA build `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
All native offsets below are hexadecimal. Original exports remain private; their
acquisition identities are in REA_RECEIPT.json. No native execution, Ghidra query,
recording recount or production decoder change was performed by this reviewer.

The new passive_item_catalog research utility verifies the executable, the
LF-normalized inventory metadata, and every selected resource before decoding.
The original metadata's `659f9e...92642` build provenance remains separate from
the selected LAA executable. ITEM_CATALOG.json contains all 93 hash-checked item
declarations. All 12 independently extracted selected items agree on resource
hashes, definition IDs/names, active byte, passive/external/active-inline ability
names, and every declared property index/name/binary32 bit pattern. The comparison
normalizes hexadecimal formatting, not values. English/Korean localization proof
is referenced through NAMES_AND_DEFINITIONS.json and KOREAN_NAME_MAPPING.md;
translations are not inferred from English factory names here.

The item root+30 relocation points to a null-terminated array of relocated entry
pointers. Each entry's first word relocates to its buff-name string. It is not a
direct string-pointer array. Actual selected resources establish:

| Item definition | Declared buff entries | Native factory mapping |
| --- | --- | --- |
| 534 Item_CapacitorPlate | Buff_Item_CapacitorPlate_Control | 008ee2c0 |
| 533 Item_Pulseweave | Buff_Item_Pulseweave_Control; Buff_Item_Lifespring | 008f0b30; Lifespring covered separately in 02 |
| 531 Item_RooksDecree | Buff_Item_RooksDecree | 008f10f0 |

These links identify declared grant candidates. The grant/duplicate/remove
conditions in 01_OWNERSHIP_AND_STACKS remain required. A declared name is not an
observed active buff or proof that two item instances multiply its effects.

## Capacitor Plate

Exports012–014 show Control008ee2c0, Lockout008ee500 and SpeedBoost008ee570.
Control constructs a Lifetime callback and two ModifyAttribute behavior nodes
(005301d0, confirmed by095), configured with attribute/layer operands24/2 and22/0
and provider thunks008676d0/008676a0. It also constructs a Heal callback node with
selected packed settings, appends a target-selection behavior, and declares
application of Buff_Item_CapacitorPlate_Lockout using provider00867700.

Lockout constructs an application callback list through00810010 and declares
Buff_Item_CapacitorPlate_SpeedBoost through0052ec60, with provider00867730.
SpeedBoost constructs a Lifetime behavior through00530800 with provider00867760.
The item resource separately declares HEAL_AMP and BARRIER_AMP as binary32 near
.15, MSPD_STRENGTH1.5, MSPD_DURATION3 and LOCKOUT_DURATION15. These property labels
and values remain declarations; merely owning the item does not establish a heal,
barrier recipient, speed trigger, lockout start or successful attribute mutation.
The complete Heal callback's event filtering, target-selection executor, and
provider invocation must be bound before claiming every received heal triggers
speed or assigning an observed timer. Construction settings are not duration
measurements or unconditional eligibility rules.

## Pulseweave

Exports015–017 distinguish Control008f0b30, Active008f08e0 and Slow008f0ec0.
Control constructs Lifetime attribute12/layer2 with provider00867ae0. An additional
callback construction stores period operand.5. It builds nested ConditionalNew
nodes (0052f560) and ActorHasCooldown conditions (00813320) keyed by the signed-byte
FNV hash of `Pulseweave`; a nested branch also declares ActorIsAlive for the buff
bearer. The condition's name does not alone establish its inversion or readiness
polarity, and the .5 setting does not prove observed callback cadence.

The graph includes target-selection, DAMAGE_BURN lookup, ModifyCurrentCooldown
(005305c0) keyed by Pulseweave with provider00867b40, and ApplyBuffToBearer for
Buff_Item_Pulseweave_Active with provider00867bd0. CooldownOngoing construction
(008103f0) also binds the same key and configures an availability presentation
node. These are distinct internal keyed-state and buff declarations, not a new
replay cooldown reducer.

Active builds Lifetime behavior with provider00867b70, a trigger-ring effect,
and a second callback/list containing target selection, DAMAGE_BASE lookup,
Buff_Item_Pulseweave_Slow application with provider00867ba0, and an explosion
presentation effect. Names and constants do not certify hostile selection,
actual damage, radius filtering or successful slow application.

Slow008f0ec0 resolves the actor identified by buff+21c. If it resolves, it reads
Item_Pulseweave properties5 and6 with selector1, combines property5 plus
property6 times actor component+d4, then calls008e2b90. The local resource labels
these SLOW_BASE_STRENGTH and SLOW_BHP_SCALING. Without tracing component+d4 and the
consumer, this is a field-level provider formula, not an independently certified
bonus-health stat interpretation. Other properties include COOLDOWN45,
TRIGGER_TIME3, SLOW_DURATION3 and BURN_RADIUS2.7; none is an observed remaining
timer, universal runtime radius or accepted effect duration.

## Rook's Decree

Exports018–020 identify Control008f10f0, AttackBuff008f11d0 and Barrier008f13c0.
Control constructs AbilityActivated callback0080f9e0 (confirmed by094), adds a
ConditionalNew node with the RooksDecree keyed ActorHasCooldown condition, and
declares application of AttackBuff. It separately adds removal of AttackBuff on
another callback list. The full AbilityActivated executor and condition polarity
are not recovered by constructor inspection alone; any successful ability,
attack or damage cannot be substituted for that missing event contract.

AttackBuff initializes a keyed `Consumed` value to false, creates a Combat
callback008102e0 with selected masks/settings, and attaches another conditional
node. Its configured sequence includes callback008358b0, ShootProjectileNew
(00532410, confirmed by093) with operand29, ModifyCurrentCooldown keyed
RooksDecree with provider00867c00, a Consumed-variable update and AttackBuff
removal. This supports a conditional consumption/projectile/cooldown graph,
not proof of the triggering attack category, accepted projectile impact,
recipient barrier or all duplicate-item behavior.

Fresh092 shows008358b0 resolves buff+21c, fills projectile-context fields using
the buff bearer's actor position, sets packed options and a float operand144.
Those assignments do not identify every projectile consumer or its actual hit.
Barrier factory008f13c0 configures0052fb10 with resource operand4 and provider
008362c0. Fresh089 provider reads raw integer buff+21c and combines its unsigned-
conversion expression with property0 plus property1; properties are labelled
BONUS_HEALTH_RATIO(.15) and BARRIER_STRENGTH150. The raw+21c operand is not proven
to be bonus health, so the label cannot repair the pseudocode into a certified
bonus-health formula. Resource4 configuration is distinct from actual barrier
application, and the provider's second output is a -1 sentinel. This unresolved
operand interpretation is retained explicitly rather than guessed from tooltip
language. Item COOLDOWN10 and DURATION2 likewise remain local declarations.

## Closed result, limits and next measurement

Closed: item-to-declared-buff indirection, the three selected native factory
graphs, named internal cooldown keys, and the distinction between construction,
provider calculation and accepted effect. The catalog exposes active capability,
presentation-hidden flags and item quantity rules separately from these graphs.
No possession-to-conditional-effect inference is introduced.

Remaining boundaries are callback executor masks/polarity, accepted owner/target
and ally/range selection, actual loaded resource identity, keyed-state lifetime,
duplicate sharing, sale/child cleanup and engine-clock progression. On a matched
build trace item instance and declared name through grant; callback type/context;
source, bearer and target generations; provider inputs; queued action and accepted
resource/buff changes; cooldown key and timer state. Vary duplicate equip, removal,
healing without barrier, blocked/rejected damage, ability activation without hit,
missed projectile, death and sale/rebuy independently. The absence of a matching
accepted downstream action falsifies an unconditional-effect claim. No runtime or
historical replay correctness is certified by this report.
