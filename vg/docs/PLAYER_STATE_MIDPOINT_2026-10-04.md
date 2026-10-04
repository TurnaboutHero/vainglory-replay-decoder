# Native midpoint player-state verification, 2026-10-04

The follow-up closes a coverage gap in the earlier EOF-only acceptance: one
independently observed C16 midpoint now matches all ten players and seven field
groups through the public Python API and default CLI, **140/140 comparisons**.
These are 70 independently observed groups checked through two surfaces. C16
was already a development recording; this adds a boundary, not a new holdout
or ten new distinct players to the earlier eight-recording result.

The new default CLI option `--at-record-time` exposes the API's existing
RecordTime query. Native GameTime alone did not select this observation's exact
prefix, so reference export rejects that mismatch and supports explicit record
time only after verifying the independently observed applied boundary.

```sh
python3 -B -m vg.decoder_v2.decode_match /path/to/C16.0.vgr \
  --at-record-time 894.6184692382812
```

Record time is seconds in the replay stream. It is distinct from displayed game
time. The option is mutually exclusive with `--at-game-time` and requires the
default `state-json` format. The legacy CLI does not expose record-time queries;
its explicit unsupported result is excluded from the accuracy denominator.

## Independent boundary and values

The root operator played the original recording in the pinned native Windows
client, paused it through the GUI, captured the scoreboard, and collected twenty
identical complete passive samples over five seconds. No decoder output supplied
the expected state. Names, native actor IDs, KDA, gold bits, CS, held instances
and quantities came from that capture; hero and item labels came from separately
hashed original definition assets. The native truth and asset mappings were
frozen before their first value comparison.

| Observation | Value |
| --- | --- |
| Native game clock | 866.5531616210938 seconds, float32 bits 1146659687 |
| Native reader playback time | 894.6184692382812 seconds, float32 bits 1147119509 |
| Strictly future buffered record | 894.649658203125 seconds, float32 bits 1147120020 |
| Pending record position | section 89, offset 79866 |
| Independently proven applied predecessor | section 89, offset 79842 |
| RecordTime query's selected boundary | section 89, offset 79842 |
| Observed GameTime query's selected boundary | section 89, offset 78602 |

Native dispatcher `004eb4a0` returns before dispatch when playback time is
strictly less than the pending buffer's timestamp. Both reader snapshots around
each complete sample agreed; repeated samples also agreed on every player and
clock field. The exact pending bytes and timestamp uniquely match the original
section. Sequential framing identifies its applied predecessor. All 171 source
sections match the archived injected bytes, verified injection receipt and
restored-slot receipt. The alternative source binding never modifies an older
receipt to invent a missing source fingerprint.

The captured reader was mode 1 and manager flags were 6. The proof correctly
retains `native_paused: false`; the GUI pause does not establish mode 2 or a
manager pause-bit transition. The sampler retains `atomic_record_boundary:
false`. A separate `stable_future_pending_buffer` proof establishes the stable
applied prefix from the native reader and original bytes.

Seven groups cover name, hero, KDA, visible held items, spendable gold, native net
worth and displayed CS. Gold comparisons require exact float32 bits. Inventory
compares IDs and quantities, without asserting rendered slot order. The original
[EOF acceptance](PLAYER_STATE_ACCURACY_2026-10-04.md) remains a separate
777/777 comparison result over eight recordings and 37 distinct players.

## Clock limitation

The file anchor at section 89 records replay time 890.0155029296875 and game time
861.96728515625. Its affine GameTime projection does not reproduce the separately
observed native game clock. At the applied boundary, projected game time is
866.5574951171875, 0.00433349609375 seconds ahead of the observed clock. At the
reader playback time, the difference is 0.01708984375 seconds.

The native client resets its clock from anchors and subsequently accumulates
runtime ticks with float32 rounding, a multiplier and a gate. Those runtime tick
partitions are not encoded by the file projection. This capture establishes the
divergence but does not isolate its precise runtime cause. No offset, epsilon or
rounding adjustment is fitted to the reference.

Default capture export therefore rejects this sample with
`unsupported_game_time_boundary` before writing a reference. Explicit
`export-reference --query-clock record_time` uses the observed reader playback
time and requires exact equality with the proven boundary. Equal-timestamp
partial boundaries and any other mismatch remain unsupported. The reference
keeps `observed_game_time` and its bits separately from the record-time query.

## Verification and retained limits

The changed implementation passed **852 tests on macOS/Python 3.14.7** and
**852 tests on Windows/Python 3.13.2**, with no failures or skips. Both hosts used
identical hashes for all 607 Python/core-definition files, and all 605 Python
files compiled in memory. The Windows test snapshot contained 1,057 files and
remained unchanged during execution. Subsequent report-only additions do not
change those tested code hashes. LSP diagnostics remain unavailable because the
language server is not installed.

Tests cover unstable or single native samples, wrong clocks and modes, missing
or changed injected sections, ambiguous records, first-record and cross-section
predecessors, forged EOF labels, exact query mismatches, equal-timestamp partial
prefixes, CLI clock conflicts, invalid times and unsupported output formats.
The [compact evidence index](evidence/2026-10-04-accuracy/followup-summary.json)
records native and reference hashes, actual comparison results, negative
controls, platform receipts and current source identity. Full private evidence
is retained under `.omo/evidence/accuracy-followup-20261004/`; it is required to
repeat the native comparisons. The exact final commit's review result is recorded
in that directory's ledger after the independent gate finishes.

The prior independent gate approved the EOF implementation at commit
`d4faf76d267f3d5643f23b9afe5cc147f006116b`. This midpoint is additional evidence,
not a substitute for any of the nine still-pending per-opcode runtime controls.
Their trigger, variant and guard requirements are reconciled in the private
`remaining-controls.md` report. In particular, no `0444` record occurred in the
56-recording corpus or the retained new challenges; no positive stack-control
claim was added. Universal replay compatibility and completed-match final scores
remain outside the demonstrated acceptance scope.

The follow-up restored all **13 original temporary-slot files**, including byte
hashes and timestamps, and verified that the owned game, observer, worker and
scheduled task were absent. Together with the prior 274 restored files this is
287 successful file restorations. All source recordings and the original
Windows checkout remain preserved.
