# End-match action on held-out recordings (2026-10-05)

Follow-up to [ENDGAME_BOUNDARY_2026-09-08](ENDGAME_BOUNDARY_2026-09-08.md). It checks the native `0x03f1`
ActionEndMatch record against eight held-out recordings that no development step had used. They are VGNA
community client uploads from 2026-10-04/05: five 5v5 and three 3v3. The recordings and player names are not
published, and matches are labelled V1–V8 here.

## Independent reference

The reference is VGNA's own parser output (`parsed.json`), so it is a second parser and not ground truth.
Its winner field comes from a terminal match result that may be the same `03f1` record, so agreement on
the winner is **not** independent evidence by itself. The independent signal is VGNA's objective list.
That list records which team's Vain Crystal was destroyed, using the same team numbering as the
players (1/2 mapped to decoder `team_id` 1/2 for 68/68 players).

## Results

| check | result |
|---|---|
| `03f1` present | 7/8. Absent only in V7, where VGNA also found no terminal summary and derived completion from the crystal kill |
| winner value = VGNA winner = decoder `team_id` of VGNA's winning players | 7/7 |
| winner value ≠ team whose Vain Crystal VGNA saw destroyed (independent) | 4/4 crystal endings |
| reason byte | 2 in V6 (3v3; no crystal objective, consistent with surrender); 0 in the other six |
| records after `03f1` | 0–9 per file, all with the end action's record time |
| fields changed by post-end records | none: K/D/A, CS, gold balance, net worth and items are identical when cut just before `03f1` (7/7) |

V3 was labelled a surrender before decoding: a 5v5 match with no Vain Crystal objective. Its reason byte
is 0. VGNA's objective list lacks a Vain Crystal entry in 11 of 24 recent 5v5 matches (one has no objectives
at all) but only 1 of 12 3v3 matches, which suggested an omission in the reference.

### Playback check (2026-10-05)

The recordings were played in the Steam client using the large-address-aware copy, following the procedure
in [PLAYBACK_STABILITY_2026-10-05](PLAYBACK_STABILITY_2026-10-05.md). Each was seeked near its end and played
at 1x with screenshots every 2 s. The VGNA-client recordings play in the Steam client.

| recording | reason byte | final screen centre label | last frames |
|---|---|---|---|
| V6 (3v3) | 2 | `항복` (surrender), 19–16, 13:49 | no crystal destruction |
| V3 (5v5) | 0 | `승리` (victory), 27–2, 23:08 | winners in the enemy base, then Vain Crystal shards before the result screen |
| C16 (5v5, development corpus) | 0 | `승리`, 28–37, 28:10 | (full playback, see stability doc) |

V3 therefore ended by crystal destruction, not surrender. The pre-decoding label was wrong because VGNA's
objective list omitted the crystal. Reason 2 took the surrender display in the one surrender checked, and
reason 0 took the victory display in both crystal endings checked.

V8 (VGNA `archive_contiguous=false`) and V4 differ from VGNA's duration by about 24–28 s. Their record
times have no gap of more than 2 s between sections. In both, VGNA measured duration from packet
timestamps rather than the native game clock, so the gap is a clock-source difference, not truncation.

## What this supports

- `03f1` winner value uses the same low-nibble team id that the decoder reports as `players[].team_id`.
  On these recordings it identified the winners 7/7 and agreed with the independent crystal evidence 4/4.
- Absence of `03f1` should be read as "end not recorded" (V7), never as a result.
- In this sample, recorded-end state and state cut at the end action agree, so post-end records did not
  change the decoded fields. The earlier corpus had up to 65 post-end records, so this is not a general rule.

## What it does not support

- That reason 0 always means a crystal ending, or that every surrender has reason 2. Playback confirmed
  one surrender (reason 2) and two crystal endings (reason 0); other reason values were not observed.
- That the recording client's result equals the server's or ranked record. This is client-recorded
  reconstruction.
- Final gold and duration display semantics. Those remain separate questions (see RUNTIME_DISPLAY).

Scripts and per-match outputs are kept with the private evaluation data, not in this repository.
