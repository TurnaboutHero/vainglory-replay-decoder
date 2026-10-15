# XP/hero baseline and mutation delta

This is a separate delta. The approved `experience-hero-levels` package was not changed. Exact inspected PE SHA-256: `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`, preferred VA base0x00400000. All native work is static; the executable was never run.

## Newly closed native baseline path

03f3 decoded payload fields, before gameplay application:

| Offset decimal | Encoding | Meaning supported here |
|---:|---|---|
|8|BE u32|actor ID|
|294|BE float32|base attribute40, LEVEL|
|318|BE float32|resource8, XP progress|
|322|BE float32|base attribute39, XP_REQUIRED|
|326|BE u32|nonzero skips snapshot baseline restoration|
|705|BE u32|additional post-snapshot level-loop bound|

`0x004d5930` reads +0x126 into temporary+0xa0 (attribute40), +0x142 into temporary+0x9c (attribute39), and +0x13e into temporary+0x2f0 (resource8). Its mask includes39/40. This handler operates on the endian-decoded payload, not raw little-endian wire values. The fresh dispatcher03f3 branch copies746 bytes at0x004d1a94..0x004d1ab4 into EBP-0x3e4 and converts fields first. Exact float conversion call/store pairs are0x004d2180/0x004d218d (payload294),0x004d2210/0x004d221d (318),0x004d2228/0x004d2230 (322), all through byte-swapping float helper0x004cfda0. Gate326 uses ntohl call/store0x004d223c/0x004d2244; loop705 uses0x004d2290/0x004d2298. EDI is loaded from ntohl import0x0120a614 at0x004d1ab9. The converted block is passed to0x004d5930 at0x004d23e7..0x004d23ee. Exact disassembly and byte anchors are retained.

Temporary initializer `0x0081c640` zeroes all45 attributes in all four layers and all16 resources. `0x0081ac20` copies the temporary block through `0x0081f5d0` to ActionHeroSpawn+0x40. The latter copies all four layers plus resources. The apply function `0x0094e170` calls `0x0095c940` if action+0x358 is zero. That assignment function restores masked layers0/1/2 and all16 resources; it does NOT overwrite layer3. This distinction cannot be erased merely because the temporary block's layer3 is zero.

Actual actor-stat construction is also closed: registration at `0x00954fdd` binds constructor `0x00957710` to the type later stored in global0x020e9c90; constructor calls `0x0081c640` at object+0x20. Thus a freshly constructed stats object starts with four zero layers. No claim is made that a later callback cannot change layer3.

Payload+705 maps through handler local_884 and constructor parameter28 to action+0x464. After snapshot restoration, apply loops `0x00944de0(1)` for i=1 while i<that bound. An output reader must account for this order or reject nontrivial bounds. All1680 historical H5810 snapshots have gate0 and loop bound1; no extra loop runs in this fixture.

`0x0094e170` exits for an already-resolved actor before restoration. Repeated snapshot records are not automatically native resets. The recurrence audit below uses later records only as observations to compare, never to reset predictions.

03f2 remains a different actor-spawn layout. Constructor `0x0081a750` places its own loop bound at action+0x360; its apply `0x0094d480` has its own repeated-actor guard and loop. No03f3 offsets are applied to03f2. The bounded hero audit seeds only from supported03f3 records;03f2-only actor progression is not silently assigned an invented XP baseline.

## Threshold and level mutation semantics

041c receiver `0x0094f1d0` resolves the actor, reads attribute index, layer, float operand and mode. Nonzero mode calls SET wrapper `0x0095c620`; zero calls ADD wrapper `0x0093e850` → `0x0093e940`. ADD reads the selected layer via `0x00937480`, adds, rounds on float storage, then calls `0x0095c710`. The latter delegates layer0..3 storage to `0x0095c590`. Its special health/energy/resource clamps concern indices0/2/32/43/44, not39/40. Therefore writing XP_REQUIRED39 does not inherently consume XP or raise hero level in this direct store path.

Effective value uses four layers: `((layer3+1)*layer1+base)*(layer2+1)`, with native consumer-specific clamps separately applied. A base-layer threshold cannot universally substitute for this effective value.

Both SET and ADD wrappers subsequently invoke `0x0086f1e0` for actor buff callbacks and `0x00539400` for notifications. The callback dispatcher searches the actor's buff list, matches registered callbacks and calls a function pointer. The direct mutation path is closed; the complete set of callback implementations and runtime buff state is not. This is an exact remaining dependency for a general-purpose player-state model, rather than a vague missing-XP-field claim. No arbitrary threshold curve is needed when recorded threshold assignments are present, and none is fitted here.

## Forward recurrence test, no checkpoint resetting

The one historical H5810 recording contains168 unique, contiguous numbered sections0..167. Inputs are sorted by numeric section suffix, one recording prefix is required, and every section SHA-256 is recorded. The initial03f3 for each of10 hero actors seeds level1, XP0 and threshold68. These values come from bytes, not game-mode defaults.

After seeding, the model predicts forward using native-derived float32 resource8 operations, base-layer attribute39/40 operations and0434 level deltas. Later snapshots are compared before any mutation and are NEVER loaded back into predicted state. Rules were selected from native traces before the first check; no arithmetic rule was changed after inspecting the result. Subsequent changes added explicit input/coverage accounting, not fitted behavior.

-18130 tracked resource8 operations
-110 tracked hero level actions
-110 tracked threshold assignments
-1670 future snapshots ×3 fields =5010 exact comparisons
-Level1670/1670, XP1670/1670, threshold1670/1670; zero drift/mismatches
-0 modeled shape/gate/loop/layer/destruction issues

An independently written checker reproduced all5010 comparisons bitwise as float32, with10 initial seeds and no checkpoint resets. It separately records19888 relevant-opcode records belonging to untracked actors. Other opcode classes and dynamic callbacks remain unmodeled. The receipt is `independent-deepening-review/xp-recurrence-independent.json`; its exact hash is included in the final manifest.

This is a seed-versus-future-checkpoint split within one already-known historical fixture. It is NOT an independent holdout, build match, native execution, or screenshot validation. Checkpoint self-consistency is strong support for bounded reconstruction but does not prove equivalence for unseen modes, buff combinations or builds.

At cap12, XP progress continues accumulating beyond the last threshold in this fixture. This is consistent with the native level-helper cap exit and the HUD ratio clamp. It is not evidence that resource8 became a cumulative earned-XP field; lifetime total XP remains unestablished.

## Decision and remaining blocker

Absolute hero level and XP are reconstructable for this precisely bounded, base-layer, single-lifetime historical fixture and internally cross-checked without checkpoint resets. This closes the concrete baseline/replay-recursion lead. Safe additive work now includes raw03f3 baseline projections, explicit post-snapshot loop bound, raw threshold-layer operations, and a research-only finite float32 model.

General production acceptance remains blocked by two specific dependencies: build-matched independent observed state, and callback/lifecycle coverage beyond the restricted model (including layer3 state not restored by snapshots, actor reuse/destruction, nontrivial starting loops and03f2-only actors). Exhaustively emulating all registered buff callback bodies would expand into the separate buff-state emulator; it is not justified by this bounded baseline task. No current production output is promoted, and current raw XP is never relabeled cumulative XP.

## Deliverables and verification

`portable/baseline_model.py` and13 tests cover exact offsets/gate/loop preservation, four-layer composition, SET versus ADD, float32 versus double, overflow/nonfinite rejection, cap/zero-delta/one-threshold behavior. These are model tests, not runtime equivalence tests. `scripts/check_recurrence.py` and `scripts/scan_baselines.py` are historical audits requiring private inputs. Native receipts and raw replay exports remain external. Public-safe files are this original summary, candidate entries and portable model/tests only.
