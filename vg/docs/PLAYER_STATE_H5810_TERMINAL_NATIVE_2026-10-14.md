# H5810 observed terminal and result state, 2026-10-14

At decoder baseline **4edeb299589f9fbb9e726828aef1fd00201da121**, H5810 matched
**70/70 native field groups** for ten players both before termination and at
proved recorded EOF. Actors 1500/1501 matched **14/14** at each boundary.
The actual client displayed **27:35** before termination, then **27:38** and
**패배** on the result screen. Both screens matched **40/40** observed groups.
No product logic, gold/time correction, roster policy, or definitive policy changed.

The [sanitized source-bound receipt](evidence/2026-10-14-h5810-terminal-native/summary.json)
contains numeric observations and private artifact hashes and is accepted by the
existing `--display-evidence` option. It reproduces observed display values as
supplied runtime observations, not authenticated server-final fields. The
[earlier offline/blocked work](PLAYER_STATE_H5810_TERMINAL_2026-10-14.md) and
[ten-minute result](PLAYER_STATE_H5810_10MIN_2026-10-14.md) remain preserved.

## Scope, playback, and actual source boundaries

This is the same independently selected H5810, not another new holdout: ten
players, ranked 5v5, 168 complete sections, numbered-series scope
`sha256:e0594f1bb06721d1139c18c156001cc8379cc182d12cb9451ca786a8a728d11b`.
Original source bytes were rehashed locally and on winsrv before substitution
and after cleanup. Existing lock-screen attempts are setup failures, not replay
accuracy failures; this is the first successful terminal capture of H5810.

Preflight found no existing game/worker/observer/task. WTS unlock, owned
foreground on Default desktop, and a real game screenshot were checked.
The existing LAA client and five player-probe guards plus nine clock/display
entry hooks matched their recorded executable/collector hashes. A fresh practice
slot was backed up, replaced with H5810, and all substituted hashes verified.
Playback began from the loaded start at 1x, used verified 5x, and returned to 1x
near native 1635 seconds. No GUI seek or restart occurred in this capture.

The clock briefly fell after the speed transition when a recording anchor
resynchronized it. The controller still waited for the actual native 27:35
interval. It paused at **1655.3775634765625**, with multiplier and delta zero,
then opened the scoreboard. Before resuming, it froze sample sequence 369 and
**286 identical complete samples spanning 73.103 seconds**. The full completed
log has 588 identical pre-end samples spanning 150.557 seconds, covering the
pre-end screenshot. The native paused flag was false; stability establishes the
pause without an atomic snapshot claim.

| Observation | Actual boundary or clock |
| --- | --- |
| Pre-end screen interval | 1655 <= native game seconds < 1656, displayed 27:35 |
| Pre-end native clock | 1655.3775634765625 |
| Pre-end reader playback time | 1674.3297119140625 |
| Applied prefix | Section 167, offset 101688 |
| Strictly future pending buffer | Section 167, offset 101712 |
| Recorded EOF prefix | Section 167, offset 145152 |
| EOF reader proof | Exhausted section 168, file closed, retained applied buffer matches last source record |
| Native terminal/final/formatter clock | 1658.9735107421875, float bits 1154440999 |
| Recorded EOF anchor projection | 1659.0091552734375 |
| Actual result-screen time | 27:38 |

The pre-end future buffer uniquely identifies the source record; its predecessor
establishes the applied prefix. The separate EOF proof matches the original last
record bytes and exhausted reader. The pre-end CLI/API query uses the observed
reader cutoff, not one of the planned offline times. Unbounded EOF traverses
all records, including the five records after the queued request at the same
timestamp. Native snapshots are observational, not atomic or server snapshots.

| Native query | Match | Mismatch | Unknown | CLI/API |
| --- | ---: | ---: | ---: | --- |
| Actual pre-end prefix, all ten | 70 | 0 | 0 | Equal |
| Actual pre-end prefix, actors 1500/1501 | 14 | 0 | 0 | Equal |
| Proved recorded EOF, all ten | 70 | 0 | 0 | Equal |
| Proved recorded EOF, actors 1500/1501 | 14 | 0 | 0 | Equal |

Seven groups per actor are native name, definition ID, K/D/A as one group,
complete item definition/instance/quantity multiset, resource 6 float bits,
resource 7 float bits, and CS from resource 14. Zero unknowns here applies only
to those seven groups; rendered skin identity remains unverified. The selected
results are subsets. The new EOF outputs equal the preserved offline EOF outputs.

## Result screen, cached gold, and time

The pre-end screenshot spans **13:10:15.802883 to 13:10:16.651258 UTC**
(22:10 KST), and the result screenshot spans **13:13:56.502087 to
13:13:57.277933 UTC** (22:13 KST). Each matched 40 screen-to-observation groups:
K/D/A, CS, cached gold label, and visible item icon count for ten rows. Each had
55 visible item icons, excluding the native hidden entries 457 and 526.
Exact pixel item identity, order/stack quantity, full pixel name transcription,
skin and portrait asset identity were not certified.

All ten result gold labels agree with their last guarded formatter/label calls.
Every one of the **1139 gold formatter calls** was linked to its preceding native
row and a strictly increasing cache bucket. EOF resources match the native
snapshot, but **eight direct EOF formatting candidates differ from the observed
cached labels**. Actor 1505 has resource 7 **15955.25**; its last formatter input
is **15901.25**, producing observed **15.9k**, whereas direct EOF formatting gives
estimated **16.0k**. Actor 1508 has resource 7 **9881.5009765625**, retained input
**9800.5009765625**, and observed **9.8k**, versus direct candidate **9.9k**.
Observed result gold is a client display value, not certified server-final gold.

The 03f1 terminal entry, final entry, and last time formatter occur in sequence
77224, 77225, 77226 with identical clock bits. Their native time is about
**0.03564453125 seconds below** the EOF anchor projection. That small difference
crosses an integer second: the native formatter produces **27:38**, while flooring
the projection would give 27:39. The old conservative duration **1667 seconds**
remains a separate partial crystal estimate. None authorizes a fixed time offset.

All **49,625/49,625 consecutive tick transitions** match float32 clock recurrence.
The 12,341 ticks after the last anchor, including multiplier 0 during the pause
and multiplier 1 after resumption, reconstruct the terminal clock bit for bit.
Post-game reader playback time continues to advance even with a closed exhausted
reader, while game clock, complete player state, mode/section, and retained record
buffer stay constant. Those latter values match in **461 samples spanning 118.987
seconds**, covering the result screenshot; no new record boundary is inferred
from the advancing playback time.

## Winner observations and remaining uncertainty

Privately preserved row/name associations connect all ten actors to their screen
sides: decoded/native team 1 is blue, team 2 is orange. The queued request names
team **2**, and the native terminal call also receives **2**. This verifies team
mapping and recording/native-call agreement.

The screen's result text is **패배**. It does not independently label a winning
side, and the local-team getter was not captured. Therefore
`winner_screen_side=null`; the text, team mapping, and call agreement are retained
separately. No independent screen winner or authenticated server winner is asserted.

Recording source/version identity, server-final winner/gold/duration, rendered
skin, and broader client/computer compatibility remain unverified. Every CLI/API
output retains definitive exclusion for source/version/final-result reasons.
The result establishes only this instrumented local client run and named fields.

## Reproduction, diagnostics, and cleanup

Supplying the published receipt as `--display-evidence` with the matching local
H5810 series reproduces ten observed gold labels and 27:38. Full and selected
CLI/API pairs match; original player values, field statuses, boundaries, recording
client status, and eligibility are identical to the default EOF outputs.
Observation status remains `supplied_runtime_observation`, with
`supplied_receipt_not_independently_authenticated` provenance. The default export
still has no attached display observation; reconstruction needs the supplied
formatter evidence. No caller-supplied final certification is introduced.

The initial screen-stability helper incorrectly required post-EOF playback time
to stay constant. That failed check is preserved; the corrected audit separately
verifies the exhausted reader/buffer, game clock and full player state. A reduced
image transcription initially read actor 1508 as 9.9k and yielded 39/40 screen
matches. Inspection of the **unchanged original 3094x1870 PNG** showed 9.8k.
The original transcription and 39/40 artifact remain preserved beside the corrected
40/40 artifact. No image, gameplay value, or test was changed to match a calculation.
The complete observer ended without a trace/RPC error or missing final sample.

Cleanup verified **648 prelaunch sections plus 12 fresh practice-slot sections**
against backup bytes and creation/write times; seven prelaunch files removed by
practice startup were recreated. All 168 substituted sections were archived
privately. Source and original/LAA executable hashes remain unchanged. The owned
game, observer and worker exited, pending command was absent, and both owned
tasks were removed after exact action checks. Windows was released after this
verified cleanup; no further Windows input or collection followed the handoff.

Related repository unittest checks passed **79**. The full suite was not rerun
for this documentation/receipt increment. Native, display, scope, baseline and
cleanup assertions passed; four native and two display-attached CLI/API pairs
were checked. Raw replay bytes, screenshots, player names, traces, complete
outputs and collection scripts remain private. Only numeric/hash evidence and
documentation are published.
