# Compare an observed final screen

`python -m vg.analysis.final_screen_comparison` compares EOF native K/D/A and resource14 counters with an independently transcribed final screen. It checks the exact numbered replay SHA-256 scope and screenshot SHA-256 before matching the complete roster by big-endian entity ID. Player names are optional cross-checks, never join keys.

```sh
python -m vg.analysis.final_screen_comparison replay.0.vgr \
  --observation observation.json --screenshot final.png -o comparison.json
```

The observation uses this structure, with one row per recorded player:

```json
{
  "schema_version": "vg.final-screen-observation.v1",
  "replay_scope": "sha256:<64 lowercase hexadecimal characters>",
  "screenshot_sha256": "<64 lowercase hexadecimal characters>",
  "capture_stage": "final_screen",
  "provenance": {
    "transcription_method": "manual_visual",
    "observed_at_utc": "2026-10-03T07:15:23Z"
  },
  "screen_side_to_team": {"blue": "left", "orange": "right"},
  "winner_screen_side": "blue",
  "duration_display": "27:53",
  "players": [
    {
      "entity_id_be": 1506,
      "screen_side": "blue",
      "kills": 9,
      "deaths": 9,
      "assists": 12,
      "cs": 137,
      "gold_display": "16.5k"
    }
  ]
}
```

Use `vg.core.stat_evidence.frame_scope(load_frames(replay_file))` for the replay scope. It includes section numbering, lengths and content. Missing or mismatched hashes are errors. The caller must visually verify the transcription and the screen-to-roster mapping: hashes establish artifact identity, not transcription accuracy. The screenshot is hashed as bytes; this tool does not perform OCR or authenticate the image.

Results retain both native and observed values for each counter as `matched`, `mismatch` or `unavailable`. A mismatch never changes native counters. `cs` compares the displayed value with native resource14; a match validates that particular observation, without establishing its meaning on all recordings. `as_of_game_time` is the recorded EOF clock, not the displayed final duration.

Winner, duration and gold display remain `observation_only`. No kill-lead inference, raw end-match team interpretation, exact gold conversion or timer correction is applied. For C16, the observed blue team wins with28kills against37; K/D/A and CS match all40 native values at EOF, while the approximate legacy duration1690 differs from the displayed27:53. These observations do not authorize a general final-stat algorithm.

The output is a separate `recording_specific_final_screen` report with `accepted_for_index=false`. Default match decoding and index gates remain unchanged. Private screenshots, player handles, replay bytes and machine paths do not belong in Git.

When a final screen shows a surrender or another result without identifying a winner, supply `"winner_screen_side": null` explicitly. The counter comparison still runs; `observed_winner` retains null sides with `status="not_observed"`. The optional `result_display` preserves the actual nonempty result text as `observation_only`. No winner is inferred from that text, roster presence, team kills or a queued end request. Omitting `winner_screen_side` remains an input error.

Exit codes:0 for complete counter agreement;1 for a written mismatch/unavailable report;2 for invalid inputs or failed output. Output paths cannot alias numbered replay sections, the observation or screenshot, including symlinks and hard links. Reports use the existing atomic replay output writer.
