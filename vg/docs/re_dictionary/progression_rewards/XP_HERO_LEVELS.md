# Offline XP and hero-level evidence

## Result

The inspected Windows client positively distinguishes hero level, within-level XP, and XP required. A cumulative earned-XP counter is **not established**. This report does not promote historical replay candidates to accepted player state.

- Binary SHA-256: `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`, preferred VA image base `0x00400000`
- Work: static-only Ghidra/PE inspection plus offline replay parsing; no client or server execution
- Replay: historical H5810, unmatched build, not a fresh holdout. Exact section hashes are in `replay-evidence.json`
- Production files and existing frozen evidence were not edited

## 1. Applied level action and raw wire fields

RTTI type descriptor `0x01e65d04` names ActionLevelUp, complete-object locator `0x018971b8`, vtable `0x0127c964`. Receiver `0x0094f120` resolves actor from action+0x10 using `0x00857970`; if absent it does nothing. If present, action+0x14 is passed to `0x00944de0`.

Opcode `0x0434` dispatcher branch `0x004d31ec` copies eight bytes, converts two network-order u32 values, and calls constructor `0x0081b840`. The constructor places actor and requested delta at +0x10/+0x14 and installs that vtable. Serializer `0x0094b150` emits the same two network-order u32 values through `0x00816ac0`. This is distinct from the ability upgrade request opcode0x0436 and applied skill investment0x043a.

The historical replay has 162 records of opcode0434, all payload length14 and all requested delta1. The extra six bytes are retained as an opaque trailer in the bounded diagnostic, not silently given meaning. A recorded delta is not an absolute level or proof that actor lookup and application succeeded.

## 2. Hero-level mutation, initialization and effects

`0x00944de0` reads effective attribute40 (LEVEL). Base stats+0xc0 is only one term: `((modifier3+1)*modifier1 + base)*(modifier2+1)`, using offsets +2dc/+174/+c0/+228, plus native bounds and integer conversion. It exits if effective level is already >=12. Otherwise unsigned requested delta is capped to 12 minus current effective level; only positive capped delta increments the base.

Zero delta is NOT a universal no-op: below cap it still enters stat recalculation, XP adjustment, and callbacks. The ordinary finite illustrative model deliberately preserves this distinction and is not an SSE/NaN emulator.

Growth stats use definition base plus growth*(new_level-1): health, energy, regen, weapon/crystal strength, defenses, attack speed and other named attributes. Health/energy adjustment considers current resource fractions and per-level growth. The exact core receipt preserves each assignment. Positive level delta grants attribute29 (ABILITY_POINTS); this is separate from spending points on skills. `0x0093fba0` initializes base level0 then invokes level delta1. Spawn receivers can subsequently loop delta1 from an explicit incoming starting-level field; neither a global level1 nor ARAL level4 baseline may be invented for all recordings.

Named `LevelUp` telemetry uses format literal `0x0127c5e0`: Team, Actor, Level, LifetimeGold. Resource7 at stats+30c is LifetimeGold, **not cumulative XP**. This independently prevents the tempting wrong inference from its presence in a level-up event.

## 3. XP current progress, threshold, and UI

The attribute label switch `0x007d1410` maps:
- 20 / 0x14 → XP_VALUE, a reward-value attribute, not XP accumulated
- 39 / 0x27 → XP_REQUIRED
- 40 / 0x28 → LEVEL
- 29 / 0x1d → ABILITY_POINTS

Resource8 at stats+0x310 is within-level XP progress. HUD `0x005ad770` reads it and divides by effective attribute39, then clamps the target ratio to 0..1. The displayed bar is cached at HUD+0x697c: it animates upward using elapsed time and resets to zero on a target decrease. A raw ratio is consequently not an exact screenshot/display-state reconstruction. HUD threshold clamp globals (0x02094e74/0x01a418ec) differ from the generic attribute39 bounds used by the level helper; equivalence is not assumed. No local zero-denominator guard is visible in this HUD path, so the illustrative ratio helper explicitly supports positive finite thresholds only.

During the level recalculation path, core `0x00944de0` reads the old effective XP_REQUIRED and stores `max(0, progress-old_threshold)` through resource8 setter `0x0095f270`; this occurs once per invocation, not requested_delta times. New level1 initializes progress0. Generic resource storage floors negative values; raw recorded ADD/SET operands are not themselves resulting state. Relevant attribute layers and callbacks also matter.

Historical H5810 shape scan: 18,130 resource8 updates; 110 attribute39 base-layer SETs, values84,100,116,132,148,164,180,196,212,228,244 each10 times; no explicit attribute40 operations in this scan. These are observed thresholds, not a proven general curve. In particular, do not fit a linear curve and advertise it for other modes/builds. The scan uses framed records rather than byte signatures.

## 4. Safe implementation boundary and closure path

Safe additive diagnostics now supported: opcode0434 actor/requested-delta plus opaque trailer, resource8 raw operation/value, and attribute39/40 raw layer/mode/value, with record provenance and an explicit unmatched-build status. `portable/diagnostics.py` implements only the level event projection and bounded illustrative arithmetic; it is research-only, not wired into production.

Still withheld: absolute/current hero level, current XP reconstructed across all actor lifetimes, total earned XP, exact threshold curve, and exact animated UI state. Missing evidence is concrete: the recording/build match and independent displayed-state observations are absent; all threshold-setting/configuration and attribute-layer callbacks are not closed; actor spawn/destruction/resnapshot behavior must be integrated before a state model is safe. Existing native gold/stat models cannot simply be copied because level actions have their own recalculation side effects.

Next feasible offline steps: trace the existing 03f2/03f3 deserializer fields through starting-level and stat snapshot restoration, close all attribute39/40 mutation paths including callbacks, preserve float32 storage and all modifier layers, then compare reconstructed intermediate states against a build-matched recording with independently observed level/XP. A complete controlled fixture should include XP gain with no level-up, threshold crossing, a multi-level delta, zero delta, cap12, XP SET/negative ADD, non-default starting level, and late snapshot. No new installation, credentials, or live client/server access is needed for the remaining static work; independently matched observed state is the validation blocker for export acceptance.

## Tests and reproduction

`cd portable && python -m unittest -v`: 12 tests passed. Tests establish only diagnostic bounds and the stated finite illustrative model, not native execution or unseen replay accuracy. `scripts/verify_evidence.py` pins binary bytes, named labels, RTTI links and receipt hashes. `scripts/scan_replay.py` reruns the historical shape scan. Ghidra `probe.sh` uses the pre-existing approved toolchain with a private project and no executable execution. Exploratory receipts with incorrect boundary hints are excluded from the curated receipt manifest.

Public packaging should include only this original summary, candidate catalog entries and original bounded test code. Raw decompilation, binary data, game assets and raw replay exports stay external/private.
