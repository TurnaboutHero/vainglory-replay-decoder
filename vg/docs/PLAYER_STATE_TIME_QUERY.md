# Query players at game 10:00

Run from the repository root with Python 3.12 or newer. Keep a replay's numbered
sections together. Create a separate output directory before using `-o`.

```sh
python -B -m vg.decoder_v2.decode_match "replays/match.0.vgr" --at-game-time 600 -o "reports/all-10min.json"
python -B -m vg.decoder_v2.decode_match "replays/match.0.vgr" --at-game-time 600 --player-id 1500 --player-id 1502 -o "reports/selected-10min.json"
```

First run the all-player query and choose IDs from `players[].native_actor_id`.
The IDs above belong to the H5543 example below; use the IDs in your own recording.
Names can repeat, and actor IDs are local to one recording. Selection preserves
roster order rather than argument order. All fields and display gold rows are
projected from the same full-roster decode; selection does not change the boundary.
`--player-id` is supported only by `state-json`, the default format.

The equivalent Python API returns dataclasses; call `.to_dict()` for JSON:

```python
from vg.decoder_v2.player_state import decode_player_state

everyone = decode_player_state("replays/match.0.vgr", at_game_time=600)
selected = decode_player_state("replays/match.0.vgr", at_game_time=600,
                               player_ids=[1500, 1502])
assert selected.players == tuple(p for p in everyone.players
                                if p.native_actor_id in (1500, 1502))
assert selected.record_boundary == everyone.record_boundary
assert selected.query_timing == everyone.query_timing
```

## Interpret the time boundary

`requested_game_time` is the requested cutoff. `as_of_game_time` is the projection
for the last included record, not an assertion that the game clock was observed
at that value. All native readers use that inclusive record boundary. Without an
exact boundary at the cutoff, state is carried through the preceding record;
fields are neither interpolated nor extrapolated to make an exact 600-second snapshot.

The additive `query_timing` object in `decoder_v2.player_state.v3` contains:

| Field | Meaning |
| --- | --- |
| `applied.record_boundary` | Last included section and record offset; equals the state boundary |
| `applied.record_time` | Actual timestamp stored in that record |
| `applied.projected_game_time` | Anchor game time plus record interval, or null when mapping is unavailable |
| `applied.anchor_record_time`, `anchor_game_time` | Anchor used for that projection |
| `next_record` | First record after the boundary; null at recorded end or for invalid queries |
| `cutoff_relation` | `exact_record_boundary`, `preceding_record`, `recorded_end` or `unavailable` |
| `seconds_before_requested` | Distance in the requested clock between cutoff and applied record |
| `bracketing_record_interval_seconds` | Actual timestamp interval to the next record; not proof of missing data |
| `clock_audit` | Full-family clock status and mapping validity, with reason |
| `coverage` | Observed game endpoints, section range/count and whether the family starts at section zero |

`state_interpolated` and `native_game_clock_observed` are false. Even an exact
projected boundary does not establish an independently observed native game clock.
Paused clocks that produce non-prefix selections, forward jumps, malformed records
and missing sections can make a game-time query unavailable. The full family is
audited, including data after the requested time. Do not treat a large interval
alone as missing data, or observed coverage as proof of completed gameplay.

For a known record timestamp, use `--at-record-time SECONDS` or
`decode_player_state(..., at_record_time=SECONDS)`. Game and record cutoffs are
mutually exclusive. Valid record order may remain queryable after a forward game
clock jump, but game-time projections and coverage are null in that case.

## Handle selection and unavailable data

`player_selection` reports all/selected mode, requested IDs, missing IDs, returned
count and selection status. IDs must be unique positive integers below `0xffffffff`;
the API accepts a nonempty list or tuple. Invalid arguments fail before loading or
replacing reports. If any requested actor is absent at the boundary, the selection
returns `support_status: player_not_found`, explicit missing IDs and no players or
display gold rows. An absent roster or failed clock audit remains unavailable;
selection cannot turn `out_of_coverage` or `unsupported_clock` into success.

Top-level `support_status` and `field_status` continue to audit **all recorded
players before selection**, as `player_selection.support_scope` states. Selecting
one supported player cannot promote a partially supported recording. Inspect that
player's own `field_status` for individual fields. Unknown fields stay null;
recorded zero stays zero. Domain statuses are JSON results with CLI exit code 0;
malformed arguments/input paths and report-write failures produce exit code 2.

`display_values.raw`, estimated formatter candidates and supplied observations
retain separate provenance. A terminal display receipt cannot establish a 10:00
capture and is rejected for capture queries. Definitive final-result eligibility
does not change: unverified source/client provenance still excludes the recording.

## Observed 5v5 example, 2026-10-11

Offline H5543 query at 600 seconds returned 10 supported players. The preceding
boundary was section 62, offset 128535: stored record time **626.8685302734375**,
anchor record time **620.0037231445312**, anchor game time **593.1337890625**.
Its projected game time was **599.9985961914062** (1.403809 ms before the request).
The next record, offset 128551, stored **626.8851318359375**, projected to
**600.0151977539062**. The bracketing record interval was **0.0166015625** seconds.

| Native actor ID | K/D/A | Scoreboard CS | Recorded balance (resource 6) | Recorded net worth (resource 7) | Visible item definitions, native array order |
| --- | --- | --- | --- | --- | --- |
| 1500 | 1/0/0 | 19 | 745.5 | 4795.5 | 524, 478, 458, 460 |
| 1502 | 0/1/0 | 80 | 992 | 6042 | 464, 499, 463, 478, 458 |

The selected API players and every field/provenance entry equaled their all-player
counterparts; selected CLI JSON equaled selected API JSON. Native state and boundary
values matched the pre-change all-player CLI baseline. All 153 section hashes/sizes
matched the acquisition manifest before and after querying. Full outputs, source
paths and player names remain in local evidence, outside version control.

This verifies the query and selection paths on one real family. It does **not**
independently verify game UI values at 10:00, recording client provenance, final
winner, final scores, cached gold labels or match duration. H5621 separately returned
`unsupported_clock` for 600 seconds because of a forward jump at sections 89 to 90.
Its exclusion applies even though the requested boundary precedes that jump.

A later [actual H5543 10:00 capture](PLAYER_STATE_H5543_10MIN_2026-10-12.md)
matched all ten players in 70/70 native field groups and the selected actors in
14/14 groups through both CLI and API. It records the GUI seek/pause path,
observed clock 600.3882446289062, distinct 600-second query boundary and cached
gold labels. That observation adds midpoint evidence without certifying final
results or the recording's original client version.

The Python 3.14.7 local suite passed **903 tests**, including 15 new timed-query
tests for selection consistency, repeated names/full actor IDs, actual boundaries,
CLI/API agreement, preserved reports, unknown IDs, coverage failures, future malformed
records, section gaps, clock jumps and display receipt scope. Run the focused checks:

```sh
python -B -m unittest tests.test_player_state_time_query tests.test_player_state_service tests.test_player_state_cli tests.test_display_values -q
```
