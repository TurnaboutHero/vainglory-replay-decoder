# Native scoreboard integration — 2026-09-07

This document preserves the September 7 investigation and its dated fixture counts. Current product behavior is summarized below and in the [offline reliability guide](PRODUCT_RELIABILITY.md); historical test counts are not the current regression result.

## Current integration contract

The safe capture schema is `decoder_v2.capture.v2`, and safe final output uses `decoder_v2.match.v2`. Capture K/D/A may be accepted as a source/time/roster-bound observation, while `accepted_for_index` stays false. Final K/D/A, minion kills, gold, winner and exact duration remain withheld. Structural validity and an apparently complete recording do not independently validate a final score.

`UnifiedDecoder` now reads native state through EOF without using its heuristic duration as a cutoff. It retains native status/reason/as-of time and recording evidence, but its ordinary final K/D/A/minion/gold fields remain null without final validation. Legacy duration convenience values have `duration_provenance`: unknown, estimated or supplied_truth, always with final-index acceptance false. A supplied truth source is retained separately, including when no duration is present.

## Native reader behavior

`vg.core.native_stats` reconstructs observed scoreboard counters from native
`03f3` snapshot assignments and `041c` / `041d` SET/ADD messages. Snapshot
values replace state; counting messages or assuming a zero initial state is
not equivalent. The receiver-derived offsets and evidence scope are described
in [mismatch causes](MISMATCH_CAUSES_2026-09-07.md) and
[native statistic labels](NATIVE_STAT_LABELS_2026-09-06.md).

`GameTime` and `RecordTime` are distinct query types. The core reader requires
strict record framing, a supported `046f` clock anchor in every section, and
whole-input clock integrity even for an early capture. Missing baselines,
unsupported layers/counts/layouts, and out-of-coverage queries withhold state.
A later full snapshot replaces earlier state; unsupported layers not reset by
the native snapshot remain tainted. Invalid state never becomes zero.

Omitting the core reader cutoff consumes every record through EOF, including
updates whose interpolated game time exceeds the final endpoint after a paused
clock anchor. `RecordTime` is bounded and filtered by record timestamps;
`GameTime` retains its game-clock coverage and filtering. First/last game times
describe recording endpoints, not interpolation extrema. Requested actor IDs
must be unique positive uint32 integers; booleans and coerced numeric IDs are
rejected as `invalid_query`.

Both `UnifiedDecoder` and `decoder_v2` consume this reader. Unified output
includes `native_stats_status`, `native_stats_reason`, and `as_of_game_time`.
Its current whole-recording native read is independent of the duration estimate. Unknown final player
counters remain `None`, JSON emits `null`, CSV emits blank cells, and team/batch
sums stay unknown if any required value is missing. Truth comparisons count
unavailable values separately from matches and mismatches.

## Public capture API

```python
from vg.decoder_v2.decode_match import decode_match
capture = decode_match("/path/to/replay.0.vgr", at_game_time=1551)
print(capture.to_dict())
```

```bash
python -m vg.decoder_v2.decode_match /path/to/replay.0.vgr \
  --at-game-time 1551 -o capture.json
```

The capture schema is `decoder_v2.capture.v2`; its explicit scope and requested
and observed times accompany the player values. Capture K/D/A is not accepted
for the final-match index. Final winner, gold, duration, and minion counts are
withheld in this schema. Capture debug output similarly avoids whole-recording
gold, winner, and minion candidates. Negative/nonfinite CLI times are rejected
with exit status 2. Omitting the option retains the final-match completeness
gate. Unified has no capture option because its other fields use the whole
recording.

## Historical verification — September 7, 2026

The following counts and runtime assertions describe that historical run, before later conservative final-field changes. They are not reasserted as current universal accuracy or a current full-suite result.

- Existing tournament truth names were matched exactly without changing the
  truth file or widening the comparison population. At each supplied capture
  time, all 294 K/D/A values for 98 matched players across 10 coherent fixtures
  agreed. M5 and M6 each contribute 9 matched names; the other 8 contribute 10.
- M9's 27 comparable K/D/A values are unavailable, not counted as corrected
  matches. All 10 parsed players have unavailable K/D/A in capture output.
  Default v2 withholds accepted K/D/A, winner, and gold; Unified emits unknown
  K/D/A/minion counts and winner.
- Corpus screening covered all 56 real replay starts, excluding AppleDouble
  metadata. 53 yielded native state. M9 was rejected as `mixed_segments` due
  to a backward clock jump. Two other recordings remain `unsupported_clock`:
  their only threshold anomalies occur at section 0→1, with game deltas
  16.730141 / 21.140392 seconds over record deltas 10.015263 / 10.006122.
  The remaining 148 / 115 transitions did not cross the integrity threshold.
  This does not prove those two recordings were mixed.
- Real CLI checks covered `--help`, M6's successful capture, M9's withheld
  capture, and nonfinite input rejection. JSON scope and withheld gold were
  checked from the actual output files.
- Final full suite: `python -m unittest discover -s tests -q` passed all 305
  tests in 29.127 seconds. At that time the Unified regression exercised endian
  ID conversion and a record-time cutoff. Current Unified decoding instead reads
  native state through EOF and withholds final fields; the historical cutoff
  result does not describe its present behavior.
- Unit regressions cover snapshot replacement, SET/ADD, signed resource
  updates, layer taint, missing baselines, query clocks/coverage, malformed and
  mixed inputs, capture/final separation, and nullable export consumers.

## Limits

These results validate the compared captured counters, not every final match
score. The per-section game-clock interpolation and discontinuity tolerances
are conservative supported-profile checks, not a complete reconstruction of
the native UI timer. The two unsupported clock starts remain unresolved.
The corpus screen verifies structural/state support, not scoreboard truth for
53 games. Resource 14 was historically mapped to `minion_kills` in Unified. Current
final Unified/v2 fields remain withheld; raw resource observations do not extend
its native display-label proof or authorize final-index acceptance. Gold formulas, winner algorithms, identities, item extraction, and the
underlying final-completeness detector are not newly validated here. Current v2 final gold values remain null with an explicit withholding decision.
The [October runtime follow-up](RUNTIME_DISPLAY_2026-10-03.md) explains observed
UI gold caching for two playback paths and clock agreement for those runs;
general final-gold reconstruction, end-time interpretation and broad corpus
compatibility remain unresolved. A hash-bound final-screen comparison matches
only its listed K/D/A/CS counters; gold, winner, duration and result remain
observation-only, even when comparison_status is matched.

Local detailed QA artifacts are kept under the ignored
`.superpowers/sdd/2026-09-07-native-stats/` directory. Raw replays and player data
are not included in this change.

Follow-up: [startup clock investigation](CLOCK_STARTUP_2026-09-08.md) identifies
independent clock stores and an intentionally omitted clock-reset message.
The two unsupported inputs remain withheld; no startup origin was repaired.
