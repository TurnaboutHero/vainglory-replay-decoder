# Reviewed XP baseline and structure research, 2026-10-15

This isolated extension starts from `2a9925d`. Original summaries, structured
facts and test-only models are separate from production decoding. Native
addresses use PE32/x86 preferred VAs, image base `0x00400000`, executable SHA256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
Raw native exports, assets and recordings remain external hash-bound references.

## Hero snapshot baselines and threshold layers

The newly verified `03f3` path decodes base LEVEL, resource-8 XP progress and base
XP_REQUIRED at payload offsets 294, 318 and 322. Gate 326 and the subsequent
level-loop bound 705 are distinct fields. The model preserves raw base values,
withholds effective level/state acceptance and does not assume that every
snapshot applies. Already-resolved actors return before restoration.

Snapshot restoration writes masked layers 0/1/2 and resources, leaving layer 3
unchanged. Fresh stats construction initializes all four layers; later callbacks
can change them. Effective values therefore cannot always be read from base
fields alone. Post-snapshot level-loop operations follow restoration and cannot
be ignored outside the observed trivial-bound fixture. `03f2` remains a separate
layout and is not interpreted using `03f3` offsets.

Attribute `041c` distinguishes selected-layer ADD from SET. Direct threshold or
level writes do not automatically consume XP or invoke level gain in the storage
path; dynamic callbacks after storage remain a separate unresolved dependency.

## Forward recurrence evidence and its limits

Ten first snapshots seed a bounded float32 model. Later snapshots are comparisons,
never resets. An independently written checker reproduced all 5,010 field
comparisons across 1,670 future snapshots, with no drift in the selected model.
Both implementations use the same development-seen H5810 recording with an
unmatched producer build. This is not 5,010 independent games, a fresh holdout,
native execution, screenshot validation or proof of general runtime equivalence.

Thirteen portable tests cover offsets, gate/loop preservation, layer arithmetic,
float32 rounding, nonfinite/overflow rejection and level-helper boundaries.
A full callback/lifecycle model, actor reuse/destruction, nontrivial start loops,
03f2-only actors and independently observed build-matched state remain outside
this result. Current XP is not relabeled cumulative earned XP, and no production
state output is promoted. The detailed original report remains in
`../progression_rewards/XP_BASELINE_DELTA.md`.

## Structure destruction

[Original reviewed report](STRUCTURE_DESTRUCTION.md) and [unchanged candidate findings](structure-additions.json) distinguish VainNode (manifest297, armory title) from ArmoryTurret5v5 (manifest341, turret title). The Korean alias 무쇠마루 remains unresolved. Resource classification is exact-build static evidence, not a name-substring classifier.

ActorDie requests state3 and emits a callback; the state machine may reject an edge. VainNode and 5v5 crystal death sequences reach MarkMyselfDead, whose producer-mode action requests ActorDead; opposite-mode application requests state4 only from state3. EntityDestroy marks a cleanup bitmap after its callback, without proving completed deallocation. These steps do not supply objective credit, payouts, a rebuild scheduler or a crystal-to-match-end causal edge.

The node regeneration callback has mode/global gates and a strictly greater-than-five elapsed comparison, then a health-limit-dependent self-change amount with float32(1/180). Its pre-damage timestamp is not proof of successful damage; cadence, initial timestamp and runtime availability are unresolved. Eight finite-input synthetic tests cover only these boundary conditions and keep raw source distinct from awarded killer/team and winner.

The unmatched, development-seen H5810 recording gives 14 tentative structure joins among 2422 ActorDie observations in 168 sections. This is a diagnostic using current resource definitions, not independently validated structure counts, lifetime reconstruction or award evidence. Producer accepted_for_index:false and production_ready:false flags remain unchanged. Native exports, assets, raw actor IDs and replay examples remain external.
