# Historical research map (before the static follow-up)

This map records the earlier investigation state. Input acquisition and cooldown/HUD findings below were subsequently advanced: see acquisition-receipt.json, REPORT.ko.md and CLOCK-HUD.ko.md in this directory. Proposed work here is not a claim that it remains unimplemented.

# Vainglory replay-to-state research map

Prepared 2026-10-14 from the downloaded repository. This is a map of existing evidence and proposed tracing, not a fresh REA verification of the client.

## Baselines and confidence

- Main inspected: `7d1e0e982d24bf48a11de6debbaeab7b7db090ba`
- Additional read-only evidence: remote branch `origin/codex/rea-item-activation`, commit `3361131`
- Reference x86 Windows client SHA-256: `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`
- Definition manifest SHA-256: `7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c`
- “Confirmed” below means the cited repository contains bounded native or runtime evidence. It does not establish all client builds, full-event semantics, or successful use for every request.
- “Candidate” means there is a named or observed path worth tracing. An unobserved event is not an absent feature.

## 1. Replay framing and dispatch

Confirmed within the reference-build scope: reader `004ca130` consumes timestamp, BE32 length and complete packet; `004eb4a0` passes the buffer to dispatcher `004cfec0`; recorder `009546f0` copies the complete packet. Recorded and serializer lengths are separate domains. Some suffixes remain opaque.

Source: `vg/docs/EVENT_SEMANTICS_2026-10-04.md`, its event atlas and linked native receipts. The atlas retains 161 candidates, 123 handled receiver branches and 93 observed opcode/length pairs; this is not 161 decoded meanings.

Next edges: preserve queue/constructor/apply identity for each investigated opcode; trace caller mode guards before equating a network path with replay application.

## 2. Actor, item and ability identity

Confirmed roster fields: `03ee` actor/definition/skin/team fields, with `03f2`/`03f3` spawn corroboration. Receiver branch `004d274e` calls `004d52a0`; downstream functions include `0096d310`, `0095e5e0`, `0095e9f0`.

Confirmed inventory distinction: actor `+0x34` points to its item component; each item has definition pointer `+0x14`, definition ID `+0x2c`, instance ID `+0x30`, quantity `+0x34`. Equal definitions can be separate instances. Item IDs are not actor references. Original assets and localization bind the shipped inventory subset.

Candidate/missing: a general ability identity join across actor abilities, item abilities, override/grant actions and cooldown references. Numeric equality alone is insufficient.

Sources: `NATIVE_ROSTER_2026-10-04.md`, `NATIVE_INVENTORY_2026-10-04.md`, original definition evidence.

## 3. Requests, activation and shared ability dispatch

Confirmed bounded activation evidence on the remote activation branch: `0448`/`0449`/`044a` serialize distinct request layouts; observed wrapper caller `00529ff0` selects paths through `0095bda0`, `0095bea0`, `0095bdd0` and serializers `00813dc0`, `00813fc0`, `00813ec0`.

`044c` receiver `004d3e39` selects mode constructors `0081b7f0` (target), `0081b790` (position), `0081b740` (untargeted). Apply `0094ee90` resolves actor/component/item/ability and reaches `onPlayAbility` on eligible paths. Guards and mode-specific active fields matter.

Candidate parallel ability paths: `0411`–`0413` activation request classes, `0415`–`0417` play ability, `041a`/`041b` overrides, `043a`/`043b` grant/downgrade, `043c` cancel and `0489` behavior sync.

Next shared edge: trace `onPlayAbility` registration and eligible downstream callees, then compare item and hero ability paths. Keep success, rejection, cancellation, no-target and mode conditions separate.

Source: branch `vg/docs/REA_ITEM_ACTIVATION_2026-10-14.md` and its receipt; main inventory report; binary-event candidate atlas.

## 4. Cooldown, charges, inventory stacks and protective effects

Candidates, not decoded cooldown state:
- `0427` ActionPauseCooldown; constructor `0081bde0`, formatter `008178c0`; not observed in the documented corpus
- `0428` ActionModifyCooldown; constructor `0081bb60`, formatter `008173c0`; 135,732 recorded instances in the documented corpus
- `0429` ActionModifyAbilityCharges; constructor `0081b8d0`, formatter `00816cc0`; 1,314 recorded instances
- `048a` ActionSyncCooldown_Client; constructor `0052ad40`; 971,766 recorded instances

Next concrete trace: start with the `0428` and `048a` receiver branches, constructors and apply targets. Establish referenced owner/ability identity, timer field addresses, units, clock source and operation (set/add/scale/pause) from actual reads/writes. Find common storage with `onPlayAbility` and `0429`. Inspect writer and reader paths before assigning payload names.

Confirmed inventory stacks are separate: `0444` apply `0094f6f0` writes the low 16 bits of quantity; zero does not itself remove an item. `044b` consume uses `00872340`, with quantity/definition-dependent removal. `043d` grants use `0094e070` → `0093d080` → `0093cdc0`.

Protection/buff candidates: `043e`/`043f` apply buff; `0441` duration; `0442` max stacks; `0443` stacks; `0445` cancel; `0446` timeout; `0447` decrement; `048b` buff variable. Trace original buff definitions, target resolution, setters and end paths. A buff action does not by itself establish shield amount, damage absorption or invulnerability. Compare resource/attribute changes and effect consumers rather than collapsing all protection into one counter.

Sources: `vg-binary-event-candidates-2026-09-09.md`, `vg-binary-event-candidates-2026-09-09-details.md`, inventory evidence.

## 5. HUD consumers

Confirmed limited consumers: inventory HUD refresh `005c1bb0` calls `005a0790` and excludes original resource names Healing Flask and Vision Totem from general inventory; active/passive display differs from native array order. Rejected-buy callback registration in `005ce440` connects to `005ce000`, which clears owner `+20bd` bit `80`.

Missing: cooldown overlay/text/charge and protective-effect HUD readers bound to the same state and clock. Trace readers of timer/charge fields identified above; separately establish rounding, cache refresh, hidden item rules, slot order and replay speed behavior.

Sources: `NATIVE_INVENTORY_2026-10-04.md`, `REA_ITEM_EVENTS_2026-10-14.md`. Existing gold/terminal display evidence does not validate cooldown rendering.

## Contradicted shortcuts

- An activation request or `044c` is not inventory-consumption proof; a distinct `044b` update is required by the existing reducer
- All requests are mutation-free is false: reorder `0438` has a client serialization-side swap
- Native array order is not established rendered slot order
- Universal six-byte trailer handling contradicts observed length differences
- Zero quantity is not equivalent to immediate pointer removal

## Inputs needed for new verification

1. The reference `Vainglory.exe`, or another explicitly identified build with a newly recorded SHA-256. No executable or DLL was present in the downloaded checkout.
2. Matching `definitions.resource` and relevant item/ability/buff assets (and localization for labels). Small derived catalogs already shipped do not replace all original resources for new paths.
3. At least one complete `.0.vgr` plus numbered sibling family with the relevant events; source hashes and record locators must be retained. No replay file was present in the checkout.
4. Later, controlled runtime traces/screenshots for successful, rejected, canceled, charge/stack and protected/unprotected cases if claiming execution or rendered results. Static analysis can proceed on Linux without running the Windows game.

No verified exact client-download URL was found in the checked repository. The official site's historical community-edition notice reports removal of new Steam downloads; the currently inspected official homepage and support FAQ do not provide a verified matching Windows build. A community distribution must be source-reviewed and hash-checked rather than assumed identical.

Official references checked: https://www.vainglorygame.com/news/vainglory-community-edition-update-edtheshred/ and https://superevil.zendesk.com/hc/en-us/articles/27836259401243-Frequently-Asked-Questions-Vainglory

## Fresh remote-branch audit: 2026-10-14 08:56 UTC

`git fetch origin --prune` completed successfully. No new published commits appeared beyond the previously known activation `3361131` and H5810 `45e42a4` heads. This says nothing about unpublished work on another computer; none was accessed. The shared checkout remains on main and unchanged.

### Exact branch provenance

- `origin/main`: `7d1e0e982d24bf48a11de6debbaeab7b7db090ba`. All main-document claims in sections 1–5 above are pinned here, including framing/dispatch, original roster behavior, inventory transitions, HUD filtering, cooldown/buff candidate lists, and rejection consumer. The 911-test cloud run covers this commit only.
- `origin/codex/rea-item-activation`: `33611314a29d2ad57a4c56a2f6da569b22ec9641`, one commit ahead of main, zero behind. All activation-branch layout, mode, serializer, apply-path and 35,264-row corpus claims refer to this commit and its checked-in receipts. Those corpus claims were not rerun in the cloud.
- `origin/fix/h5672-spawn-skin-identity-20261014`: `45e42a41acf16974dd42588c3a70b09c4cf59dd6`, three commits ahead of main, two behind. Its three unpublished-to-main commits are described below.
- `origin/codex/rea-item-events`: `df1da9a28282d0298b3eece999a2454ab9959ff3`, fully contained in main (zero unique commits; one commit behind).
- `origin/fix/definitive-analysis-eligibility-20261011`: `296b10174db299f896bb4bd5c41bc57187de497f`, fully contained in main (zero unique commits; three behind).
- `origin/feat/decoder-stat-accuracy-20261004`: `b7d5a3af675db6d6a96ae3c71823a3f6d13b5d24`, fully contained in main (zero unique commits; 43 behind).

### Existing unmerged implementation: do not recreate

Activation commit `3361131` already adds mode-aware extraction for `0448`, `0449`, `044a`, `044c` in `vg/analysis/native_event_fields.py`, includes them in `event_timeline.py` defaults, and adds `tests/test_item_activation_timeline.py`. This is implemented code, not merely proposed research. New work should start downstream of that established bounded extraction rather than add duplicate opcode decoders.

Actor/skin commit `dbb571871e255e5a818b21beb68e61657bb06828` already adds `NativeRosterPlayer.actor_identity_status`, based on matching actor definitions independently of skin hashes. `player_state.py` uses this identity status for gameplay fields, preserves `spawn_skin_hash`, and exposes separate skin uncertainty/conflict. The overall roster can remain partial while corroborated actor gameplay fields remain available. The branch adds six tests in `tests/test_skin_identity_split.py`; these were inspected but not rerun as part of the main-only cloud test result. Do not recreate this identity split when linking activation actors.

The two implementation branches have disjoint changed file lists. Their important semantic overlap is actor identity: future activation/cooldown joins must respect the actor-versus-skin split while retaining target and item-instance distinctions. Disjoint files do not prove integration correctness, and no merge was attempted.

### H5810 evidence already completed versus still pending

- `b68ab8f969dcab915a52aa99371485ec17667d29`: `PLAYER_STATE_H5810_10MIN_2026-10-14.md` records an independent native comparison at displayed 10:00: 70/70 field groups across ten players, with 14/14 for selected actors 1500/1501. It used decoder `dbb5718`, and the report distinguishes matching endpoint states from unverified intermediate states. This is existing scoped runtime evidence, not a new cloud result.
- `45e42a41acf16974dd42588c3a70b09c4cf59dd6`: `PLAYER_STATE_H5810_TERMINAL_2026-10-14.md` records 11/11 CLI/API JSON pair equalities and a frozen terminal protocol. Actual pre-terminal and result-screen comparison remains explicitly pending. Internal consistency is not native accuracy. Winner, final display gold/time and definitive eligibility remain unverified.
- H5810's postgame event precedes its queued end request by 6.0928955078125 projected seconds; gold changes after postgame. Five records follow the end request. Those observations already rule out treating either first postgame or queued request as a universal final-state cutoff.

### Documented replay source discovered on the H5810 branch

The H5810 ten-minute report identifies the previously permitted public archive `https://replays.richardtravel.com`. It identifies ranked 5v5 H5810 with 168 numbered sections, match UUID `00add1f2-a259-45ed-beda-2463bc3a3760`, recording UUID `8b68b2dd-924e-4c75-b662-c9da67df376d`, bundle SHA-256 `9019dd4f22ea813a90696af0499e5ed49a35b2121fc5026852af536d68f5c63c`, and concatenated source SHA-256 `ae8e37a0eb42f8d323311b20ceee2a1314fe97ae330be24cf30e3ffeca4870f0`. This is a source pointer from existing evidence; current archive availability and download integrity still need checking. The executable distribution source remains missing.

### Remaining nonduplicate research

Proceed with the shared cooldown/ability-state writers and HUD readers described in sections 3–5, using the existing activation layouts and actor identity split as dependencies. Do not equate H5810's ten-minute player-state validation with cooldown, protective-effect or final-result validation. No branch inspected supplies a completed general cooldown/protection reducer or validated cooldown HUD path.
