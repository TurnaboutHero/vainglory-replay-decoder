# Resource6 gold diagnostics

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

The legacy estimate `600 + round(positive ADD total)` remains partial and unaccepted as final earned gold. A fixed starting amount omits other game modes and initial state. The normal practice control shows30.3k while this formula produces972; another practice recording shows30.0k with no resource6 operation records. Neither case authorizes replacing600 with another universal constant.

Native references: [SET/ADD trace](NATIVE_EVENT_TRACE_2026-09-06.md), [binary verification and build limits](NATIVE_EVENT_BINARY_2026-09-06.md), and [Windows resource apply/store path](TERMINAL_COUNTER_TRACE_2026-09-09.md). The Windows path is pinned to its executable hash; the separately inspected Android/VGNA arithmetic is not a claim of complete cross-build equivalence.

Final match/index gold remains withheld. Rounded screenshot values do not establish an exact earned-gold getter or a universal display-rounding rule.
