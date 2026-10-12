# Independent H5672 player state at displayed 10:00, 2026-10-12

The existing decoder at **f6e11cdf1390bb0e68149af512780c5eb7852974**, before any
product logic change, matched **64 supported native field groups**, with
**0 mismatches and 6 unknown groups**, in the newly acquired H5672 recording.
Actors 1500 and 1501 matched **14/14 groups**. The actual client scoreboard
displayed **10:00**, while its native clock remained **600.34130859375 seconds**.
All four all-player/selected-player, game-time/record-time CLI/API JSON pairs
were identical. Their full-roster support status remained **partial**.

This is an initial independent sample result, not a repaired sample relabeled
as an independent pass. **No product code, supported-field policy, hero catalog,
gold correction, or time correction was changed.** The actor 1505 identity
conflict and the original baseline outputs remain preserved.

The [sanitized evidence receipt](evidence/2026-10-12-h5672-10min/summary.json)
records the source scope, hashes, boundaries, comparison counts, unknown reasons,
screen observations, interval audit, and cleanup. Original replay bytes,
screenshots, player names, full traces, process identifiers, and task definitions
remain in private local evidence; they are not published in this increment.

## Sample selection and independence

The permitted public archive identified H5672 as `GameMode_5v5_Ranked`, with
ten players and 121 complete numbered recording sections. The sample excludes
H5543, H5519, H5621 and previously acquired development/validation recordings.

| Identifier | Value |
| --- | --- |
| Match UUID | 55eaeaea-0c5f-4f7a-852d-b900e1a3dd27 |
| Recording UUID | 1f7c9adb-e650-4fce-b3f3-86e236b08114 |
| Downloaded bundle SHA-256 | 59dfd380d0fb701442914182bbe5f71c85a4d8105471406f2b127fc9d8248c29 |
| Concatenated section SHA-256 | 0d69a7875ddfa1720593134f68bc9f4d833e383e31526d557194eaef1295ee9e |

The acquisition inventory compared UUIDs, bundle hashes, and individual section
content against local `Documents/Codex` and winsrv `VG_EVAL`, `Documents/GitHub`,
and `DevCache/Temp`. It found no prior UUID, bundle, or section-content overlap.
This establishes independence within those inspected inventories; it is not a
claim about every possible external copy. Source hashes were checked on both
Mac and winsrv and rechecked after the experiment.

The original 600-second all/selected baseline was saved before actual observation
and before any possible product change. The later game600 results equal those
preserved baselines, including their partial support status.

## Capture and time correspondence

The successful capture used playback from the loaded start, 1x then 5x then 1x,
revealed controls before the target, paused, and opened the scoreboard. The
successful control sequence contains no GUI seek. This does not certify every
intermediate rendered frame or rule out effects of instrumentation on playback.

The scoreboard capture ran from **2026-10-12 14:27:02.885848 to 14:27:03.652237
UTC**. The complete ten-player state and clock were identical in **177 samples
spanning 45.148 seconds**, covering that screenshot. Runtime multiplier and
delta were zero, and the time formatter received the same clock float bits.
The manager's native paused flag was false; stability, rather than that flag
or an atomic snapshot claim, establishes the stopped state.

The unchanged future reader buffer uniquely matched section 59, offset 139117.
The immediately preceding record establishes the applied prefix, offset 139093.

| Clock or boundary | Value |
| --- | --- |
| Visible 10:00 interval | 600 <= game seconds < 601 |
| Native clock / time formatter input | 600.34130859375 |
| Reader playback time used by the separate record query | 599.3580932617188 |
| Observed applied prefix | Section 59, offset 139093 |
| Its record timestamp / projected game time | 599.3298950195312 / 600.336669921875 |
| Future pending record | Offset 139117; timestamp 599.3626098632812 |
| Requested game-time cutoff | 600.000 |
| Game-time query applied prefix | Section 59, offset 135925 |
| Its record timestamp / projected game time | 598.9608764648438 / 599.9676513671875 |
| Next projected game time for that query | 600.032470703125 |

The separate queries have different boundaries. The native clock also differs
from the observed prefix's anchor projection by 0.004638671875 seconds. No fitted
offset or interpolation was introduced to make any of these clocks identical.

The prefixes differ by **119 records**. The original helper compared endpoint
states and found no supported-field differences. The final offline audit also
checked the intervening records against the current readers' state-changing
handlers: no roster/spawn/inventory record occurs; 14 candidate attribute,
resource, or destruction records target other fields or actors. None changes
the compared supported groups. This supports interval stability for those
decoder fields, not every transient native field or actor 1505's identity.
The receipt retains opcode counts and candidate index classifications.

## Native comparison and retained unknowns

Seven groups per player are counted: name, hero definition ID, K/D/A as one
group, complete native item definition/instance/quantity multiset, resource 6
float32 bits, resource 7 float32 bits, and native CS (resource 14).

| Query | Match | Mismatch | Unknown | CLI/API |
| --- | ---: | ---: | ---: | --- |
| Observed record cutoff, all ten | 64 | 0 | 6 | Equal |
| Observed record cutoff, actors 1500/1501 | 14 | 0 | 0 | Equal |
| Requested game 600 seconds, all ten | 64 | 0 | 6 | Equal |
| Requested game 600 seconds, actors 1500/1501 | 14 | 0 | 0 | Equal |

The selected comparisons are subsets, not extra independent players. The top
support status remains partial even when the selected actors' groups all match,
because support audits the entire recorded roster before selection.

All nine other players have seven supported matching groups. Actor **1505** has
a matching supported name, while its hero association, K/D/A, native inventory,
balance, net worth, and CS are **identity_unproved**, hence unknown rather than
zero, mismatched, or successful.

Its roster and all consumed spawns agree on definition ID **257**. The roster
skin hash is **1054951559**, but the first spawn at section 0, offset 8749 uses
**3836149698**. The later 59 spawns before the 600-second cutoff use the roster's
hash. Selecting only later matching snapshots would discard the initial conflict;
the existing `conflicting_spawn` result is therefore retained. The captured
native actor can expose values without proving the decoder's identity association.

## Screen comparison and display limits

Screen transcription and captured native/formatter observations match **40/40
groups**: K/D/A, CS, cached gold text, and visible inventory icon count for each
of ten rows. There are **46 visible inventory icons**. Actor IDs and team/row
mapping were connected through the privately preserved names and native roster.

This is a screen-to-observation comparison. It does not make the six unknown
decoder groups for actor 1505 supported. Exact rendered icon identity, order,
stack quantity, portrait identity, and skin asset identity were not independently
certified from pixels. Native item instances/quantities are a separate comparison.

All ten visible gold labels match the last captured formatter inputs and label
calls. Cached text can lag current resource 7; for example actor 1501's resource
7 is 6591.04150390625, while its observed 6.5k label was formatted from
6528.04150390625. A direct formatting candidate is an estimate and must not
replace observed display evidence or be called server-final gold.

The trace contains no observer error and matched **31,806/31,806 consecutive
clock tick transitions** bit for bit. The replay-record timestamp, anchor
projection, accumulated native clock, and integer screen label remain distinct.

## Cleanup, validation, and remaining limits

The owned game and observer stopped; the final audit verified that no owned
observer or worker remains and no command is pending. The two scheduled tasks
were removed only after exact action path/arguments and worker identity checks;
their definitions were archived privately. Other user tasks/processes were not
selected for cleanup. Original **615 prelaunch sections** and **13 temporary
practice-slot sections** match their saved hashes and creation/write times.
All 121 H5672 source hashes and the original/LAA executable hashes remain unchanged.

Related tests passed **80**: native roster, player-state time query, service,
CLI, and display values. The full suite was **not rerun** for this documentation
increment. Offline receipt checks additionally verified source/log hashes,
baseline preservation, all four CLI/API pairs, native counts, screen counts,
capture/stability overlap, record classification, and cleanup receipts.

Earlier failed setup, lock-screen, and interrupted attempts were not counted as
captures. The existing development session subsequently encountered repeated
response-stream/capacity errors. After it stopped, the authorized relay completed
only cleanup and evidence documentation in the same checkout and branch.

This adds **one independent recording** on the same tested LAA client/computer.
The original recording client version is unverified; definitive eligibility stays
false. Server-final winner, gold, and duration remain uncertified. No final-result
correction, product policy relaxation, new PR, merge, or deployment is part of
this increment.
