# Recorded values and client display evidence

`decode_player_state` and the default state-json CLI add `display_values` with
schema `vg.client-display.windows_2026_10_11.v1`. Existing player resources,
record times, recording-client status and definitive admission are preserved.
Legacy unified JSON and batch state JSON include this object through their
existing player-state service. Final-safe output continues withholding final fields.

Each `gold` row is identified by recording-scoped `native_actor_id`. `raw.value`
is resource 7, with the same native field provenance as `players[].net_worth`;
`players[].gold_balance` remains the distinct spendable resource 6. `observed`
is null by default. `direct_raw_candidate` is a stateless float32 formatter
estimate marked `estimated`. It can differ from cached game text.

The documented client refreshes only when `trunc(float32(resource7 *
float32(0.01)))` exceeds its previous 100-gold bucket. The formatter receives the
actual resource value at that update and applies `float32(0.001)` and `%.1fk`.
An EOF number cannot recover the last UI refresh, and rounding down to a bucket
does not recover that formatter input. The Python formatter remains a candidate
outside the named validation corpus, including platform rounding edge cases.
See the [native display study](RUNTIME_DISPLAY_2026-10-03.md) and
[terminal-call validation](TERMINAL_DISPLAY_CALLS_2026-10-11.md).

`time.raw.seconds` is the native anchor plus recorded interval at the selected
boundary, or null with `status=unknown` when mapping is unavailable. It is not
certified match duration. The last anchor is reported separately. Supplying
`playback_speed=5` (CLI `--playback-speed 5`) adds a conditional
`playback_clock_estimate`: last anchor plus record interval times speed. Its
reason states the open-gate and constant-speed assumptions. Actual frame deltas,
pauses, seeks and float32 stores are unavailable from EOF state, so an estimate
does not acquire an observed label. Without a supplied speed the estimate is null.

## Optional runtime receipt

Pass a parsed receipt as `runtime_evidence=receipt`, or use CLI
`--display-evidence receipt.json`. The accepted input schema is
`vg.terminal-display-observation.v1`, as illustrated by the
[two-case receipt](evidence/2026-10-11-terminal-display/summary.json).
Exactly one case must match `replay_scope`; terminal evidence cannot attach to a
timed capture. The case must cover the same source section count and actor set,
and every resource-7 value must equal decoded EOF state. Float32 values/bits,
formatter labels, increasing buckets, event ordering, recorded clock/last anchor,
one terminal/final callback and artifact hashes are checked. The supported
observation client is the documented LAA build, not the recording's original build.

`observed.status=supplied_runtime_observation` reports that receipt's label,
formatter input, call sequence and trace/screenshot/client/collector hashes.
`reconstructed.status=reproduced_from_observed_formatter_input` reports a label
reproduced from the supplied formatter input. These call sequences describe the
last UI update, which may precede the recorded-end resource boundary. Both remain
distinct from `raw` and from the stateless candidate. Time reconstruction uses
integer seconds from the supplied time formatter. A receipt is not independently
authenticated by matching hashes in its own contents; the source explicitly says
`supplied_receipt_not_independently_authenticated`. Supplied certification flags
are ignored, and no value becomes definitive.

Malformed, mismatched, incomplete or unsupported receipts are rejected; CLI
errors preserve existing output. Evidence files participate in output alias
protection and rehashing alongside replay inputs. They are never overwritten by
the report path. Source/build and server-final certification remain false, and
`definitive_analysis.eligible` stays false.
