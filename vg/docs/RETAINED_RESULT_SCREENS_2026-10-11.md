# Retained 5v5 result screens: winner, gold and time

This follow-up audits existing screenshots from two held-out recordings, H5543 and H5519. It does not repeat the completed playback experiment. For each recording, the retained evidence contains one seek-near-end result screen and two results reached by full playback. The six screenshots represent two recordings and 20 players, not six independent matches.

The [sanitized receipt](evidence/2026-10-11-result-screens/summary.json) binds the numbered recording scopes, screenshot hashes, manual transcription hashes, comparison hashes and previous post-result native evidence. It contains no player handles, machine paths, replay bytes, screenshots or dumps. Private originals and complete CLI reports remain in the local evaluation directory.

## What was checked

The decoder revision was `04e73640dd2af0dc54519d91e302e23d50255761`. All 305 numbered source sections were rehashed before and after the audit. Each screenshot was inspected visually for the complete roster, screen side, K/D/A, CS, gold label, result label and duration. Names were used privately to check the actor mapping; joins in the comparator use recorded entity IDs. Identical counter/gold transcriptions were confirmed in all three screenshots of each recording.

Each retained screen was processed through the real `vg.analysis.final_screen_comparison` CLI with its hash-bound observation. All six commands succeeded: 40 K/D/A/CS values per screen, **240/240 matched**. These are repeated observations of 80 unique counters. All reports retain `accepted_for_index=false`; the hash checks establish artifact identity, not independent authentication of the manual transcription or original recording client.

| Recording | Seek screen | Full A | Full B | Observed winning side | Queued end request |
|---|---|---|---|---|---|
| H5543 | 25:01 | 25:34 | 25:34 | orange; blue displays defeat, 9-16 | team 2, reason 0 |
| H5519 | 24:47 | 24:49 | 24:49 | blue; displays victory, 33-13 | team 1, reason 0 |

The recorded team mapping is blue=1, orange=2. The end-request team therefore agrees with the observed winning side on these two recordings and all six screens. This is further client-observation evidence, not a server or ranked result. The queued request remains a queued request, and the ordinary decoded winner remains unverified.

## Gold: direct EOF formatting fails on 9 of 20 players

All ten player gold labels per recording are identical across its three retained screenshots. A candidate that formats the latest recorded net worth directly, using float32 multiplication by float32(0.001) and one decimal place with a `k` suffix, disagrees with **6/10 H5543 players and 3/10 H5519 players**. Examples:

| Recording / actor | Recorded net worth | Direct candidate | Observed label |
|---|---:|---|---|
| H5543 / 1505 | 12368.8125 | 12.4k | 12.3k |
| H5543 / 1504 | 9852.978515625 | 9.9k | 9.8k |
| H5519 / 1509 | 13952.833984375 | 14.0k | 13.9k |
| H5519 / 1506 | 16090.7509765625 | 16.1k | 16.0k |

This falsifies that direct-formatting candidate on the new recordings. It does not establish a replacement conversion or recover exact final gold from rounded labels. The previous [formatter/cache study](RUNTIME_DISPLAY_2026-10-03.md) explains why cached inputs can differ from raw net worth on its own observed runs; these new screenshots do not contain the formatter call history needed to prove that mechanism anew. Native balance/net worth remain raw recording observations, and final gold remains unavailable.

## Time: neither EOF nor a fixed correction is final duration

| Recording | Decoded recorded-end seconds | Existing post-result native clock | Difference |
|---|---:|---:|---:|
| H5543 | 1501.378173828125 | 1534.5474853515625 | +33.1693115234375 s |
| H5519 | 1487.29052734375 | 1489.4930419921875 | +2.2025146484375 s |

The integer parts correspond to the seek and full-playback screen times respectively. The full A/B screen repeats agree within each recording. The differences vary across recordings, so neither direct EOF duration nor a universal two-second adjustment is supported. The raw record timestamp of an end request is also a separate clock domain and is not substituted for the game clock.

The previous post-result native captures still match the same decoded EOF player state 140/140 across both recordings. Those probes attached after the result screen and did not capture the pre-terminal clock advancement or gold/time formatter calls. Player-state agreement therefore cannot resolve the duration discrepancy. This audit rehashes that existing evidence; it does not claim a new live native capture or causally isolate speed, seek behavior, scheduling or UI caching.

## Remaining evidence needed

- Recording-client provenance: authenticated producing-build evidence bound to the numbered recording contents. The current files have no build identifier; the playback executable hash cannot supply the writer's identity.
- Final winner: an independent match-result source linked to these recording scopes. The available screen and queued action establish a client observation only.
- Exact final gold and time: a new controlled observation of terminal entry, clock anchors/advancement, time formatter arguments, gold row update inputs and retained UI labels. The current post-result snapshots lack that history. Any such experiment must vary a meaningful condition or use new material rather than repeat the completed stability runs.

Until those checks exist, all these recordings remain automatically excluded under the [definitive analysis policy](DEFINITIVE_ANALYSIS_ELIGIBILITY.md). This evidence adds no admission override and changes no decoder statistics.
