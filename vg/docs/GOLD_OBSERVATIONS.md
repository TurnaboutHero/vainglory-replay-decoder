# Native gold observations and resource6 diagnostics

`decode_gold_from_replay(...).native_observation` reconstructs the recorded EOF state from a native baseline and resource updates. It is also available at `gold_debug.native_observation` in `python -m vg.decoder_v2.decode_match REPLAY.0.vgr --format debug-json`.

| Observation field | Meaning |
| --- | --- |
| `valid`, `status`, `reason` | Whether the supported recorded state could be reconstructed |
| `players[].entity_id` | Recording-scoped big-endian actor ID |
| `players[].gold_balance` | Resource6 balance, including purchases/debits and balance assignments |
| `players[].net_worth` | Resource7 raw float, used by the inspected Windows scoreboard and `myNW` export |
| `as_of_game_time` | Interpolated native anchor time at EOF; not final match duration |

The enclosing `replay_scope` binds the observation to the exact input sections. Baselines at snapshot payload286/290 replace state, so a practice baseline of30000 and a normal baseline of600 need no mode-specific constant. Positive resource6 ADD increases both resources; resource6 debits or SET do not increase resource7. Explicit resource7 updates are applied too. Native stores round to float32. Mode0 is ADD and every nonzero mode is SET in this reader.

Missing baselines, invalid identities, malformed records, mixed clocks, unsupported relevant payloads, nonfinite values and float32 overflow withhold the observation. An applicable later full snapshot may replace earlier unsupported semantic state; invalid full-input framing or clock coverage cannot be repaired that way. A valid observation is neither an accepted final result nor a reconstruction of the cached display string.

The Windows row only refreshes gold when `int(net_worth * float32(0.01))` increases, then formats the value using `%.1fk`. Consequently directly formatting EOF net worth can differ from a previously cached label. Do not fit a floor/round rule to screenshots. See [native dataflow and remaining duration boundary](NATIVE_GOLD_TIME_2026-10-03.md).

Resource6 operation0 is an ADD request and operation1 is a SET request. A SET value is not a refund amount or a spending delta. Repeated balance assignments must not be summed into income or refunds, and a negative SET must not count as spending.

`decode_gold_from_replay` exposes the following partial observations:

| Field | Meaning |
| --- | --- |
| `action_06_income` | Sum of positive supported ADD values |
| `action_06_spent` | Absolute sum of negative supported ADD values |
| `action_06_last_set_value` | Last supported raw SET value, including zero or negative values; null if none |
| `action_06_set_count` | Number of supported SET observations |
| `action_06_sellback_refund` | Deprecated, always null; no refund amount is established |

The last SET is a recorded request value, not a reconstructed current balance. Native clamping, later ADDs, snapshots and unsupported records can change state. `record_issues` and the partial status remain relevant even when a supported observation exists.

The legacy per-player `gold` estimate `600 + round(positive ADD total)` remains partial for compatibility and is unaccepted as final earned gold. Use `native_observation` for baseline-aware raw state. The normal practice control shows30.3k while this formula produces972; another practice recording shows30.0k with no resource6 operation records. Their reconstructed EOF resource7 values are30372 and30000 respectively.

Native references: [SET/ADD trace](NATIVE_EVENT_TRACE_2026-09-06.md), [binary verification and build limits](NATIVE_EVENT_BINARY_2026-09-06.md), and [Windows resource apply/store path](TERMINAL_COUNTER_TRACE_2026-09-09.md). The Windows path is pinned to its executable hash; the separately inspected Android/VGNA arithmetic is not a claim of complete cross-build equivalence.

Final match/index gold remains withheld. The recovered resource7 getter does not establish match completion or reproduce the final UI cache state; rounded screenshots cannot validate an exact raw float.
