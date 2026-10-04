# Independent player-state reference registry

`vg.tools.player_state_accuracy` is an offline verification tool. Production
readers must not import it. Private assets and generated manifests stay outside
commits. A successful inventory audit is not an accuracy claim.

## Commands

Use Python 3.14 with `-B`, from the repository root:

```sh
python3.14 -B -m vg.tools.player_state_accuracy prepare --asset-root /path/to/work --output-dir /path/to/reference
python3.14 -B -m vg.tools.player_state_accuracy audit --manifest /path/to/reference/manifest.json --output /path/to/audit.json
python3.14 -B -m vg.tools.player_state_accuracy compare --manifest /path/to/reference/manifest.json --recording normal17 --require-six-fields --output /path/to/comparison.json
```

`prepare` reads the root-exported `accuracy-20261004/corpus/manifest.json`, local
`stat-followup-20261003/controls/{normal17,C34}`, and the two original historical
JSON files under `offline-repo/vg`. It hashes sources without decoding recordings
(including held-out recordings). It writes metadata only, preserves original
historical values, and creates `freeze.json` containing the manifest SHA256.
An existing manifest is never overwritten. Add new independently acquired
observations to a new registry and freeze that new manifest explicitly; editing
the original registry invalidates its freeze. The corpus partition is preserved.

`audit` verifies hashes, aliases, source inventory and the 56/109/60 expected
counts. Historical tournament rows and item-count rows remain separate arrays;
overlap entries resolve M1..M11 to corpus recordings using replay filenames.
They never become 169 additional players or complete six-field references.
M5/M6/M9 and all other rows remain present regardless of coverage.

`compare` and its `verify-capture` alias invoke the real decoder CLI for each
observation. `--surface default-cli|legacy-cli` chooses the public surface;
`--reader roster|counters|inventory` calls the component reader directly.
Component readers must report their actual applied record boundary. Missing
boundary or component fields are failures, including fields a component has not
yet implemented. Full integration should provide these fields before acceptance.
`--require-six-fields` requires all seven scalar/group entries below (balance and
net worth together form the gold category). Without a component selection, the
same complete comparison is performed. `--all-observed` documents whole-registry
selection; observations are never silently dropped and missing references remain
failures. `--recording` can be repeated and accepts registry aliases.

`--coverage-only` inventories selected recordings and their declared support,
without decoding or certifying accuracy. It is a source-coverage report, not a
native-state-coverage claim. `--expect-support-status` runs a negative support
assertion; a successful assertion does not certify numeric accuracy.
`--mutate-reference remove-items|drop-one-duplicate-item|flip-one-gold-bit`
changes only an in-memory reference. Missing mutation prerequisites fail.

Exit codes: **0** requested audit/assertion passes; **1** missing source/truth,
inventory count discrepancy, mismatch or unsupported state; **2** schema,
integrity, collision, mutation precondition or invocation error. Reports contain
exact expected/actual values, source hashes, query/boundary, actor, denominators,
interpreter, commit and subprocess receipts. Output cannot alias an input through
its path, symlink or hardlink. Consumed inputs are rechecked before publication.

## Manifest and observations

Paths are relative to the manifest or absolute private paths. `source_files`
entries contain `section`, `path`, `sha256` and optional `size`/`source_path`.
Recordings contain `recording_id`, `aliases`, `partition`, `client_sha256`,
`replay_scope`, `support`, `source_files`, `images` and `observations`.
Missing support metadata remains unknown; no values are filled from truth.

`reference_sources` entries require `source_id`, `path`, `sha256`, and a `kind`
of `client_native`, `client_render`, `definition_asset`, or `receiver_apply`.
Decoder output is never an independent source. These tags identify evidence
provenance, not automatic proof: the capture author must establish independence
and the actor/clock boundary against actual client or static evidence.

An observation has `observation_id`, `clock_kind` (`recorded_end`, `game_time`,
or `record_time`), `record_boundary` (`section`, `record_offset`), `replay_scope`,
`source_refs`, and `players`. A timed capture supplies the finite nonnegative
`game_time` or `record_time` selected by `clock_kind`. EOF is never converted to
the last GameTime. Decoder output must return `scope` (`recorded_end` or
`capture`), the matching `requested_game_time` or `requested_record_time`,
`record_boundary`, `support_status`, and `players`. RecordTime additionally
requires `query_clock: record_time`. A different time, replay scope or boundary
fails comparison.

Record-time references can retain `observed_game_time` and its float32 bits as
independent native metadata. These values do not replace the record-time query.
The default CLI and component readers support this clock; the legacy CLI reports
`unsupported_query_clock` without being invoked. Such a rejection is not an
accuracy PASS. Native export requires the strict reader proof documented in
[player-state capture](PLAYER_STATE_CAPTURE_2026-10-04.md).

Each reference player has an independent `reference_player_id`, positive
unsigned 32-bit `native_actor_id`, `actor_link` with `status: observed` and
`source_refs`, and `fields`:

| Entry | Observed value |
| --- | --- |
| `name` | Exact client display name |
| `hero` | Independently resolved hero name |
| `kda` | `{kills, deaths, assists}` nonnegative integers |
| `minion_kills` | Nonnegative integer, independently established display meaning |
| `items` | `[{native_item_id, quantity}]`; quantity is a positive integer |
| `gold_balance` | Eight hexadecimal float32 bits, or `{float32_bits, value}` |
| `net_worth` | Same native float32 representation |

Every field wraps the value as `{status: "observed", value: ..., source_refs: [...]}`.
Use `status: "unobserved"` and omit the value for unknowns. Required unknowns
fail. A rounded UI gold label cannot supply native float32 truth. If raw value
and bits are both present they must agree. Nonfinite values are rejected.

Items compare native IDs and total multiplicities; no recipe/price inference,
set deduplication or slot-count substitution occurs. When `slot_order_proven`
is true, exact ordered entries including slots must also match. Empty observed
inventory is `[]`; missing inventory is null/unobserved. Numeric zero is valid.

Actual players use `native_actor_id`, `name` (or `display_name`), `hero_name`
(or `hero`), KDA group (or individual counters), `minion_kills`, `items`,
`gold_balance`, and `net_worth`. Optional `field_status` values that explicitly
withhold a field fail acceptance even if a numeric value is present.
Duplicate/lost actors and unproved actor links fail; names never serve as joins.

## Historical limitations

The 109 tournament rows preserve original names, heroes, K/D/A, displayed gold
and minion values. They lack independently established native actor links and
aligned capture boundaries. Their displayed gold is not native float32 state.
The 60 historical inventory rows contain only occupied slot counts; they do not
prove native item identity, multiplicity, order, or lifecycle semantics. Both
sources remain partial until independent acquisition supplies the missing proof.
