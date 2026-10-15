# Structure destruction: exact-build offline evidence

## Result

The supplied resources distinguish ordinary turrets, VainNode (the armory-labelled actor), and VainCrystal. ArmoryTurret5v5 is a turret, not VainNode. No supplied localization proof links the user's Korean spelling 무쇠마루 to a particular definition, so that alias remains unresolved. This report does not silently equate them.

A new native chain separates ActorDie, subsequent ActorDead state request, and EntityDestroy cleanup marking. VainNode and 5v5 crystal death abilities lead to MarkMyselfDead, not a demonstrated match-end producer. A real VainNode regeneration callback was recovered, but it does not establish a destroyed armory's rebuild schedule. Structure reward allocation, awarded killer/team credit and crystal-to-authoritative-match-end remain unproved. Production decoder behavior is unchanged; every candidate is unaccepted for semantic indexing.

## Build and source scope

Windows PE32 Vainglory.exe SHA256 d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc, preferred image base00400000. Manifest03A640B504C2B4D7C8CBF3A04E189223 SHA2567292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c,932 definitions. Existing local Ghidra12.1.3/JDK21 and CFF decoder were used, with a private project copy and exact byte/hash anchors. No client execution, server request, installation, credentials or external asset export.

Prior creature-kill-credit, shared-reward-distribution and match-result-deepening reports are reused and hash-bound. Old659f9eed lifecycle addresses were leads only; EntityDestroy and ActorDead bodies were freshly checked in d6717c. H5810 is previously seen, producing executable unmatched, and provides only tentative diagnostics.

## Canonical definitions and alias boundary

CFF Actor symbol type2419fb6c and manifest serialized-name linkage establish:
-291..296 VainCrystal_Base/Home/Away_3v3 and Base/Home/Away_5v5, native kind2
-297 VainNode, native kind3, with CHAR_INFO_VAIN_NODE and DESCRIPTIVE_TITLE_ARMORY; death/spawn abilities and Buff_VainNode_Regeneration are declared in this actor resource
-339 Turret5v5,340 OuterTurret5v5,341 ArmoryTurret5v5,342 Turret5v5_Disabled, native kind3;341 carries DESCRIPTIVE_TITLE_TURRET and the same Ability__Turret__Die_5v5 declaration as339/340
-356 VainCrystal_LightWall is kind8, illustrating why a name containing VainCrystal is not sufficient structure classification

00942480: kinds2/3 set flag1000; kind3 exact-name VainNode sets4000, other kind3 sets2000; kind2 sets8000. The exact-name literal is0128eefc.005b19e0 consumes4000 with hud_battlelog_armory (012278bc) and2000 with the turret icon path. These are build-specific classification and presentation evidence, not objective-counter eligibility.

942 DEF0 symbols were scanned. A separate full raw asset scan searched UTF8/UTF16LE spellings of 무쇠마루 and two localization keys across48223 files. No Korean spelling match was found. This does not exclude encoded/compressed localization. The evidence establishes an armory-labelled VainNode but not that Korean alias.

## Three distinct lifecycle paths

1. ActorDie apply0094c8f0 resolves victim, checks mode0209e204==0 and predicate00558e40, then calls0092c110 and presentation. Predicate rejects actor states3/4.0092c110 requests state3 via00966570 on actor+48 and broadcasts onActorDie. The state transition function rejects equal/disallowed edges; the subsequent callback broadcast is not by itself a receipt that the transition succeeded.
2. VainNode death factory008c7670 builds death effect, armory-destroyed sound, Die animation, a5.5 operand on a delay-like behavior, and00526e60. Crystal5v5 factory008c6e40 builds selection/buff-reference setup, cracking/explosion effects and eventually the same00526e60. RTTI of0121a820 identifies AbilityBehavior_MarkMyselfDead; slot18 is0085c3a0. When0209e204!=0 this method constructs ActionActorDead vtable0127c6a8 with one actor ID and queues via0092d780. Its apply0094c8b0, under the opposite mode gate, resolves actor and only requests state4 when current state ID is3. This is not the two-reference ActorDie action and does not choose a credited killer or winner. The5.5 operand must not be named a rebuild delay.
3. EntityDestroy constructor0081a6c0 and apply0094d470 dispatch0092b630 in their respective mode paths. It resolves the actor, broadcasts onBeforeActorDestroyed, and calls0112a1f0. That marks a pool bitmap; it does not directly free the actor or establish the precise deletion time. Despawn/removal observation is not a structure kill.

Repeated creation is not proof of respawn: existing same-build creation apply0094d480/0094e170 can skip an already-resolved ID. Dead/disabled resources and animations likewise do not prove a new lifetime. The earlier historical parser support is not expanded to an independently verified new replay build by this static work.

## Regeneration and invulnerability

Buff_VainNode_Regeneration registry factory0091a8e0 registers onBuffIntervalName→00933e90 and onPreCalculateDamageExchangeName→00933de0, and declares vainNodeTimeOfLastDamage. The pre-damage callback updates that variable from00548880 when the damage-exchange target field matches the node actor ID. This is pre-calculation timing, not confirmed applied damage.

00933e90 runs only when0209e204!=0 and byte0209e208+21 is zero. It requires current clock minus stored value strictly greater than5.0, computes the same max-health-like expression seen in health work, clamps against020e7348/01a76098, compares current resource0, then constructs0081e780 with self as both references and amount multiplied by float32(1/180), codeee. This identifies a concrete conditional regeneration producer. Callback cadence, initial variable value, runtime branch availability, complete health-exchange effects and rebuild-after-death policy are not established; no per-second heal rate or respawn timer is asserted.

Buff_Turret_Invulnerable factory009195f0 declares gameplay-flag selector0200 via BuffBehavior_ApplyGameplayFlags constructor0081d390/vtable0127d798 and a flyout buff. Its resolve/remove slots00961580/009625e0 were inspected. This evidence is a separate flag/buff mechanism, not an ActorDie or EntityDestroy event. It does not prove the authoritative damage veto or every protection condition. Shield-break animations, flyouts, vulnerability transitions and destruction counts must not be merged.

## Credit, rewards and terminal boundary

The turret announcement branch00541430 uses victim classification/team/view predicates and TurretDestroyed. It is display logic, not a server award. Creature-kill-credit already proves retained hero attribution+1c0 is written before damage application and may replace raw source for hero-victim display; that does not authorize copying this attribution rule to structure objective awards. Raw death source, victim team, player last hit and awarded team remain separate.

Shared-reward-distribution establishes individual resource6/8 updates, but no structure-specific recipient/split/participation producer. This pass finds no gold or XP award formula in the inspected structure death factories. Turret count and first-armory-kill analytics names are not causation proof.

A direct-call lead scan finds00549620 called at004c0f1a;004c0e10 called at0094d458 (end action) and005b74c4 (separate fixed-argument wrapper). No inspected structure death factory directly calls these paths. ArmoryDestroyed/ArmoryRespawned string initializers0044e1e0/0044e210 store hashed IDs at020a0ca4/0209e308; bounded raw absolute references only locate those initialization writes. Unreferenced named IDs do not prove an implemented rebuild event. Indirect dispatch and absent server implementation remain possible, so this is a bounded negative, not proof no chain exists.

Match-result-deepening remains authoritative for the downstream boundary:00549620 writes team/reason before guarded transitions; primary state2 entry may run synchronously; repeated requests can overwrite fields without another callback. Reason0 is not proven to mean crystal destruction. Neither crystal death nor a nearby03f1 request yields a certified winner or credits.

## Historical diagnostic and verification

The strict existing parser scanned168 H5810 sections and2422 ActorDie records. Tentative current-manifest joins select14 structure deaths:6 OuterTurret5v5,5 Turret5v5,1 ArmoryTurret5v5,1 VainNode,1 VainCrystal_Home_5v5. There were no conflicting definition IDs or prior destruction observations for those scans. These are action observations, not independently validated structure counts, awarded objectives or complete lifetimes. Raw actor IDs, timings and replay examples remain external.

native-spans.json binds fresh full-entry native ranges. external-receipts.json binds reused evidence. verify_evidence.py checks exact binary/spans, vtables/RTTI, fresh resource decoding and finite boundary models; tests are static/parser/synthetic, not gameplay validation. Portable package excludes raw exports, assets, recordings and Ghidra projects. All accepted_for_index and production_ready flags remain false.

## Actual blockers

Korean alias requires a same-build localization link or explicit user clarification. Complete destruction/rebuild rules, invulnerability gates, awarded player/team objective counters, reward selection and crystal-to-match-end causality require authoritative producer implementation or independently labelled matched-build execution evidence. The supplied client contains useful declarations, state consumers and one conditional regeneration producer, but those do not close the missing chains. No nearest-event correlation or blanket name taxonomy fills the gaps.
