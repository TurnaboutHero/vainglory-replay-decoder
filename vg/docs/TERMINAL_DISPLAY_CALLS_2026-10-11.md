# Terminal gold and time display calls, 2026-10-11

Two instrumented full replays on winsrv reproduce the retained result screens:
H5543 ends at `25:34`, H5519 at `24:49`, and all 20 player gold labels match.
The nine disagreements with directly formatting EOF net worth are explained by
the client's gold display cache. The 33-second and 2-second differences from the
retained seek screens follow the client's speed-dependent clock accumulation
after its last anchor reset. These observations do not certify server results
or the recording client's version.

Numeric receipts, float bits, event sequence numbers, source scopes, and private
trace/screenshot hashes are in [summary.json](evidence/2026-10-11-terminal-display/summary.json).
The archived [probe](evidence/2026-10-11-terminal-display/probe.js) and
[byte guards](evidence/2026-10-11-terminal-display/manifest.json) are the exact
sources used for both successful runs. Raw replays, screenshots, player names,
full traces, process paths, and dumps remain private.

## Observation boundary

The decoder baseline was `6f4ac1ff437119a3977e1a90f2c6413e23a8c48c`.
Playback used the LAA client with SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
Both traces attached before replay selection, observed all 153 / 152 anchor
calls, one terminal call, one final callback, and the final time formatter.
They have consecutive event sequences, no trace errors, and a successful detach
12 seconds after the final callback. The source sections were rehashed against
the frozen decoder reports, including another 305 hash checks after cleanup.

Nine entry hooks observe gold rows, formatter inputs, the proven gold text
consumer, time formatting, anchor assignment, clock setters/ticks, termination,
and the final callback. They check relocated instruction bytes and the actor
handle generation before linking a display to an actor. No return/interior hooks
or gameplay/resource setters are invoked. Frida's instruction interception can
affect timing; fractional times below describe these runs, not an exact recovery
of earlier runs. Observation is bounded to 900 seconds / 120,000 events.

One initial H5519 playback request returned to home without any replay anchor
calls while the game process stayed alive. Its setup cause was not isolated and
it contributes no result fields. A subsequent preparation rejected an empty
section in an actively recording practice slot before replacement. The successful
retry used a completed practice slot. These exclusions are retained in the receipt.

## Gold: the last formatter input survives within a cache bucket

The observed path agrees with the earlier
[native display investigation](RUNTIME_DISPLAY_2026-10-03.md).
`006f6fd0` reads native resource 7 and compares its integer 100-gold bucket with
the row cache at `+f4`. Only an increasing bucket calls `00740390` with the
current raw value. `007a84e0`, restricted to the proven caller `007403cf`, receives
the resulting gold string. Ending the replay does not force every row to format
the current resource again.

All 1,007 H5543 and 1,064 H5519 formatter calls link to a preceding row whose
resource bits equal the formatter input and whose new bucket exceeds its cache.
All 20 EOF resource-7 values equal the frozen decoder's net worth. All 20 final
labels equal both the last observed formatter output and the retained screens.

| Replay / actor ID | EOF resource 7 | Last formatter input | Observed label | Direct EOF candidate |
| --- | ---: | ---: | --- | --- |
| H5543 / 1500 | 10367.459 | 10302.459 | 10.3k | 10.4k |
| H5543 / 1501 | 10899.396 | 10800.396 | 10.8k | 10.9k |
| H5543 / 1504 | 9852.979 | 9801.979 | 9.8k | 9.9k |
| H5543 / 1505 | 12368.813 | 12302.813 | 12.3k | 12.4k |
| H5543 / 1506 | 11769.542 | 11742.542 | 11.7k | 11.8k |
| H5543 / 1508 | 12478.854 | 12436.854 | 12.4k | 12.5k |
| H5519 / 1506 | 16090.751 | 16000.751 | 16.0k | 16.1k |
| H5519 / 1508 | 12861.474 | 12800.014 | 12.8k | 12.9k |
| H5519 / 1509 | 13952.834 | 13931.834 | 13.9k | 14.0k |

The table rounds raw values only for readability; the receipt preserves values
and float32 bits. Actor IDs are local to each replay. Row snapshots are taken
on entry: their cache/display fields can precede a formatter later in the same
call. Use the last formatter input and label sequence, not that entry snapshot
alone, to describe the final display. A raw balance, resource 7, a cached display
input, and a rendered label remain separate observations.

## Time: the final formatter receives the accumulated playback clock

`00549470` assigns the anchor input to controller `+194`. Between resets,
`005497a0` adds the observed delta at `020ec6d0` multiplied by the double at
`01a761b0`, then stores float32, when gate `+19d & 1` is clear. The exact
[Windows instructions](evidence/2026-09-08-windows-clock/native-evidence.txt)
multiply/add in double precision before that float32 store.

All 35,360 H5543 and 32,606 H5519 consecutive tick transitions, excluding
intervening anchor/setter/end calls, match that operation bit for bit. Starting
with each last anchor, applying every remaining tick also reproduces its terminal
clock exactly. The final `0073a770` input has the same bits as that terminal clock.
Integer seconds from this input agree with the screenshot. The shared scratch
text buffer is not treated as a durable time label because other formatting
calls overwrite it.

| Observation | H5543 | H5519 |
| --- | ---: | ---: |
| Last anchor | 1493.120361 | 1486.730835 |
| Last recorded interval | 8.257813 | 0.559692 |
| Decoder EOF, anchor + recorded interval | 1501.378174 | 1487.290527 |
| Observed delta sum after last anchor | 8.231146 | 0.604709 |
| Remaining ticks / multiplier | 140 / 5 | 11 / 5 |
| Terminal clock and final formatter input | 1534.275757 | 1489.754517 |
| New full-replay screen | 25:34 | 24:49 |
| Retained seek screen, earlier observation | 25:01 | 24:47 |
| Display difference | 33 seconds | 2 seconds |

The recorded interval multiplied by five estimates 1534.409424 / 1489.529297;
the actual tick sequence, rather than that estimate, produces the measured clock.
Earlier uninstrumented snapshots were 1534.547485 / 1489.493042. Their fractional
values differ, while both old and new full-replay displays give the same strings.
No new seek run was performed here. A constant 33-second or 2-second correction
would be unsupported: the last interval, speed, and frame timing differ by run.

## Result interpretation and cleanup

Terminal argument 0 is 2 for H5543 and 1 for H5519, agreeing with each queued
`03f1` team ID and the observed orange / blue winning side. This establishes the
client playback mapping for these files; a queued request and client result
screen do not authenticate the original server's final result.

This increment adds research evidence, without promoting display values to
definitive gold/duration or changing parser policy. Source/build provenance and
server-final certification remain false, and both cases remain excluded from
definitive analysis. The earlier
[retained-screen audit](RETAINED_RESULT_SCREENS_2026-10-11.md) remains the source
for its six screenshots and KDA/CS comparisons.

The two probes exited successfully; owned game, probe, and worker processes are
absent and the owned scheduled task was removed. All 29 backed-up practice
sections have their original hashes and creation/write times; 21 missing sections
deleted by subsequent native client launches were recreated from those backups.
Both executable hashes and all 305 source hashes remain unchanged. The worker's
exit acknowledgement timed out because its exit branch omitted `end_utc`; process
and scheduler checks independently confirmed cleanup. No server result was
inferred from that command acknowledgement.
