# Lifesteal declarations, shared buffs and heal-production boundary

## Verified names and starting basis

01_NAMES_AND_ITEMS.json verifies installed Korean localization keys and the
selected item resources. 바다뱀의 가면 is Item_SerpentMask, definition479;
맹독 단검 is Item_PoisonedShiv, definition520. The no-space user spellings are
explicit whitespace variants, not exact localization strings. This report uses
selected LAA SHA256d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc;
original catalog build659f9e...92642 remains distinct. Addresses/offsets are hex.
It does not substitute telemetry Vampirism naming for a native heal producer.

The two item resources are hash-checked CFF version12 declarations. SerpentMask
resource1CDE66CE2915BAE2CEE39077344885DB has SHA256
02aae9198736394ede481b527137c640ca41886527dafb1d1b3cced2684cea0d;
PoisonedShiv C004022B19B8B95312D035BB04DEDB4F has SHA256
caabdb31018b31f412d8e6dcd246e17e246e0c9ede5bf9903f94cbdecf7e08c8.

## Separate fixed attributes, item properties and buff capacities

SerpentMask fixed-stat list declares attribute4 with operands70/0 at entry+4/+8.
PoisonedShiv declares attribute4 operands35/0 and attribute15 operandsapproximately
.35/0. These entries are not lifesteal percentages merely because the item also
has VAMP properties. Native fixed-attribute application and the effective layered
getter determine any duplicate accumulation rule.

| Item | Property index and exact declared value bits | Declared value |
| --- | --- | --- |
| SerpentMask |0 VAMP 3e800000|.25|
| SerpentMask |1 CAP_MIN 43c80000;2 CAP_MAX 44480000|400;800|
| SerpentMask |3 RECHARGE_TIME 42f00000|120|
| SerpentMask |4 OMNI_VAMP 3e19999a|approximately.15|
| PoisonedShiv |0 Hits_To_Proc 40000000;1 Mortal_Wound_Duration 40000000|2;2|
| PoisonedShiv |2 VAMP 3dcccccd|approximately.10|

Both item metadata rows declare max_stack1,stackablefalse,uniquefalse. This is
inventory quantity/eligibility metadata; it proves neither additive lifesteal
per copy nor a unique-passive exclusion between different items.

The relocated item+30 entry lists declare:

- SerpentMask: High_Vamp,BookOfEulogies_Control,SerpentMask_Control,UnifiedVamp_Control.
- PoisonedShiv: Mid_Vamp,UnifiedVamp_Control,PoisonedShiv,BookOfEulogies_Control.

All names above have Buff_Item_ prefix. The separate hash-checked KindredBuffs
resource551BCB541D80053BACD0A897B7993A77 SHA256
e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79
declares reuse policy0 for these selected buffs. SerpentMask305 has cap1200;
Control306,PoisonedShiv309,Payload310,BookOfEulogies_Control325,Mid_Vamp327,
High_Vamp328 and UnifiedVamp_Control329 each have cap1. The cap1200 is not silently
replaced by the item property's400/800 range. Which provider initializes or
consumes these counters must be traced separately.

## Existing duplicate and cleanup bridge

Prior01_OWNERSHIP_AND_STACKS in passive_items_2026-10-16 establishes conditional
mode-nonzero00865e30 lookup of the owner's active buff by name hash+228, reuse of
its instance ID+220, queued application and recording that ID in each item's
ledger. Policy0 generic00863050 reuses an active name without policy1's additional
bestower check; reapply callbacks can veto/change behavior. A cap-one active
control can consequently be shared conditionally between multiple owned items.
00870c30 preserves a current1/cap1 buff when another item ledger references the
same ID, otherwise queues cancellation/decrement. Queue ordering, pending create
reconciliation and accepted downstream application remain conditions.

Thus two copies do not justify two independent UnifiedVamp controllers. Conversely,
shared controller identity alone does not prove its provider chooses sum,max,
priority or a product: that requires the actual provider and inventory predicates.
Fixed weapon/attack-speed declarations must remain separate from shared passive
callbacks, temporary Serpent capacity and final healing.

## Native registrations and callback paths

Existing exact registry candidates identify SerpentMask008f1a50,
SerpentMask_Control008f1b10,UnifiedVamp_Control008f35b0,
BookOfEulogies_Control008eddf0 and PoisonedShiv008f0500. Low/Mid/High_Vamp and
PoisonedShiv_Payload map to the already-known empty00450910 address; a stub factory
does not negate declaration flags or other consumers of those marker definitions.
Fresh015–019 complete factory exports establish the following selected graph.
SerpentMask008f1a50 sets lifetime suspension flag4 and, only under mode nonzero,
registers onBuffInterval to0083d520 and onAfterApplyDamage to0083d320. Its Control
008f1b10 builds an application list referencing SerpentMask and reads CAP_MAX
property2; fresh074assembly supplies the lost float/call operands below.
UnifiedVamp_Control008f35b0 builds a Combat callback with selected mask10 and
registers00844f00 through a script behavior. BookOfEulogies_Control008eddf0
initializes Guid_lastMinionProced=-1 and registers onBeforeApplyDamage00839b50.
PoisonedShiv008f0500 registers onAfterApplyDamage0083cbc0 and a list naming its
Payload buff. The callback bodies055–059 and selected assembly071–074/096 refine these
registration facts below. Actual dispatch context remains distinct from factory
construction; no second session is started here.

## Unified coefficient selection and separate conditional contributions

Fresh055/07100844f00 checks High_Vamp first, then Mid_Vamp, then Low_Vamp.
08600868d00 locates the actor buff manager and calls105009320d0: the latter
walks manager+14 links+260 and returns true for matching name hash+228 with
state+224==0, otherwise false. These tests concern active named marker buffs,
not counts of inventory definitions. High
selects Item_SerpentMask property4 OMNI_VAMP (approximately.15); Mid selects
Item_BarbedNeedle property0 VAMP (approximately.10), and Low selects
Item_BookOfEulogies property0 VAMP (approximately.05). No matching marker yields
zero. Supporting provider resources are independently hash-checked in01. This is
an explicit ordered choice, not a sum of .15+.10+.05, an unrestricted numeric MAX
operation, or use of PoisonedShiv property2 merely because its label matches.
The callback then adds the selected value to a context-derived combat field+28.
That write is coefficient accumulation, not a heal action. Duplicate invocation,
other contributors and final consumption require their own dispatch proof.

The Combat constructor093 initializes the filter fields, and factory017 sets
event mask10 and source-owner mode1. Fresh10200947cb0 calls predicate1060095fa10
before constructing behavior context and dispatching its list. Under these
selected defaults, the predicate requires `(eventSelector & 31)==4`, combat source
ID+0c equal to the buff bearer, and a type bit accepted by default byte38=ff.
Required flags are0, any-flags mask isffff, excluded flags are0, and optional
extra predicates remain unset. This is an exact filter configuration; the low-five-bit event selector4
and type indices are not renamed physical/ability/AOE without their producer.
The percentage is therefore selected once per eligible shared controller
callback, not once per inventory copy by this code alone.

Fresh0560083d320, registered by SerpentMask only in mode nonzero, requires the
combat source-ID operand+0c to match the bearer, target actor flags+1e0 bit0,
and combat word+4==0. With positive combat+44, it computes a contribution from
that operand times Serpent property0 (.25), limited by calculated missing health
and current low16 buff stacks times .25. It adds the contribution to combat+4c
and queues a stack adjustment through0092ea80. This is a separate conditional
capacity-backed contribution; it is not the Unified marker's .15 coefficient.
Fresh072assembly closes the queued operand: divide the selected contribution
by .25, convert via011b8a40, subtract the integer result from current low16
stacks, then queue absolute count mode1 using vtable0127c9f0. Exact conversion
semantics and exceptional/nonfinite domains are not guessed. This adjustment
is still queued, not an accepted immediate stack mutation. The script's use of combat+44 is not relabelled as actual
health loss without the producer/consumer chain.

Fresh073assembly resolves the Serpent interval's lost arithmetic. It calculates
an effective actor-component value S from fields+2dc,+174,+c0,+228 and image
bounds; it then uses factor(S-1)*image constant012928bc to interpolate CAP_MIN
and CAP_MAX, converting the result through011b8a40 to a target count K. It queues
absolute count convert(min(float(K),float(current)+float(K)/RECHARGE_TIME)) using
the same action/vtable/mode1. No engine delta is multiplied in this callback.
The effective value S is not called actor level without its getter proof, and
an interval invocation is not a certified elapsed second. Thus the declared120
operand cannot be promoted to an observed120-second recharge. Generic setter
capacity and actual scheduler cadence remain separate. Fresh074/060 also bind
Control's list+34 ApplyBuff node name to SerpentMask, duration-1 and integer
CAP_MAX initial stack operand800; list+40 names its removal. The800 initial
operand and resource definition cap1200 are distinct static inputs.

Fresh05800839b50 is registered before damage application. It checks matching
source, positive target health<=combat+44, target classification mask110, and a
Guid_lastMinionProced deduplication field. It chooses Book property1 HEAL_RANGED10
or property2 HEAL_MELEE30 under a definition-byte/combat-bit condition, stores the
target ID as the last processed ID, initializes a plain14-word context through0081e780 with bearer as source and
target and the selected amount. Fresh096assembly resolves the next call at
00839cd2 DIRECTLY to00450910, the known empty return. It is not a forwarded
heal action and the decompiler name guard_check_icall must not hide that stub.
The last-ID write occurs before this empty call. This selected client body has
a real context/deduplication calculation but no implemented heal operation at
that terminal edge; it certifies neither a kill nor health recovery.

Fresh0590083cbc0, registered after damage, requires a valid target, matching
source and combat-byte8 mask4. It searches an active Payload buff by its name key.
When its current count matches Hits_To_Proc-1 it queues Buff_MortalWound to the
target for property1 duration and cancels the payload; otherwise it queues the
Payload on the bearer. The selected declared threshold2/duration2 are distinct
from vamp coefficients. This callback does not itself produce lifesteal healing.

## Remaining heal-production and runtime boundary

The selected Book terminal edge is closed as an empty client implementation;
0081e780 is context initialization, not a native action constructor. Combat callback eligibility/dispatch is narrowed by102/106 as above. Remaining
downstream checks are the caller-supplied event-selector meaning and the producer
and final consumer of combat+28,+44,+4c. Serpent selected interval arithmetic is established,
but its scheduler cadence, effective S interpretation and conversion environment
are not independently observed. Thus native eligible damage categories, base
damage versus applied health-loss operand, AOE coefficients, final heal recipient
and resource mutation are not certified by the factory names alone. Prior
ImpactHealth evidence separates early notifications, protective allocation and
final resource mutation. Negative input can be fully absorbed without positive
health loss. No production heal calculator is enabled.

The falsifying trace must bind item/buff/actor generation, distinct fixed layers,
marker buffs and provider selection; compare Serpent duplicates, Shiv duplicates
and a mixed pair; vary attack/ability/periodic/AOE damage, shield absorption,
nonhero targets and rejected damage. Record the exact eligible damage operand,
remaining capacity, proposed heal and accepted resource0 mutation including max-
health/healing modifiers, then cleanup and recharge clock. Until that chain is
available, local declarations support candidate research, not a runtime lifesteal
calculator or historical-build certification. No production decoder is changed.

## Bounded stacking answer

For the selected loaded definitions and active buffs, the Unified provider chooses
one tier: High(.15) supersedes Mid(.10), which supersedes Low(.05). It neither
adds tiers nor multiplies them. Shared policy0/cap1 controls and marker buffs
provide a conditional duplicate-identity route; they do not create a new .15
contribution for each observed Serpent inventory copy. Serpent's separate .25
capacity contribution is additive to combat+4c, while the Unified tier updates
combat+28. Combining those different fields into an unconditional .40 heal rate
would skip the unresolved damage/filter/consumer chain. PoisonedShiv's own
post-damage callback supplies Payload/MortalWound behavior; its VAMP label does
not override the Unified selection of BarbedNeedle's .10 property for Mid.
Fixed attribute declarations, shared passive identity, temporary stack capacity,
coefficient accumulation and accepted resource healing are five separate layers.

Closed reason: current resource and native bodies resolve tier priority, shared
instance conditions, separate Serpent capacity arithmetic and the exact Book
client-stub boundary. They do not reveal an implemented final lifesteal heal
consumer in this selected slice. Further arbitrary item-count correlations or
historical descriptions cannot replace that implementation/runtime dependency.
