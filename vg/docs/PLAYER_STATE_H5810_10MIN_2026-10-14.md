# Independent H5810 player state at displayed 10:00, 2026-10-14

The decoder at **dbb571871e255e5a818b21beb68e61657bb06828** matched all
**70/70 native field groups** for ten players in H5810 at displayed **10:00**.
The two preselected actors, 1500 and 1501, matched **14/14** groups. There were
zero mismatches and zero unknowns **within those seven compared groups**.
All four game-time/record-time, all-player/selected-player CLI/API JSON pairs
were equal. No product logic, catalog, support policy, gold correction, or time
correction was changed for this recording.

The [sanitized evidence receipt](evidence/2026-10-14-h5810-10min/summary.json)
contains source identity, private artifact hashes, clocks, boundaries, comparison
counts, screen observations, retained unknowns, and restoration results. Raw
replay bytes, screenshots, player names, traces, and task definitions remain
in private local evidence.

## Independent selection and preserved baseline

H5810 was selected from the permitted public archive at
<https://replays.richardtravel.com> by metadata before decoding: ranked 5v5,
ten players, and sufficient duration to reach ten minutes. The first inspected
candidate, H5812, was not 5v5 and was rejected by this criterion. H5810 contains
168 complete numbered sections, reconstructed from the archive's segment map.

| Source identifier | Value |
| --- | --- |
| Match UUID | 00add1f2-a259-45ed-beda-2463bc3a3760 |
| Recording UUID | 8b68b2dd-924e-4c75-b662-c9da67df376d |
| Bundle SHA-256 | 9019dd4f22ea813a90696af0499e5ed49a35b2121fc5026852af536d68f5c63c |
| Concatenated source SHA-256 | ae8e37a0eb42f8d323311b20ceee2a1314fe97ae330be24cf30e3ffeca4870f0 |

The frozen inventory inspected 13,215 local files in `Documents/Codex` and
18,921 files in winsrv `VG_EVAL`, `Documents/GitHub`, and `DevCache/Temp`.
No recording UUID, bundle, or section-content overlap was found. Independence
is limited to those inspected inventories. Selection used the already completed
H5672 skin-identity change; this is a new sample of that decoder, not a new
validation of the original client crash fix or an untouched pre-fix decoder.

The all-player and selected-player 600-second baselines were saved before native
playback. Both repeated game600 queries equal those original baselines. The
acquisition's earlier lock-screen limitation remains in its original receipt;
the new native experiment adds evidence without rewriting that result.
All 168 local and transferred source hashes and sizes were checked before
injection; source hashes were checked again after cleanup.

## Actual capture and clock correspondence

The experiment ran on winsrv with the existing LAA client, SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
The owned game, unlocked interactive desktop, foreground, passive probe guards,
and RPC readiness were checked before starting H5810. A fresh practice recording
was backed up and replaced with the verified H5810 series.

The first speed-control automation stopped because hidden controls prevented
verification of 5x speed. Its failure receipt is preserved. Controls were then
explicitly revealed and the **same game process and replay session** continued;
there was no restart, sample replacement, or GUI seek. Playback used 1x, then
verified 5x, then verified 1x before the target. Temporary control-reveal pauses
were checked and resumed before the final pause.

The scoreboard screenshot spans **2026-10-13 18:07:39.993041 to
18:07:40.877211 UTC** (2026-10-14 in Korea). The complete ten-player state and
clock remained identical in **137 samples spanning 34.89 seconds**, covering
the screenshot. Multiplier and delta were zero. The native paused flag was
false, so repeated stability, rather than that flag or an atomic snapshot
claim, establishes the stopped state. The time formatter received the same
float32 clock bits as the native player samples.

| Clock or boundary | Value |
| --- | --- |
| Visible time interval | 600 <= game seconds < 601 |
| Native clock / formatter input | 600.3576049804688 |
| Reader playback time for the separate record query | 619.273193359375 |
| Observed applied prefix | Section 61, offset 133306 |
| Applied record timestamp / projected game time | 619.213134765625 / 600.3192138671875 |
| Strictly future pending record | Section 61, offset 133330; timestamp 619.2776489257812 |
| Pending projected game time | 600.3837280273438 |
| Requested game-time cutoff | 600.000 |
| Game600 applied prefix | Section 61, offset 127554 |
| Game600 applied record timestamp / projection | 618.8933715820312 / 599.9994506835938 |
| Game600 next projected game time | 600.0325927734375 |

The unchanged future reader buffer uniquely matched the source bytes; its
immediate predecessor establishes the consumed prefix. The native clock differs
from that prefix's anchor projection by **0.03839111328125 seconds**. The unrelated
probe global named `record_clock` stayed at the earlier practice value and is
explicitly unverified; it was not used for alignment. No fitted offset or
interpolation makes record time, projected game time, accumulated native clock,
or integer screen text identical.

The two compared prefixes differ by **198 records**. Their compared endpoint
states are equal. The interval receipt retains every record's location and
opcode counts, but this increment does **not** certify every intermediate
state or claim that no compared field changed transiently between endpoints.

## Native and CLI/API comparison

Seven groups per actor are counted: native name, hero definition ID, K/D/A as
one group, the complete item definition/instance/quantity multiset, resource 6
float32 bits, resource 7 float32 bits, and CS from resource 14. Native inventory
includes hidden entries 457 and 526; UI icon counts below exclude them.

| Query | Match | Mismatch | Unknown | CLI/API |
| --- | ---: | ---: | ---: | --- |
| Observed record cutoff, all ten | 70 | 0 | 0 | Equal |
| Observed record cutoff, actors 1500/1501 | 14 | 0 | 0 | Equal |
| Requested game 600 seconds, all ten | 70 | 0 | 0 | Equal |
| Requested game 600 seconds, actors 1500/1501 | 14 | 0 | 0 | Equal |

Selected-player comparisons are subsets, not additional independent players.
Top support status is `supported` for these recorded state fields. All ten
players retain `skin.status=unverified_rendered_skin`; agreeing recorded skin
hashes do not prove the rendered asset. H5810 has no first-spawn/roster skin-hash
conflict. Its actor 1505 is a different recording's actor and does not establish
anything further about H5672 actor 1505.

## Screen observations and cached gold

Manual screen transcription matched **40/40 groups** across ten rows: K/D/A,
CS, observed cached gold label, and visible item icon count. There were
**42 visible item icons**. Row associations use the privately preserved native
roster and screen names; two stylized name strings were only approximately
transcribed, so full pixel name transcription is not certified or counted.
Exact icon identity, item order/stack quantity, skin, and portrait assets were
not independently certified from pixels.

All ten gold labels match the captured formatter/label calls, whose input bits
also equal the row's cached display value. Those inputs differ from current
resource 7 for all ten actors. For example, actor 1507 has resource 7 **4392.5**,
while its **4.3k** label comes from the cached formatter input **4302.5**.
Formatting the current resource directly would not reproduce that observed
label. A candidate display calculation must remain an estimate; this is not
server-final gold evidence or authorization to add a fixed gold correction.

The complete trace ended normally with no observer error and matched
**33,386/33,386 consecutive clock tick transitions** bit for bit. This does not
certify uninstrumented playback or every rendered frame.

## Restoration, checks, and remaining unknowns

The owned observer detached and the game stopped. The final audit verified
absence of the owned game, worker, observer, and pending command. Both owned
scheduled tasks were removed after matching their exact action paths and
arguments. The **641 prelaunch sections** and **7 fresh practice-slot sections**
match saved hashes and creation/write times. Thirteen prelaunch files removed
by game startup were recreated from their verified backup. All 168 substituted
sections were archived privately. All H5810 source hashes and original/LAA
executable hashes remain unchanged.

Related repository unittest checks passed **86**: native roster, skin identity,
time queries, service, CLI, and display values. An initial pytest command found
no installed pytest; no package was installed, and the repository unittest
runner was used successfully. The full suite was not rerun for this docs-only
increment. Offline receipt assertions checked all four pairs, preserved
baselines, source/log hashes, native counts, screen counts, capture/stability
overlap, observer completion, and restoration receipts.

The recording client remains `unverified`. Definitive eligibility remains
**false / excluded**, with `recording_source_unverified`,
`recording_version_unverified`, and `final_result_unverified`. Public archive
acquisition and successful local playback do not identify the original recording
client build or establish final winner, final gold, or final duration. This adds
one recording at one midpoint on the same observed LAA client/computer; broader
compatibility and original-versus-LAA stability remain separate experiments.
