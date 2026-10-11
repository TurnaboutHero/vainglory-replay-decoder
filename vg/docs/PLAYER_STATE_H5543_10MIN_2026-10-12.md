# H5543 player state at displayed 10:00, 2026-10-12

H5543's actual LAA client scoreboard displayed **10:00** while its native game
clock remained **600.3882446289062 seconds**. All ten players matched the decoder
in **70/70 native field groups**, using both the observed reader cutoff and the
separate 600-second game-time query. Selecting actors 1500 and 1502 matched
**14/14 groups** and preserved the full-roster boundary. All four serialized
CLI/API JSON pairs were identical.

This adds an observed midpoint to the already used H5543 family. It is one
recording and one client/computer, not another independent recording or proof of
final winner, final gold, match duration or compatibility with every client.

The [sanitized evidence receipt](evidence/2026-10-12-h5543-10min/summary.json)
contains source scope, binary/script hashes, boundaries, float bits, counts,
formatter sequences, capture times and cleanup results. Original recordings,
player names, process identifiers, screenshots and full traces remain in private
local evidence. Their hashes are included so the underlying captures can be
identified without publishing them.

## Capture and boundary proof

The successful path was **GUI seek, 1x playback, reveal controls before the
target, pause, open scoreboard**. It was not uninterrupted playback from the
beginning to the captured midpoint. The native clock and complete ten-player
state were identical in **241 samples spanning 61.671 seconds**, including the
scoreboard capture at 2026-10-11 15:30:41.476025 to 15:30:42.399278 UTC
(2026-10-12 in Korea). The time formatter received the same clock float bits
as the observed native clock; the visible label was 10:00.

The manager's native paused flag was false. Runtime multiplier and delta were
both zero. The proof therefore uses observed stability, not that flag or a claim
of an atomic record snapshot. The reader retained an unchanged, strictly future
pending buffer. Its bytes uniquely matched section 62, offset 132887, in the
original recording. The immediately preceding record, offset 132863, establishes
the applied prefix. Source scope was checked across all 153 numbered sections,
against acquisition hashes and remote source hashes.

| Clock or boundary | Observed value |
| --- | --- |
| Screen 10:00 interval | 600 <= game seconds < 601 |
| Native game clock and time formatter input | 600.3882446289062 |
| Reader playback time, used as record query cutoff | 627.2740478515625 |
| Applied reader prefix | Section 62, offset 132863 |
| Applied record timestamp | 627.24267578125 |
| Applied prefix projected game time | 600.3727416992188 |
| Pending record | Section 62, offset 132887; timestamp 627.2926635742188 |
| Requested game-time query | 600.000 |
| Game-time query applied prefix | Section 62, offset 128535 |
| Its stored timestamp and projected game time | 626.8685302734375; 599.9985961914062 |
| Its next projected game time | 600.0151977539062 |

The two prefixes differ by **149 records**. The seven compared player field
groups do not change across that interval. This explains why both queries match
the captured state; it does not make their clocks or boundaries identical.
The observed native clock differs from the applied-prefix projection by
0.0155029296875 seconds. No fitted time offset was introduced.

## Native and screen comparisons

Each native comparison covers seven groups per player: name, hero definition,
K/D/A, complete native item definitions/instances/quantities, resource 6 float
bits, resource 7 float bits and native CS. This includes native hidden items;
visible inventory is a separate projection.

| Query | Native groups matched | Serialized CLI/API JSON |
| --- | --- | --- |
| Observed record cutoff, all ten | 70/70 | Equal |
| Observed record cutoff, actors 1500 and 1502 | 14/14 | Equal |
| Requested game 600 seconds, all ten | 70/70 | Equal |
| Requested game 600 seconds, actors 1500 and 1502 | 14/14 | Equal |

The selected groups are a subset of the ten-player comparison. Repeating the
comparison through two clocks and two interfaces does not increase the number
of independent players or recordings.

The screenshot independently confirms **40/40 screen groups**: K/D/A, CS,
cached gold text and visible inventory icon count for each player. There are
41 visible inventory icons. Exact rendered item identity, icon order, stack
quantity and portrait asset identity were not independently mapped from pixels.
Native item IDs and quantities were compared directly with native state, but
that comparison does not certify those screen details.

| Selected actor | K/D/A | CS | Resource 6 | Resource 7 | Native held item definition IDs |
| --- | --- | --- | --- | --- | --- |
| 1500 | 1/0/0 | 19 | 745.5 | 4795.5 | 524, 478, 458, 460 |
| 1502 | 0/1/0 | 80 | 992 | 6042 | 464, 499, 463, 478, 458 |

All selected held quantities are one. The lists above follow native array
order, not a certified screen order. The UI shows cached gold labels 4.8k and
6.0k for these actors, last formatted from 4774.5 and 6033 respectively.

## Gold and time display evidence

The last captured formatter/label calls reproduce all ten visible gold labels.
Formatting current resource 7 directly would disagree with **3/10 labels**:

| Actor | Current resource 7 | Direct candidate | Last formatter input | Captured/UI label |
| --- | --- | --- | --- | --- |
| 1503 | 4552.5 | 4.6k | 4502.5 | 4.5k |
| 1508 | 5062 | 5.1k | 5038 | 5.0k |
| 1509 | 4072 | 4.1k | 4009.5 | 4.0k |

These calls support the cache behavior documented in the
[terminal display investigation](TERMINAL_DISPLAY_CALLS_2026-10-11.md):
a current resource value and the last rendered label can differ. They do not
establish server-final gold. A direct formatter candidate remains estimated;
it must not replace missing observed/reconstructed display values.

The successful observer trace also matched **35,739/35,739 consecutive tick
transitions** bit for bit. This supports the captured clock behavior without
equating replay timestamps, projected game time, native accumulated game time
and integer UI text. The earlier terminal 33-second/2-second discrepancies
retain their separate evidence and scope.

## Failed attempts and limits

The initial replay request returned HOME with no open replay reader; the setup
cause was not isolated. A detached observer launch failed before attachment and
was excluded. A subsequent client loaded the same recording successfully.

Several pause attempts missed the target. When replay controls were hidden, the
first click revealed them instead of pausing playback. A wait also missed its
cutoff, and an atomic status-file replacement temporarily prevented a status
read. Captures showing 10:51 and 10:01 were excluded. The successful attempt
revealed controls before the target, then verified zero clock progression and
opened the scoreboard while the same native state remained stable.

One observer attached after loading, at about game second 34; the successful
replacement observer covered the seek/capture phase. This is not a claim that
every clock or display call from launch through match end was collected.
Instrumentation may affect playback timing.

The tested executable is identified by its LAA SHA-256 in the receipt.
The recording's original client version remains unverified. Its definitive
analysis eligibility remains false, and this capture does not certify
server-final winner, gold or duration. No decoder logic change or fixed
gold/time correction was justified by this midpoint comparison.

## Cleanup and validation

Owned game, observer and worker processes were absent after cleanup, and the
two owned scheduled tasks were removed. All **58 preserved practice sections**
were restored with matching hashes and creation/write times. This includes
35 original sections removed by native client launch and recreated from verified
backups. The injected 153-section temporary family was archived privately.
Original replay sources and both original/LAA executable hashes remained
unchanged.

The focused time-query, service, CLI and display-value suite passed **58 tests**
during this verification. The earlier implementation's 903-test run is described
in the [query guide](PLAYER_STATE_TIME_QUERY.md); it was not repeated for this
documentation-only increment. GitHub Actions has no configured workflows.
