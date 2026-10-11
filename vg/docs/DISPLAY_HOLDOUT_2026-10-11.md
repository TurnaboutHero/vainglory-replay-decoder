# Fresh 5v5 display holdout, 2026-10-11

H5621 completed full LAA playback on winsrv. All ten observed gold labels match
the actual result screen and the last formatter inputs. Eight differ from
directly formatting recorded-end resource 7. The clock formatter receives
1074.1488037109375 seconds and the screen shows `17:54`. Recorded-time mapping
remains unknown and this replay remains excluded from definitive analysis.

The [numeric receipt](evidence/2026-10-11-display-holdout/summary.json) preserves
float32 values/bits, call sequences, source scope and private artifact hashes.
Raw replays, player identities, screenshots and full traces remain private.

## Frozen selection and provenance

Before decoding, the protocol selected the newest complete ranked 5v5 recording
from the [public replay archive](https://replays.richardtravel.com).
Two metadata candidates were inspected: H5622 was excluded by non-5v5 mode
metadata, then H5621 was selected. Bundle checksums and continuous-v1 offsets
reconstructed all 108 source sections with no unused bytes. Section hashes match
between local acquisition, the Windows source copy and the post-cleanup copy.
The selection does not depend on observed accuracy.

First-section hashes, full replay scopes and match UUIDs were compared against
136 prior local families, representing 95 unique scopes. No overlap was found.
Acquisition provenance identifies the archive and exact bytes; it does not
authenticate the recording client build or the server's final result.

The implementation baseline is `2b257cb89fcf3ddc681aa3f3fff19cd2b652983b`, with
the preterminal time-call acceptance correction included in this increment.
Playback used the same guarded LAA client, probe and byte manifest as the
[previous terminal-call study](TERMINAL_DISPLAY_CALLS_2026-10-11.md).
The receipt contains their exact hashes. No original-versus-LAA comparison was
performed for this specimen.

## Gold cache reproduced on new actors

All 769 gold formatter calls link to a preceding row with identical native
resource-7 bits and a strictly increasing 100-gold cache bucket. All ten final
resource values equal decoded `players[].net_worth`. All ten last formatter
labels match the screen. The formatter applies float32 `0.001`; the refresh
gate applies float32 `0.01`, rather than replacing the raw value with a bucket.

| Actor ID | EOF resource 7 | Last formatter input | Screen / reproduced label | Direct EOF candidate |
| --- | ---: | ---: | --- | --- |
| 1500 | 13709.875 | 13700.875 | 13.7k | 13.7k |
| 1501 | 11027.833 | 11000.833 | 11.0k | 11.0k |
| 1502 | 11781.750 | 11700.750 | 11.7k | 11.8k |
| 1503 | 6387.625 | 6333.625 | 6.3k | 6.4k |
| 1504 | 13588.500 | 13504.500 | 13.5k | 13.6k |
| 1505 | 5484.250 | 5400.250 | 5.4k | 5.5k |
| 1506 | 8594.334 | 8501.334 | 8.5k | 8.6k |
| 1507 | 6895.833 | 6800.833 | 6.8k | 6.9k |
| 1508 | 9454.333 | 9400.333 | 9.4k | 9.5k |
| 1509 | 7783.167 | 7732.167 | 7.7k | 7.8k |

Values are rounded only in this table; the receipt retains exact bits. Actor
IDs are scoped to this recording. EOF resource 7, spendable resource 6, the last
formatter input and cached text remain separate values. The eight disagreements
are display-cache behavior for this playback, not missing raw resource updates.

## Clock accumulation and a preterminal formatter

All 24,122 consecutive tick transitions match the observed native operation:
double-precision delta times playback speed plus previous clock, stored as
float32. All 108 anchor values match the source sections in order. No seek was
performed; playback started at 1x and changed through 3x to 5x.

| Observation | H5621 |
| --- | ---: |
| Last anchor | 1051.6890869140625 |
| Last recorded interval | 4.494140625 |
| Ticks from last anchor to terminal | 71 |
| Observed delta sum / multiplier | 4.49201301112771 / 5 |
| Terminal clock and last formatter input | 1074.1488037109375 |
| Actual result screen | 17:54 |
| Anchor plus recorded interval times 5, conditional arithmetic only | 1074.1597900390625 |
| Decoder recorded EOF time | unknown |

The full last-anchor tick sequence reproduces the terminal clock bit for bit.
Unlike the two earlier specimens, the last time formatter occurs immediately
before termination: formatter sequence 44841, terminal 44842, final callback
44843. All three have the same clock bits. No further time formatter runs after
the final callback. The validator now accepts this unchanged preterminal path
as well as the previously observed post-final path. Differing float bits,
overlapping sequence numbers and reversed terminal/final order are rejected.

The decoder flags frames 89 to 90: game-clock delta 15.117249 versus record
delta 10.005371. It retains native record order but does not assert a game-time
mapping. Consequently `display_values.time.raw.seconds` and the conditional
playback estimate remain null, including when an independent runtime receipt
supplies the observed `17:54`. The arithmetic example above is not emitted as
a supported estimate. Probe interception can affect frame timing; these
fractional values describe this run.

Terminal argument 0 and the queued end request both identify team 2. The result
screen says surrender and does not explicitly identify a winning side, so
`winner_screen_side` remains null. This establishes call agreement, not an
authenticated final winner.

## Analysis outputs, regression checks and cleanup

The [display-values contract](DISPLAY_VALUES.md) is exercised through both
`decode_player_state` and the default state-json CLI. Default CLI and API
outputs agree. Attaching the new receipt reproduces ten gold labels and the
time label, with matching CLI/API output, while preserving every original
player value and the definitive-admission result.

Raw, supplied observations and reproduced values remain distinct. Receipt
hashes are supplied evidence references, not independent authentication.
Recording-build and server-final certification remain false; definitive
eligibility remains false. The new regression test covers a preterminal
formatter with unknown recorded time and rejects stale values or invalid order.
All 888 tests pass. This extends the display corpus by one new 5v5 recording
on one computer, without claiming universal compatibility or server accuracy.

Two preparation attempts exited the client before replay injection after the
operator selected client exit; both returned code 0. They are excluded setup
errors, not playback failures of H5621. The successful attempt used a completed
practice slot. Its 15 sections were backed up before replacement and restored
with original hashes and creation/write timestamps. The 108 substituted sections
were archived privately. Owned game, probe and worker processes are absent;
the owned scheduled task was removed. Both executable hashes, both collector
hashes, both artifact hashes and all 108 source hashes remain unchanged.
