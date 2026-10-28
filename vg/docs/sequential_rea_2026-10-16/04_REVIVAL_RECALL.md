# 4. Revival timer expiration and recall boundaries

Starting evidence: RESPAWN_CALLER_FOLLOWUP_2026-10-16.md and
re_dictionary/respawn_recall/REPORT.md. Prior inline constructor searches did
not prove exhaustive producer absence. Selected SHA is in README.

## Newly closed conditional respawn producer

Fresh type-global01ef0b44 references lead to00954e40 registration. Assembly
00955b64 pushes00953990,00955b69 pushes slot3; registration sets current descriptor
constructor009588e0,size1c,type global01ef0b44, then calls0112af70 at00955bff.
0112af70 writes descriptor+slot*4 and optional flag bits. Thus00953990 is the
registered CKinRespawnTimer callback at descriptor slot3; this is not an asserted
wall-clock frequency or full scheduler execution proof.

00953990 reads delta via0112a7a0, performs SUBSS/MAXSS into component+14, and
checks zero (including an initially zero value; not only a positive-to-zero crossing). At zero, **only when0209e204!=0**, it reads position from the pointer
at component+18 (+18/+1c/+20 within that object), reads owner actor ID+178,
constructs an ActorRespawn **inline** on the stack with vtable0127c6d0 and header
byte0, and calls0092d820 at00953a50 with queue020db890. No00819f70 constructor
call is needed, explaining the earlier constructor-reference search gap.
It also constructs Buff_SpawnStage_Recharge(duration operand2.0,stack7) and
Buff_Shop_AllowStorePurchase(1.5,stack1) actions, then calls0112a080. Fresh130 shows that helper ORs the corresponding pooled-object bitmap bits; it does not itself establish immediate free/removal timing. These are queued declarations, not observed buffs or universal durations.

Existing queue evidence now connects this local zero-header action:0092d820
clones/enqueues;00931bd0 calls serializer+4, then under0209e204!=0 apply+8;
0127c6d8 points0094c950→009572b0, the known existing-actor reset. This closes a
**conditional static timer-expiry→queued respawn→reset path**, replacing the
older unqualified missing-producer statement for this exact build only.

Important boundary: ordinary received StartRespawnTimer00950c80 is gated by
0209e204==0; a new component sets+18=0, and ctor009588e0 zeros+14/+18. At expiry
in mode0,00953990 skips producing ActorRespawn and marks the timer. A valid
component+18 spawn-point object and authoritative initialization are not recovered
for the nonzero-mode producer. Do not execute or emulate null pointer access.
There is no claim that receiving0433 in a client automatically produces0432.
Incoming009572b0 references still find0094c964 only; inline production is upstream.

The pre-expiry0.1<remaining<=0.3 mode-nonzero branch compares owner position with
spawn object then calls00450910; fresh body is an empty return. It does not prove
an early teleport. General005d3b60 and additional005cc310/005f1dd0/006f7a80 are
UI consumers. Decompiled rounding/casts in the latter are not promoted without
assembly;005cc310 assembly is retained for future interpretation. None triggers
respawn at a displayed zero.

## Recall boundary rechecked

00923320 builds cancellation,timeout,end and presentation behavior lists.
00946ee0 initializes context then dispatches each list member's virtual+4;
it is shared by several callback types, so reaching it does not identify timeout.
Fresh00532910 assembly installs TeleportSelection0121b3d8 and helper0121b3cc;
0052f3b0 installs CancelThisBuff0121b0d0. Exact table+4 reads select0045ecd0 for
both run slots (RET4) and0045cd00 for helper setter (returns this). Their declared
provider and callback names cannot prove teleport, cancellation or a four-second
live recall. Input request and queued client apply remain separate from server
acceptance. No new historical-prefix decoder or recall-success reducer.

## Falsification and exact experiment

Check the selected hash, selected direct calls/vtable words and inline respawn
vtable immediate with the bounded verifier. Registration callback/slot, header
byte, mode gates and full queue/reset control flow rely on the cited assembly
receipts and prior queue report; the verifier does not validate those predicates.
A build changing any of these reopens this conclusion. Valid timer+18 and mode
are required; zero display alone is a counterexample to completion.
Next matched-build trace records component generation/owner,+14,+18 validity,
engine delta/mode, enqueue header/vtable and position, reset invocation, accepted
state1 transition and player-control restoration. For recall record request,
accepted start,buff instance,cancel/timeout/end callback class,teleport action,
actual position/resources and user control; independently induce movement,
damage,ability use and natural timeout. Do not use generic0409 or re-spawn
snapshot coincidence as proof. No native client/server/screen execution performed.
