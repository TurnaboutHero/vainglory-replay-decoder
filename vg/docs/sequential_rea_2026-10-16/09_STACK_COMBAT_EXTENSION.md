# Extended resource, interval and combat boundaries

Base326582d; selected LAA SHA256d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc.
+offsets are hexadecimal. Acquisition IDs are in EXTENDED_REA_RECEIPT.json.

## Resource load and application override

Start:05_NAMED_STACKS proves local KindredBuffs cap5/15 and definition+24 to buff+252.
Next: follow runtime name lookup,resource registration/replacement and action+38/+3c override.

0260112a790 returns context/arena manager020ec81c.0610112ab50 assembly uses
manager+0c array indexed by its first argument,then0112c050 hashes the symbol
with0096c7a0/004c4450 and searches that arena's tree+0c. A matching entry returns
entry+14 and optionally metadata+18;missing returns0. This is lookup of registered
memory,not hashing a resource file to prove which bytes are loaded.
046/076 show context manager and per-arena tree construction.087/088 resolve the
same teardown0112b180,which releases trees/arena storage and clears globals;not
an alternate resource-load path.07501129ea0 looks up a named root and applies
registered type callbacks,using optional temporary allocation context and then
restoring it. Parameter roles omitted by the decompiler remain bounded.

101004bf790 supplies a concrete missing-manifest route: if *KindredManifest* is
not registered,it calls0112b080(0,build://Levels/DefinitionManifest.def),then
01129ea0(*KindredManifest*,0,-1,0).0480112b080 delegates to installed manager+10
virtual+4 when present. This establishes the dependency/loading interface and
manifest lookup;it does not prove the actual runtime KindredBuffs file hash,
all replacement policies or inheritance/override values. Existing local declaration
hashes do not certify loaded memory. Full resource selection remains runtime/provider
boundary rather than a claim that item MAX controls capacity.

0970094c9a0 assembly corroborates action+38 handle/+3c generation validation and
nonzero-mode callback override+1c.0780081a060 initializes that handle NULL and its
generation sentinel;selected new callers085/086 use the ordinary constructor path.
Those callers concern reveal/Flicker warning buff declarations,not proof of a
custom cap/override. No non-null override producer or callback implementation was
identified. Ordinary application still checks definition permissions and actor
flags before008659c0;that helper's existing mutable pre-receive callbacks and
reapply veto prevent declaration==effective-state inference.

## Interval registry to callback cadence

Next check00954aa0 turned out to register generic buff type and cooldown event
handlers,not to be the interval dispatcher itself. Its update registration is
stage4 callback00967a20.039 name-pointer references lead to that tick and timeout
00966410.043/062 assembly close the actual tick fields and ordering:

- Ending state+224==2 returns. Lifetime flags govern duration+22c independently.
- While state+224==0,interval remaining+234 subtracts engine delta and elapsed+238
  adds delta. At remaining<=0 it dispatches native list+48,then script interval,
  resets elapsed+238 to0,and adds period+23c to remaining+234 ONCE.
- There is no loop to deliver every missed interval in this regular branch.
  Negative debt can persist into later updates. This differs from setting remaining
  equal to the period and from dispatching floor(delta/period) times immediately.
- Lifetime timeout00966410 can additionally dispatch an interval when packed
  flag bit8 is set,before timeout callbacks. If the buff remains active,the later
  regular interval branch can also run. Therefore one regular dispatch per tick
  is not a universal one-interval-callback-per-frame guarantee.
- The generic update still depends on stage4 dispatch and global publication
  guard. Dragon's Eye's separate lastDamage/lastStack gate and mode!=0 remain
  additional conditions. A declared .2 period is not proof of live 5 Hz cadence.

0700086f110 matches the event name hash,sets __PARENT__ context,and dispatches
0086ef20. Prior registered Dragon callback then performs its own one-adjustment
check. No native execution or catch-up timing was observed.

## Health preparation, notifications and final resource mutation

Start:02_REWARDS retains damage source before resource application;05 links
pre-calculation callback to Dragon timing. Next: producer/notification ordering,
shield allocation and actual mutation,not another reward formula.

081 finds0086eb50's two direct callers:existing apply0094e970 and new0094af20.
107 table words place0094af20 at ActionImpactHealth vtable0127c928+4 (SERIALIZE),
0094e970 at+8 (APPLY),and clone0092e690 at+c.110 RTTI names ActionImpactHealth.
Thus0094af20 must not be presented as a second direct health-apply function.

084/095 serializer resolves target,then for finite negative input calls0086eb50.
When action+23 is zero and actor+1f8 mask10 is clear,it adjusts the residual
health output if resulting actor component+2f0 would be<=0,leaving1 before
recombining outputs and writing action+18. This is a conditional nonlethal
preparation rule,not an immunity rule or universally applied damage formula.
Under0209e204!=0,it serializes target/source and operands via008167c0.
096/104 show that helper wraps opcode041e with16payload bytes (18opcode+payload
bytes;additional transport envelope length prefix is separate),optionally uses
an installed transform,and reaches004cfea0→004eb3f0→installed transport virtual+30.
This is static reachability only;no network send was performed. Historical replay
padding/framing and server validation are not inferred from that wire helper.

030/0830086eb50 zeroes four output deltas. Finite positive input goes to main pool.
Negative input first consumes positive component+300,then uses min(+304,+2f0)
for the second protective allocation with factor.5. Residual routes to main or
alternate health according to actor+1f8 mask10. Numeric operations are binary32;
NaN/nonfinite behavior is not promoted. Calling the helper calculates outputs;
it does not itself store actor resources.

106/108 apply0094e970 first rejects missing target and an already nonpositive
selected health pool (+2f0 or+2f4 by mask10). With a source and negative input,it
retains source/eligible hero and dispatches onTakeDamage then onDealDamage BEFORE
the allocation call0094eca5 and resource writes. Nonzero outputs change resources
4,5,0,1 at0094ecdd/ed12/ed33/ed54. Later actor presentation callbacks have additional
gates. Therefore a negative input or these early notifications does not imply
positive actual health loss: full protective absorption is a static counterexample.

The onPreCalculateDamageExchangeName pointer/string xrefs inspected here are
registration sites,not a recovered authoritative calculation producer. The complete
rejection/immunity pipeline before received/queued ImpactHealth remains unclosed.
No server damage rule,kill credit or award recipients follow from this slice.

## Closure, falsifiers and next measurement

Closed: registered-name lookup versus file identity distinction,manifest dependency
load interface,NULL default apply override,stage4 regular interval debt behavior,
ImpactHealth serialize/apply roles,conditional nonlethal preparation,and notification
before final resource mutation. Runtime loaded hashes/custom override,actual interval
execution and authoritative pre-calculation/immunity remain explicit boundaries.

Falsify on matched build: capture arena index,symbol lookup returned pointer and
actual loaded resource hash;action handle/generation/custom callback;buff instance,
ending state,flags,remaining234/elapsed238/period23c,delta and each regular/timeout
interval call. For combat bind action generation,input flags,resources0/1/4/5 before,
serializer-adjusted operand,server response,early hooks and separately final deltas.
Test fully absorbed damage,nonlethal request,missing/dead target,alternate pool and
changed protective state between serialization/application. Reject identity changes.
No new decoder rule is enabled because historical identity and live outcomes remain
unverified. Token-text parser guesses and unrelated/interior queries are excluded
from conclusions and cannot be counted as discoveries.
