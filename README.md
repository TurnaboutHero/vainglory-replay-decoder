# VG Reverse Engineering

Vainglory: Community Edition (VG:CE) replay file (.vgr) binary format analysis and data extraction toolkit.

## Overview

This project reverse-engineers the VGR replay binary format to extract match data including player names, hero selections, team compositions, game modes, and entity interactions. All analysis is performed on locally-stored replay files.

### Current event evidence (2026-09-10)

Latest offline research: the [161-code binary candidate inventory and validation plans](vg/docs/vg-binary-event-candidates-2026-09-09.md) preserves named and unresolved candidates, observed payload variants, and native/corpus evidence. The [0452 postgame follow-up](vg/docs/POSTGAME_OFFLINE_2026-09-09.md) separates callback evidence from final-score acceptance. These publications add research evidence, not newly validated gameplay semantics or changes to final-stat extraction.

See the [event catalog](vg/docs/EVENT_CATALOG_2026-09-08.md), [endgame boundary investigation](vg/docs/ENDGAME_BOUNDARY_2026-09-08.md), [death action and crystal-source proof](vg/docs/DEATH_EVENTS_2026-09-09.md), and [next implementation plan](docs/plans/2026-09-09-event-semantics-next.md). The timeline exposes native `0x03f1` end actions, `0x0430` death actions and `0x040b` deletion observations, with optional verified definition names and selected Actor resource kinds. The [recorded counter-gap audit](vg/docs/TERMINAL_COUNTER_AUDIT_2026-09-09.md) preserves unmatched observations without changing final statistics. The [September Windows replay follow-up](vg/docs/WINDOWS_REPLAY_ACCEPTANCE_2026-09-10.md) records the earlier C16 replay-entry failure. The [October runtime display validation](vg/docs/RUNTIME_DISPLAY_2026-10-03.md) records successful C16 final playback, clock agreement for that path, and the cached gold-display behavior. Final-match acceptance remains gated. The legacy achievement table below contains historical claims and is not a substitute for those scoped validation records.

### Key Achievements

| Data | Method | Accuracy |
|------|--------|----------|
| Player names / UUID | Player block marker `DA 03 EE` parsing | 100% |
| Team assignment | Offset +0xD5 from player block | 100% |
| Game mode | `GameMode_*` string extraction | 100% |
| Hero selection | Offset +0xA9 uint16 LE | 100% (37 confirmed + 20 inferred = 57 total) |
| Hero hash | Offset +0xAB (4 bytes, unique per hero) | 100% |
| Entity ID | Offset +0xA5 uint16 LE | 100% |
| Match length | Frame file count | 100% |
| Weapon items | `FF FF FF FF [item_id 2B LE]` pattern | 100% |
| Item purchase event | Action code `0xBC` (Entity 0) | Confirmed |
| Skill level-up event | Action code `0x3E` (Entity 0/128) | Confirmed |
| Win/Loss | Turret ID clustering + Crystal destruction pattern | 99% (1 replay validated) |
| K/D/A | Native snapshots + SET/ADD state at a requested game clock | 294/294 compared values across 10 coherent capture fixtures; final-match scope remains gated |

### Hero Coverage

57 of 57 heroes mapped (37 confirmed at 100%, 20 inferred at ~80% avg confidence):

- **Original (0x00 suffix)**: Catherine, Ringo, Skaarf, Joule, Glaive, Koshka, Petal, Krul, Adagio, SAW
- **Season 1-3 (0x01 suffix)**: Ardan, Fortress, Baron, Skye, Reim, Kestrel, Lyra, Idris, Ozo, Samuel, Phinn, Blackfeather, Malene, Celeste, Gwen, Grumpjaw, Tony, Baptiste, Reza, Grace, Lorelai, Kensei, Magnus, Kinetic, Silvernail, Ylva, Yates, Inara, San Feng, Taka, Vox, Rona, Flicker, Lance, Alpha, Churnwalker, Varya, Miho
- **Season 4+ (0x03 suffix)**: Leo, Caine, Warhawk, Ishtar, Viola, Anka, Karas, Shin, Amael

## Project Structure

```
vg/
  core/                        # Core parsing library
    vgr_parser.py                # Main replay parser (CLI + library)
    vgr_mapping.py               # Hero/Item ID mappings (57 heroes, 80+ items)
    hero_matcher.py              # Legacy heuristic hero detection
    config.py                    # Configuration constants
    replay_extractor.py          # Replay file extraction utilities
  analysis/                    # Analysis & research scripts
    action_code_analyzer.py      # Event action code statistical analysis
    win_loss_detector.py         # Match outcome detection (turret patterns)
    turret_team_mapper.py        # Turret-to-team clustering analysis
    kda_payload_analyzer.py      # K/D/A event payload statistical analysis
    kda_lifecycle_detector.py    # K/D/A entity lifecycle tracking
    cross_replay_hero_validator.py # Inferred hero validation across replays
    entity_lifecycle_tracker.py  # Entity state machine analysis
    hero_id_mapper.py            # Unknown hero ID inference engine
    player_kill_detector.py      # Kill event detection (research)
    entity_network_mapper.py     # Entity interaction graph builder
    deep_event_mapper.py         # Event structure deep analysis
    extract_all_item_ids.py      # Item ID discovery (FF FF FF FF pattern)
    item_id_linker.py            # Item purchase event correlation
  tools/                       # Utility scripts
    replay_batch_parser.py       # Batch replay processing (JSON/CSV)
  output/                      # Analysis results (gitignored)
  docs/                        # Documentation
    REVERSE_ENGINEERING_NOTES.md # Detailed research notes
    HACKEDGLORY_SEMANTIC_COMPARISON_2026-05-18.md # Packet-decoder semantics mapped to .vgr research targets
```

## Usage

```bash
# Parse a single replay
python vg/core/vgr_parser.py /path/to/replay.0.vgr

# Batch parse all replays in subdirectories
python vg/core/vgr_parser.py /path/to/replays/ -b

# Parse with debug event output (per-player action counts)
python vg/core/vgr_parser.py /path/to/replay.0.vgr --debug-events

# Analyze action codes (0x42/0x43/0x44 phase distribution)
python vg/analysis/action_code_analyzer.py /path/to/replay/

# Detect win/loss from turret destruction patterns
python vg/analysis/win_loss_detector.py /path/to/replay/cache/ --debug

# Extract item IDs from replay
python vg/analysis/extract_all_item_ids.py /path/to/replay/

# Batch analysis summary
python vg/tools/replay_batch_parser.py /path/to/replays/ -o batch_summary.json
```

### Native scoreboard capture

```bash
# Query observed K/D/A at game-clock 25:51 (1551 seconds)
python -m vg.decoder_v2.decode_match /path/to/replay.0.vgr --at-game-time 1551 -o capture.json
```

Capture output uses `decoder_v2.capture.v1` with `scope`, `at_game_time`, and
`as_of_game_time`. Captured K/D/A is excluded from the final-match index;
final winner, gold, duration, and unaccepted minion counts are withheld.
Without `--at-game-time`, the existing final-match completeness gate applies.
Missing native baselines, unsupported state, malformed records, and clock
integrity failures produce unavailable statistics (`null`), never guessed zeros.

See [native integration evidence and limits](vg/docs/NATIVE_STATS_INTEGRATION_2026-09-07.md).

### Batch and index output safety

`python -m vg.decoder_v2.batch_decode` and `python -m vg.decoder_v2.index_export`
reject output paths that name a discovered replay section, alias one through
a symbolic or hard link, or introduce another section into a replay family.
Index export also protects supplied correction JSON files. These errors return
exit status 2 before writing. Reports are published atomically, preserving an
existing report if publication fails.

## VGR Binary Format

### File Structure

```
Filename: {match_uuid}-{session_uuid}.{frame_number}.vgr
Size per frame: 50-170 KB
Total per match: 5-20 MB (3v3), 10-30 MB (5v5)
```

The replay system uses **input recording**: player inputs and game events are recorded per frame, and the game engine reconstructs the full state during playback.

### Player Block Structure

Player blocks are identified by marker `DA 03 EE` (or `E0 03 EE`). Block size is approximately `0xE2` bytes:

```
[Marker 3B] [Player Name (ASCII, variable length)] [padding...]
  +0xA5: Entity ID (uint16 LE) - unique per player, used in event stream
  +0xA7: 00 00
  +0xA9: Hero ID (uint16 LE) - maps to BINARY_HERO_ID_MAP
  +0xAB: Hero Hash (4 bytes) - unique per hero, consistent across replays
  +0xAF: Skin/Account Hash (4 bytes) - varies per player, not per hero
  +0xD4: 02
  +0xD5: Team ID (01=left/blue, 02=right/red)
```

### Hero ID Encoding

Hero IDs use a uint16 LE format where the low byte encodes the hero number and the high byte encodes the release era:

| Suffix (high byte) | Era | Examples |
|--------------------|-----|---------|
| `0x00` | Original (2014) | Catherine(`0xF200`), Ringo(`0xF300`), Skaarf(`0xFF00`), Joule(`0xFD00`) |
| `0x01` | Season 1-3 | Ardan(`0x0101`), Baron(`0x0501`), Lorelai(`0x9901`), Kinetic(`0xA401`) |
| `0x03` | Season 4+ | Caine(`0x9303`), Leo(`0x9103`), Ishtar(`0x9A03`), Karas(`0x9D03`) |

### Event Structure

```
[EntityID 2B LE] [00 00] [ActionCode 1B] [Payload 32B]
```

#### Action Codes by Game Phase

| Code | Phase | Frame Range | Accuracy | Payload Entity Fields |
|------|-------|-------------|----------|-----------------------|
| `0x42` | Early game | 3-12 | 59.0% | 10 fields |
| `0x43` | Mid game | 12-51 | 96.4% | 3 fields |
| `0x44` | Late game | 51+ | 95.7% | 12 fields |

#### Special Action Codes

| Code | Entity | Purpose |
|------|--------|---------|
| `0xBC` | 0 (system) | Item purchase trigger |
| `0x3E` | 0 / 128 | Skill level-up |
| `0x05` | varies | Game tick / frame update |
| `0x08` | varies | Movement related |

### Entity ID Ranges

| Range | Classification |
|-------|---------------|
| 0 | System (game engine broadcasts) |
| 1-1000 | Infrastructure |
| 1000-20000 | Turrets / Objectives |
| 20000-50000 | Minions / Jungle camps |
| 50000-60000 | **Players** |
| 60000-65535 | Special entities |

### Item Storage

Items are stored with the `FF FF FF FF` marker pattern:
```
FF FF FF FF [item_id uint16 LE]
```
Item IDs range from 101 (Weapon Blade) to 423 (Stormcrown). See `vgr_mapping.py` for the full mapping.

## Research Status

### Solved
- Player identity (name, UUID, team, entity ID, hero)
- Hero hash fingerprinting (4-byte unique identifier per hero)
- Game phase detection via action code distribution
- Item purchase event detection (`0xBC`)
- Skill level-up detection (`0x3E`)
- Win/Loss via turret team clustering (ID gap 834-2519) + Crystal destruction pattern (6+ turrets in 5-frame window)

### In Progress
- **K/D/A**: Native snapshots and SET/ADD updates now restore observed counters. Ten coherent capture fixtures matched all 294 compared K/D/A values; this does not establish final-score accuracy for every replay. Mixed or unsupported clock profiles remain withheld. See the native integration evidence above.
- **Inferred hero validation** (20 heroes at ~80% confidence via suffix pattern + release chronology)

## Disclaimer

This project is for **educational and research purposes only**. It analyzes locally-stored replay files generated by the game client. No server exploitation, network interception, or game modification is involved.

This project is not affiliated with Super Evil Megacorp (SEMC) or the Vainglory Community Edition team. All game assets and trademarks belong to their respective owners.

## License

MIT
