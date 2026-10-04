# Original replay opcode controls — 2026-10-04

Eight of nine player-state control gates are verified for the pinned Windows replay build. The remaining03ee gate requires literal rendered hero-name text at an independently matched native boundary. Original replay observations, synthetic consumer controls and natural gameplay have distinct provenance. This does not change the original56-recording census, semantic-status counts, or certify complete decoder accuracy.

| Opcode | Observed controls | Scope |
|---|---|---|
|03f2|60 linked spawn applies:122-byte/existing14,126-byte/absent46|Exact framed source, native actor identity, queue-copy/apply linkage and first actor-resolution guard. Not all four length/presence combinations; no player membership inferred from spawn.|
|03f3|10 fresh750-byte actors;50 existing746-byte baselines|Fresh definition/skin/roster, selected K/D layers0..2, assists/resource14/gold/net-worth raw bits,56 non-null inventory tuples match native action. Existing sampled player state unchanged.|
|046f|13 records: C08 sections49,50,0,1,2; C03 sections0..7|69-byte payload+64 float bits equal native argument and manager+194 after apply, including backwards seek.|

[controls.json](evidence/2026-10-04-opcode-controls/controls.json) contains capture SHA256 and1-based line references, original file hashes and exact record offsets/bytes, native action bytes, resolver/queue/apply observations and before/after field snapshots. Full raw captures/corpus remain external and are identified by workspace-relative path and hash. The package is compact JSON; format locally for review if needed.

Recompute comparisons without trusting stored match booleans:

```sh
python3 vg/docs/evidence/2026-10-04-opcode-controls/audit.py
```

To additionally verify original full capture/source hashes and framed source bytes, pass `--workspace /path/to/outer/workspace`. The observed result is60 spawn,60 baseline,13 clock comparisons passing. The optional external audit uses the original local artifacts; it is not a new runtime observation. Assertions are required: do not run Python with optimization enabled.

Native snapshots remain non-atomic. Loader0095c940 copies only masked attribute layers0..2 and16 resource cells; no layer3 source-load equality is claimed. Baseline comparisons start at the native deserialized action with exact source linkage, not an independent complete decoder wire interpretation. Raw resource14 is not declared lane-only CS. Unknown suffixes, other modes/builds, header text and other initialization effects remain unknown; the variant semantic/application classifications are unchanged. The runtime copy has SHA256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`; original executable identity is retained separately in the evidence.

## 041c synthetic controls and rendered result

[counter-ui.json](evidence/2026-10-04-opcode-controls/counter-ui.json) contains eight22-byte synthetic controls for attribute indices41/42,layer0 ADD/SET. Their exact source bytes, constructor arguments, copied action, successful actor resolution and layer-store before/after bits are linked in the capture. The complete counter experiment has56 synthetic records: these eight attribute controls plus48 resource controls described below.

The independently inspected [scoreboard screenshot](evidence/2026-10-04-opcode-controls/counter-ui-board.png) shows ten players' K/D/A and icon counts matching40 native values. Its time interval10:31:42.143987..42.958522 is bracketed by unchanged samples2 and6 of39 stable samples from PID58604. Unique pending record6:135331 establishes applied predecessor6:135307. Target1509 renders3/3/0 after the final synthetic K/D SETs; no subsequent K/D041c record changes those indices through this boundary. Five intervening existing-actor baselines use the separately verified no-write guard. This proves the rendered resulting state at that later boundary, not rendered output immediately after each individual synthetic record.

Reproduce with `python3 vg/docs/evidence/2026-10-04-opcode-controls/audit_counter_ui.py`, optionally adding `--workspace /path/to/outer/workspace` to recheck all external source/capture hashes and the intervening source scan. The screenshot comparison is explicitly manual transcription of inspected pixels, checked against native values; the script does not perform OCR. Native reads remain non-atomic. No six-field visual match, natural kill emission, negative attribute clamp or literal hero-name text is claimed.

## 041d resources and natural unit kills

[Resource evidence and reproduction commands](evidence/2026-10-04-opcode-controls/resources/validation.md) cover50 original C08 receiver observations,48 synthetic ADD/SET cases on indices6/7/11/14 and13 natural resource14 increments. The actual12-byte native buffer equals the first12 bytes of each14-byte payload before endian conversion. This original-input capture covers indices2/3; synthetic inputs separately establish the arithmetic axis. Repeated identical original records retain all6-19 source-offset candidates; no unique raw-copy source offset is claimed.

The first lane kill and first jungle kill each have full screenshots bracketed by native resource14 values0 and1. Ten lane increments and three jungle increments correlate with unique original ADD1 records within sampled recording-clock intervals. The visible label is a minion-shaped icon and number; no literal CS tooltip was seen. Both kinds of kills increment this counter. These live samples are not atomic dispatch observations and do not establish victim actorIDs or a universal unit taxonomy.

The resource auditor recomputes the comparisons and rejects20 data/provenance mutations. Whole-event suffixes, flag effects, other resources and other builds remain outside this result.

## 043d,0444,044b inventory controls

[Inventory evidence and reproduction commands](INVENTORY_CONTROLS_2026-10-04.md) cover25 synthetic consumer controls:22 grant/consume cases and three quantity assignments. They verify duplicate instances, sentinel stack selection, capacity rejection, native array vacancies, low16-bit SET and consume transitions. A stored quantity0 consume removes the item; it does not reject the action. The original rejection hypothesis is retained alongside this observed correction. Naturally emitted0444 records and rendered inventory slot order remain unproved.

## Remaining03ee rendered-name condition

[The native roster index](evidence/2026-10-04-opcode-controls/roster-native.json) records50 exact original-source/native comparisons:40 payloads of216 bytes and10 of222 bytes. Both actors named Guest retain independently matched IDs, definitions and raw skins in both lengths. Skin-wrapper identity passthrough is not a skin-index lookup claim.

C08 was paused at two native reader boundaries with98 and285 unchanged reader/roster samples. The spectator surface showed both Guest names, portraits, abilities and statistics. Hovering portraits/abilities and clicking the ability row did not produce literal Petal/Lance text in the captured attempts; a click selected the camera or replay timeline. Portraits and asset localization do not satisfy the original rendered-label requirement. This is a concrete experimental gap, not a claim that no such UI exists. The strict command still exits1 for03ee and its original requirement remains unchanged.

The fresh [same-nickname identity index](evidence/2026-10-04-opcode-controls/roster-identity.json) and [original result screenshot](evidence/2026-10-04-opcode-controls/roster-identity-board.png) establish the two Guest rows independently of row order. Manually transcribed K/D/A8/0/9 uniquely joins actor1501, definition246, raw skin2899818972 and the Petal portrait; K/D/A2/4/16 uniquely joins actor1502, definition275, raw skin3301891249 and the Lance portrait. All ten native K/D/A tuples are distinct at this boundary. Guest is the displayed nickname, not a hero name. The original paired definition manifest and hero resources resolve246 to Petal and275 to Lance.

The screenshot interval14:35:46.731900–14:35:47.441870 UTC is bracketed by native capture lines244 and248. Across342 timed samples the full player/roster state and game-clock bits remain identical, and the reader retains the exact final frame of source section169 at EOF, with next section170 absent and the file closed. This is exhausted playback, not a pending future record or a paused-reader claim. Playback time continues advancing and changes during32 individual reads; the two screenshot bracket reads are internally unchanged. Fresh initial playback also reproduces50 unique original-frame/dispatch/consumer comparisons,40 with216-byte and10 with222-byte payloads, including both Guest actors in both lengths. Skin bits are not interpreted as a skin index.

Reproduce the embedded comparisons with `python3 vg/docs/evidence/2026-10-04-opcode-controls/audit_roster_identity.py`; add `--workspace /path/to/outer/workspace` with Python3.10 or newer to recheck the external captures, all170 original sections, screenshot receipt,342-sample stability and paired original assets. `python3 vg/docs/evidence/2026-10-04-opcode-controls/test_roster_identity.py` checks the unchanged evidence, row-order independence and11 rejected identity/boundary mutations. Portrait identification and screenshot transcription remain manual. The default audit validates two embedded bracket states; it does not certify the external342 samples without `--workspace`.

Additional Tab holds, portrait/ability/item clicks and holds, and replay options still produced no literal hero-name text in the captured original UI. The native help-button event path was located statically, but no callable spectator route or selected-actor binding was established. All59 original replay-slot sections touched across the two fresh sessions were restored with matching SHA256 hashes; the owned games, workers, probes and scheduled tasks were stopped. This follow-up adds bounded identity proof while retaining the strict03ee rendered-text condition as pending.

## Runtime cleanup

All three owned runtime workers were closed and their scheduled tasks removed. The final runtime restored49 original sections across two substituted slots; every restoration hash matched. Its1698 archived files match the remote files byte-for-byte. Failed lane/setup/label attempts remain archived and are excluded from passing claims. The first C08 observation ended cleanly; the later labels-only probe ended when the owned game was stopped and is not used as a completed observation.
