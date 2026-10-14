# H5810 terminal preparation and offline comparison, 2026-10-14

**Actual pre-terminal and result-screen comparison is pending.** The offline
increment at `45e42a4` ran while Windows was unavailable and verified recorded
state and CLI/API consistency only. A later native attempt was blocked before
replay injection by `LockApp.exe`; its complete cleanup is recorded below.

At baseline **b68ab8f969dcab915a52aa99371485ec17667d29**, all **11 CLI/API JSON
pairs were identical**: five all-player and five selected-player queries, plus
one conservative final export. The existing product code and final-field policy
were not changed. CLI/API equality is internal consistency, **not independent
native accuracy**. Native match/mismatch counts are unavailable.

The [sanitized offline receipt](evidence/2026-10-14-h5810-terminal-offline/summary.json)
contains source identity, output hashes, query boundaries, recorded values,
terminal events, missing native observations, and the remaining acceptance gates.
The [completed ten-minute comparison](PLAYER_STATE_H5810_10MIN_2026-10-14.md)
remains separately scoped; it does not establish terminal/result correctness.

## Source and fixed offline query points

This reuses the same independently selected H5810, ranked 5v5 with ten players
and 168 numbered sections. It adds **zero new independent recordings**. All
local source hashes were rechecked before and after the analysis. The source
scope is `sha256:e0594f1bb06721d1139c18c156001cc8379cc182d12cb9451ca786a8a728d11b`.
The original acquisition, ten-minute baselines, and prior observations remain
preserved. Archive reference results were not used as terminal ground truth.

The protocol was frozen before these output queries: 0.1 projected game seconds
before the first `0452`, 5/1/0.1 seconds before the first queued `03f1`, and
unbounded recorded EOF. Each query selects all ten players and, separately,
the previously selected actors 1500/1501.

| Point | Requested projected game seconds | Applied section/offset | All/selected CLI/API |
| --- | ---: | --- | --- |
| Before PostGame event | 1652.816259765625 | 167 / 70032 | Equal / equal |
| End request minus 5 seconds | 1654.0091552734375 | 167 / 82072 | Equal / equal |
| End request minus 1 second | 1658.0091552734375 | 167 / 130520 | Equal / equal |
| End request minus 0.1 seconds | 1658.9091552734376 | 167 / 140560 | Equal / equal |
| Recorded EOF, no time filter | None | 167 / 145152 | Equal / equal |

All ten state outputs retain `support_status=supported` for recorded fields,
`recording_client.status=unverified`, `skin.status=unverified_rendered_skin`, and
`definitive_analysis.eligible=false`. A supported parser result is not an
observed client result. Selected-player results are subsets, not extra samples.

## Terminal observations from the recording

The first `0452` occurs at section 167, offset 71088, packet time
**1671.8291015625**, with anchor projection **1652.916259765625**.
The single queued `03f1` occurs at offset 145024, packet time
**1677.9219970703125**, projection **1659.0091552734375**. Its recorded team value
is **2**, end reason **0**, and status `queued_request`.

The PostGame event precedes that request by **6.0928955078125 seconds** of
projected time. All ten actors' recorded balance and net worth change between
the pre-PostGame and end-minus-5 snapshots, and again in the subsequent two
intervals ending at end-minus-0.1. Thus the early PostGame event cannot be used
as a final-gold cutoff for this recording.

K/D/A, CS, and complete inventory are equal at those compared endpoints.
End-minus-0.1 and EOF have no differences in the compared fields, including
gold. These are endpoint comparisons; transient intermediate state was not
exhaustively validated.

Five additional records follow the queued request at the same packet timestamp:
`0430`, `041c`, `043e`, `041d`, `041d`. EOF includes them and ends at offset
145152. Equal timestamps do not authorize dropping records after the request.
Neither `0452`, a queued request, nor EOF proves successful native completion.

## Winner, gold, and time remain separately qualified

| Field | Available offline observation | Actual terminal/result validation |
| --- | --- | --- |
| Winner | Queued winning team value 2 | Unavailable; no observed client side or server winner |
| Gold | Recorded resource 6 balance and resource 7 net worth for ten actors | Unavailable; final cached formatter input and result text not captured |
| Time | EOF anchor projection 1659.0091552734375 seconds | Unavailable; terminal/final clock, formatter argument, and screen text not captured |

The conservative safe-json CLI and API outputs are identical. Final winner and
gold are **null / unknown / not accepted for indexing**. Its duration value
**1667 seconds** is the existing `crystal`-based **partial approximation**, not
a confirmed duration. It differs from the recorded anchor projection by about
7.991 seconds; neither is promoted to actual displayed duration, and no fitted
time correction is justified without the missing native trace.

The raw state export describes `scope=recorded_end`, not a certified final match.
For example, actor 1505 has recorded balance **105.25** and net worth
**15955.25**. The direct formatting candidate **16.0k** is explicitly estimated.
Its actual cached gold label remains null. All ten actors' `observed` and
`reconstructed` display gold values and the observed display time remain null.
No ten-minute display receipt is attached to an EOF output.

Definitive analysis remains **excluded** for `recording_source_unverified`,
`recording_version_unverified`, and `final_result_unverified`. Successful future
local playback can validate observed client fields within this recording, but
does not by itself identify the recording build or certify server-final values.

## Prepared Windows acceptance and remaining work

Private local evidence contains a frozen protocol and an unexecuted collector
derived from the existing hash-guarded observer. Its player sampling window is
1635 through 1705 native game seconds while the replay reader is open; the
clock/terminal/gold formatter entry observer continues through the result.
Python syntax was checked locally. PowerShell scheduling, attachment, and the
new collection window have **not** been exercised on Windows.

On resumption, check unlocked desktop and owned foreground, source/executable
hashes, and absence of an existing game/observer. Back up all temporary replay
groups plus the fresh practice slot with hashes and creation/write times.
Reinject the unchanged source and attach before playback. Use full playback,
verified 5x then 1x near 1635, and a pre-terminal pause around displayed 27:35.
Require at least 20 identical full-player samples spanning five seconds and
source-bound future-reader-buffer proof. Rerun CLI/API at the actual consumed
prefix; the offline planned cutoffs are not substitutes for that boundary.

Resume at 1x through terminal/final callbacks. Capture the actual result screen,
ten player/row/team associations, last resources, cache buckets, formatter inputs,
gold labels, and time formatter bits. Validate observed local winner separately
from queued team and server winner; compare cached gold separately from EOF
resources; keep screen time, native clock, packet time, and projection separate.
Retain failed or seek-assisted trials separately and restore source slots and
all original groups before publishing a native receipt. Missing observations
remain unavailable rather than successful comparisons.

At `45e42a4`, related unittest checks passed **79** for time queries, CLI/service outputs,
display values, final scope, definitive eligibility, winner signals, and end
requests. Tests were not rerun for the later blocked-attempt documentation.
The full suite was not rerun for these docs-only increments. Raw replay
bytes, player names, complete outputs, and private collection scripts remain
local; published evidence consists of this report and sanitized receipts.

## Native attempt blocked and restored, 2026-10-14

The [blocked-attempt receipt](evidence/2026-10-14-h5810-terminal-blocked/summary.json)
is bound to baseline `45e42a41acf16974dd42588c3a70b09c4cf59dd6`. Preflight found no
game, observer, worker, pending command, or existing VG scheduled task; original
and LAA executable hashes matched. WTS reported session flags 1. The owned LAA
game launched, but the guarded screenshot ended at **12:38:21.976648 UTC**
(**21:38:21 KST**) with foreground `LockApp.exe` and error
`Owned game not foreground on Default desktop; refused`. No screenshot was made.

No practice/playback click, replay substitution, or observer attachment followed
the refusal. The owned game stopped; all **648 prelaunch recording sections**
matched saved hashes and creation/write times, with zero files needing recreation.
The worker acknowledged exit, no owned game/observer/worker or command remained,
and the sole owned scheduled task was removed after action identity checks.
All 168 transferred H5810 source hashes/sizes and original/LAA executable hashes
were reverified unchanged. Independent local preparation remains preserved.

This is a setup failure, not a replay failure or new accuracy result. Winner,
final gold, display duration, recording client identity, and definitive exclusion
remain unchanged. Further actual game attempts and handoff to the other Windows
experiment are held until a new user confirmation that the lock screen is closed
and the desktop is visible, followed by a fresh owned foreground/capture check.
