# Framed native player roster

`vg.core.native_roster.read_native_roster(frames, cutoff=None)` restores player
identities from ordered `03ee` records and corroborates their actor, definition,
and skin against `03f2`/`03f3`. The caller supplies exactly one recording. IDs are
unsigned BE32 values, never byte-swapped/truncated legacy IDs. Same-name actors
remain distinct. Every roster/spawn observation is retained with section, record
offset and original payload. The latest roster observation supplies the player
table state and must agree with the first effective actor spawn. A changed
definition remains visible but cannot replace an existing actor's definition.

This implementation is bound to Windows PE32 SHA256
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642` and original
932-entry definition manifest SHA256
`7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c`.
`native_roster_definitions.json` is a small manifest-derived subset of definitions
observed in the available corpus. Production decoding does not read truth files,
original binaries, or screenshots.

## Native path and byte contract

The independently exported dispatch branch at `004d274e` belongs to
`FUN_004cfec0`; the existing portable source is
[evidence/2026-09-09-binary-events/branches/03ee.c.txt](evidence/2026-09-09-binary-events/branches/03ee.c.txt).
A fresh read-only/noanalysis Ghidra export followed its `FUN_004d52a0` call,
then `FUN_0096d310`, `FUN_0095e5e0`, and `FUN_0095e9f0`.
Portable narrow exports and hashes are in
[evidence/2026-10-04-roster/manifest.json](evidence/2026-10-04-roster/manifest.json).

| Payload bytes | Meaning | Native evidence |
| --- | --- | --- |
| 0..63 | NUL-terminated UTF-8 name, at most 63 encoded bytes | `004d52a0` passes offset 0 to `0096d310`; offset 64 begins the separate account string. `0096d310` validates a byte-class state machine and shifts decoded codepoints by 6, masking continuation bytes with 0x3f. |
| 160..163 | BE32 native actor ID | Receiver applies `Ordinal_14`; `004d52a0` uses offset 0xa0 for player lookup, insertion and every setter. |
| 164..167 | BE32 definition index | Receiver swaps; apply passes offset 0xa4 to `0095e5e0`, which stores at player-entry+0x78. |
| 168..171 | BE32 skin hash | Receiver swaps; apply resolves offset 0xa8 using `0081e800`. |
| 210 | Team field low4 bits; high4 bits ignored | Both insertion and `0095e9f0` update mask with 0xf, storing at player-entry+0xb0. No capacity-based assignment or inferred left/right label. |

The native receiver copies exactly 216 bytes. Both observed 216- and 222-byte
variants share this prefix; the six extra bytes are retained as opaque bytes.
Other lengths are unsupported. Spawn corroboration uses documented BE32
`(definition, skin, actor)` at payload offsets 0/4/8 and separately accepts
03f2 lengths 122/126 and 03f3 lengths 746/750. A spawn alone never establishes
player membership.

`0096d310` writes each decoded codepoint to one 16-bit cell. Strict UTF-8 BMP
names (including Korean) are decoded without ASCII filtering or minimum name
length. Invalid UTF-8, missing terminators and non-BMP codepoints retain raw
bytes and explicit unsupported status. Non-BMP is not silently converted to a
wrong displayed character. No inference about arbitrary locale encodings is made.

## Definition labels

Fresh `load_catalog` decoding checks both original hashes and the native
manifest structure. Every included hero is resolved through its original Actor resource,
not by treating an internal manifest name as a display label: root+0x10 is a relocated readable hero name and root+0x14 is the
corresponding `CHAR_INFO_*_NAME` localization key. The resource's Actor symbol
is checked against the manifest name, and native kind 0 is hero.

| Definition | Manifest name | Actor label | Original resource |
| --- | --- | --- | --- |
| 254 | Hero009 | Krul | B12CAC1F749716B334009F34808535D4 |
| 255 | Hero010 | Skaarf | AE1602CE10CC9F2BD54B8C6470D89F16 |
| 256 | Sayoc | Taka | 818120F02620D498EAB91CECDE5964B5 |
| 260 | Hero016 | Rona | 733827CA71C55BDE9A3A1B7BFFAD3DBF |
| 446 | Sanfeng | San Feng (localized) | 1402F32D97257B15FE17F69783B78BB2 |

Exact resource hashes, relocated string offsets, native kind 0 and name keys
accompany every entry in the shipped metadata. The original English resource
`Localization/english.strings` is stored under its MD5 filename
`7ED4F1146624D2D991A07272993B26C4`; it is base64-encoded UTF-8 with SHA256
`209df4c745201dec58bd5ef2497f1835298b21cbc8f23bd1bb1669589462d8d4`.
Its exact key/value pairs resolve names, including `CHAR_INFO_SANFENG_NAME`
to `San Feng`. These are direct decoded asset fields, not
legacy-map guesses or roster/truth correlation. Unknown definitions remain
unresolved and do not borrow item names (including definition 515).

## Query and support boundaries

The reader reuses the existing native clock audit over the complete input even
for an early query. EOF includes all records; explicit `GameTime` and
`RecordTime` include only records at or before that boundary and reject
out-of-coverage input. `record_boundary=(section, record_offset)` identifies
the last included framed record; `as_of_game_time` is its audited per-section
clock projection, not the requested cutoff. A forward game-clock jump does not
invalidate monotone native record order: EOF and RecordTime may restore the
state while returning null for unproved game-time values. GameTime queries
still reject that clock mapping. Mixed segments, backward resets and malformed
records reject the read.

A latest roster definition or skin that differs from the first effective spawn
yields `conflicting_spawn`; a repeated spawn cannot silently change that join.
A missing spawn yields `missing_spawn`. Such players remain visible with raw
observations, while `valid=false` prevents a caller from treating unresolved
identity as accuracy. The same applies to unresolved required hero names.
The numeric team field is preserved with raw-byte evidence; `team` stays null
because no left/right display convention is inferred here. Repeated spawns
are observations, not proof of respawns or new lifetimes.

## Verification

All 57 hero definitions observed in the corpus have verified original Actor
and English localization references. The final public-state coverage audit
restores all six field families for 504 players across 55 of 56 recordings.
C30/C52 support recorded-end state with unknown game-time mapping; timed
GameTime queries remain unsupported. C41 rejects mixed segments. These coverage
counts are separate from independent game-state accuracy comparisons.

The task evidence directory contains captured invocations, exit statuses,
source hashes, the fresh native exports and these real reader outputs:

- `task-2-tests.txt`: native roster, entity identity and strict record tests.
- `task-2-roster-error.txt`: identical-name distinct actors and embedded-marker adversaries.
- `task-2-roster.json`: normal17 and C34, one actor 1500 each; definitions 925/Amael and 243/Ringo respectively, with matching spawn IDs/skins.
- `task-2-c16.json`: all ten C16 roster actors 1500..1509, preserving recording order, names and native definition/skin associations.
- `task-2-c33.json`: dedicated item-buy recording identity evidence.

These are fresh structural/native association results. Final independent
rendered label/name comparisons belong to the root's capture and strict
comparison tasks; green unit tests and corroborating records do not replace
those observations. LSP was unavailable and its installation previously
declined; compilation/import checks and focused tests are the available checks.
