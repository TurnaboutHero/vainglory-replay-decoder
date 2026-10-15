# Recording identity and selected-viewpoint diagnostics

`read_native_roster(...)` and the default `decode_player_state(...)` API/CLI add
`recording_identity`, an evidence-only diagnostic. Player state uses a compact
summary; the native-roster report retains the full observations. Existing player values,
roster validity, support status, end requests, winner handling and definitive
eligibility are unchanged. The v2 safe/debug JSON contracts are unchanged.
Existing positional dataclass callers remain valid because the field is optional
and appended. No new CLI option is needed:

```sh
python -B -m vg.decoder_v2.decode_match replay/match.0.vgr -o reports/state.json
python -B -m vg.decoder_v2.decode_match replay/match.0.vgr --at-game-time 600 -o reports/capture.json
python -B -m vg.core.native_roster --replay-root replay --output reports/roster.json
```

```python
from vg.decoder_v2.player_state import decode_player_state

state = decode_player_state('replay/match.0.vgr')
evidence = state.recording_identity
for history in evidence.external_id_histories:
    print(history.native_actor_id, history.status, history.candidates)
print(evidence.selection.status)
```

## Compact default and explicit full detail

Default player-state `recording_identity.detail_level` is `summary`. It contains
per-actor candidate values/conflicts, observation/empty counts, candidate first
and last source pointers, selected actor/team consistency, selection counts and
status counts, and the same query boundary and content scope. Its size grows
with actors, distinct candidates and issue types, not repeated snapshots.
`source_count` references the existing state-level `source_files` hashes.

For complete per-occurrence evidence, use the existing native-roster report
command above, or `read_native_roster(frames, cutoff).recording_identity` /
`read_recording_identity(frames, cutoff)`. These retain every observation and
raw payload. Candidate first/last pointers in the compact summary do not replace
that full history. No new command-line flag or input format is required.

## External-ID history, not an authenticated account

For exactly the supported 216/222-byte `03ee` layouts, payload bytes 64..127
contain a separate NUL-terminated byte string. The actor is BE32 at +160. A
nonempty string is a raw external-ID candidate, regardless of UUID syntax or
UTF-8 decoding. A 64-byte unterminated field is unknown, not a 64-byte ID.

In the full native-roster diagnostic:

- `observations` retains every included occurrence, including empty values,
  the entire bounded `raw_field_hex`, nullable `raw_value_hex`/`utf8_value`,
  original payload, length, time and source location
- `candidates` deduplicates exact nonempty bytes and retains every source
  location; later empty snapshots never erase historical candidates
- Distinct values for one actor produce `conflicting_candidates`; a value
  shared across actors produces `shared_candidate`, with explicit
  `shared_with_actor_ids`. Neither silently selects or merges an account
- Unterminated fields remain `incomplete`. Unsupported lengths and reserved
  actor IDs 0/0xffffffff remain in `unassigned_external_id_observations`,
  with the original payload; unknown layouts are never decoded speculatively
- Empty-only history stays `empty_only`, not a claim that an account was deleted

This extends typed access to bytes already retained in the roster's original
`raw_payload_hex` history. It does not repair missing raw history or emulate a
native latest-state setter that ignores empties. Display names and actor IDs
are not globally unique. The association key is `(replay_scope, native_actor_id)`.
`authenticated_account_id` remains null.

## Recording-selected actor/team, not uploader identity

For exactly 101-byte `03e9`, +0 is BE32 selected actor and +100 is a raw team
byte. Observations keep that byte separate from its low nibble `team_id`.
Selection comes from a mode-dependent getter, including alternative cached,
team-fallback and configured-name paths. The wire record does not identify the
mode. It authenticates neither a participant nor the uploader.

The summary exposes `recording_selected_actor_id` and
`recording_selected_team_id` only when all included selection observations
are supported, agree on one valid actor/team, and all supported roster team
observations for that actor agree. These strict scalars are historical
consistency diagnostics, not a latest-state prediction. The full observation
history remains available through the native-roster diagnostic when the scalar
summary is null.

- Actor 0xffffffff is unresolved even if the team byte is 1: the native team
  getter explicitly defaults to 1 for actor -1. Actor 0 is also reserved here
- Supported teams for this diagnostic are nibble values 1/2; other values stay
  visible with `unsupported_team` and an unresolved summary
- Unsupported selection length, any unsupported roster layout, or a supplied
  section sequence beginning after zero prevents a confident scalar summary
- Changing selections, missing roster and conflicting roster team history have
  separate statuses. Valid-plus-sentinel evidence remains unresolved

`authenticated_uploader_identity` remains null. No terminal-team equality,
win/loss, rank, AFK, connectivity, or penalty decision is added.

## Provenance and query boundary

Both detail levels reuse the production framed-record parser and native query
selection. Full input framing/clock validation runs even for early queries.
All observations share the inclusive `record_boundary` with player state.
An invalid query exposes source evidence but no interpreted observations.
Player filtering does not filter or recompute recording-wide diagnostics.

`replay_scope` uses the existing `vgr-numbered-series-v1` content hash over every
supplied section number, length and exact bytes, even for early queries.
Full diagnostic `sources` supplies per-section size and SHA-256; player-state
`source_files` also supplies paths, and its compact diagnostic gives `source_count`. Scope is content-bound: renaming identical numbered bytes
does not change it. It is not an authenticated match ID or proof of completeness.
`completeness_status` is always `unknown`.

File APIs and CLIs use existing `select_replay`/`replay_sections` discovery:
ambiguous multi-family directories require an explicit `.0.vgr`; siblings with
another prefix cannot be joined. The roster batch CLI interprets each family
separately. Duplicate section aliases are rejected; gaps invalidate the native
query. Existing safe-output checks prevent overwriting replay sources.

The low-level `read_recording_identity(frames, cutoff=None)` API, like other
native readers, requires exactly one recording's numbered bytes. Bare byte
tuples have no filenames and cannot detect a caller combining unrelated
families. Use the path-based API to enforce filename-family selection. Content
hashes bind supplied bytes; they cannot authenticate their origin.

## Native evidence and limits

Pinned text disassembly and hashes are in
[evidence/2026-10-15-recording-identity/manifest.json](evidence/2026-10-15-recording-identity/manifest.json):

- Writer `004cb030`: `004cb211` calls selected-actor getter `00939790`; the
  network-order value is stored at payload +0. `004cb243` calls team getter
  `0093b1d0` and stores its byte at +100. It emits exactly 101 bytes
- Getter `00939790` has mode-dependent cached/flag-selected versus
  team/name-based paths. `0095da80` sets the mode flag and configured name
- Team getter `0093b1d0` reads roster +0xb0 low nibble, returns 1 for actor -1
  and 0xff for an unmatched actor
- Existing [03e9 receiver](evidence/2026-09-09-binary-events/branches/03e9.c.txt)
  stores actor +0 and team +100 into a flagged roster row
- Existing [03ee receiver](evidence/2026-10-04-roster/004d52a0.c.txt)
  passes the +64 string through `0095ea90`, whose pinned setter writes roster
  entry +0x44 without authenticating it

The reviewed LAA Windows executable SHA256 begins `d6717c15`; clearing its
single LAA header flag reproduces the existing reference hash `659f9eed`.
Full hashes and the exact flag difference are recorded in the manifest. The
native code bytes are identical; this is not recorder-build verification.
`recording_client_verified` stays false.

In the already-used H5810 development recording, ten initial 222-byte roster
records contain ten nonempty candidates; 1,680 periodic 216-byte snapshots are
empty. All 168 selections record actor 1505/team 1, corroborated by 169 roster
observations. One development fixture cannot establish cross-build validity,
account ownership, independent holdout accuracy, or final-result certification.

Synthetic tests cover byte retention, malformed and unsupported fields,
sentinel/default-team handling, changing/conflicting observations, shared IDs,
query cutoffs, source hashes, mixed-family isolation, API/CLI agreement and
unchanged legacy output. No replay files, client binaries, or raw user identifier
values are committed with this change. Diagnostic reports can contain personal
identifier observations: inspect their sharing scope before publishing them.

## Same-source integration check

The [redacted integration receipt](evidence/2026-10-15-recording-identity/integration-verification.json)
compares baseline commit `65bab83ae27e4c0f81338471a30a4aa1ee0944df` with this
change on the exact same H5810 files, at recorded end and inclusive record-time
100. Removing only the additive `recording_identity` field gives identical
canonical hashes for the complete preexisting player-state and roster outputs
at both boundaries. The source hashes, content scope, support and eligibility
results are unchanged. The receipt retains no raw external-ID values.

Detailed history remains in the explicit roster diagnostic. H5810 adds only
4,790 bytes of compact summary JSON to default state at recorded end and 4,764
bytes at record-time 100. Full diagnostics are 1,414,045 and 113,348 bytes
respectively. These are measured examples, not size bounds or controlled
performance benchmarks. A synthetic repetition test grows 1 to 256 empty
observations while the compact summary grows only 980 to 985 bytes; the full
report grows 2,077 to 201,959 bytes.

The final offline suite passes 972 tests, including 40 new focused identity
tests. The receipt gives source hashes and canonicalization details. Its
state hashes retain runtime paths and establish same-source equality; they
are not portable golden hashes for a renamed fixture directory.
