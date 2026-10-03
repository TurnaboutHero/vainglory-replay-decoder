# VG Reverse Engineering

Offline tools for inspecting, comparing and archiving Vainglory: Community Edition replay families. Start with the conservative decoder: a readable recording and an accepted capture do not establish verified final-match statistics.

## Start here

Use **Python 3.12 or newer** from the repository root. Python 3.12 is the syntax minimum, not a claim that every 3.12 runtime has been tested. The offline decoder, JSON/CSV exports, SQLite catalog and filesystem archive tools use the standard library. Windows screenshot capture needs Pillow and an interactive Windows desktop; native game probes have separate runtime requirements. See the [runtime and verification ledger](vg/docs/PRODUCT_RELIABILITY.md#runtime-and-verification).

Run the self-contained smoke tests without a private replay, truth file, game client or Pillow:

```sh
python -X utf8 -B -m unittest discover -s tests -p "test_product_quickstart.py" -v
```

The tests generate synthetic framed recordings, execute the documented offline commands and check source hashes. They prove those software paths, not compatibility with every game recording. For a persistent disposable example and the complete command sequence, follow the [offline quickstart](vg/docs/PRODUCT_RELIABILITY.md#offline-quickstart).

For your own recording, keep its `.0.vgr` and numbered siblings together and use a separate output directory that already exists:

```sh
python -B -m vg.decoder_v2.decode_match "replays/match.0.vgr" --format safe-json -o "reports/match.json"
python -B -m vg.decoder_v2.decode_match "replays/match.0.vgr" --at-game-time 1551 -o "reports/capture.json"
```

A single input may also be a directory containing exactly one replay family. Multiple families require an explicit `.0.vgr` selection or a batch command. Missing paths, unreadable sections, ambiguous selection and malformed input receive actionable errors.

## Choose the workflow

| Need | Entry point | What to retain |
| --- | --- | --- |
| Inspect one recording | `vg.decoder_v2.decode_match` | Safe field decisions, reasons and `replay_scope` |
| Observe a scoreboard moment | `decode_match --at-game-time SECONDS` | `decoder_v2.capture.v2`, requested/observed game time and roster identity |
| Build a dataset | `vg.decoder_v2.batch_decode`, `vg.decoder_v2.index_export` | Every input result, scoped `input_id`, status/counts and withheld fields |
| Use player/match spreadsheets | `vg.core.export_matches` | CSV provenance, blank unknowns, stable ordinals and export receipt |
| Use legacy metadata/statistics | `vg.core.vgr_parser`, `vg.core.unified_decoder`, `vg.analysis.batch_report` | Truth source, duration provenance and known/total sample counts |
| Maintain a SQLite catalog | `vg.core.vgr_database` | Catalog identities, nullable match values and catalog-only export coverage |
| Save and restore replay files | `vg.core.vgr_watcher`, `vg.core.vgr_loader` | Snapshot hashes, explicit target selection and any recovery path |
| Investigate protocol candidates | [40-command v2 capability matrix](vg/docs/decoder_v2/README.md#command-capability-matrix) | Consumed truth/replay/OCR/manifest inputs and research-only scope |

[Product reliability guide](vg/docs/PRODUCT_RELIABILITY.md) covers Python APIs, exit codes, partial batches, transactions, recovery, database behavior and archive limits.

## Read the evidence correctly

- `null` means unavailable; measured zero remains zero. CSV uses a blank cell for null. A duration estimate or supplied truth retains its provenance and is not final-index approval.
- Safe final output currently withholds final K/D/A, minion kills, gold, winner and exact duration. Captured K/D/A can be observed at a supported clock, but `accepted_for_index` remains false for those captured counters.
- The [C16 final-screen comparison](vg/docs/RUNTIME_DISPLAY_2026-10-03.md) and [native integration history](vg/docs/NATIVE_STATS_INTEGRATION_2026-09-07.md) are narrowly scoped evidence. A comparison's `matched` status covers the named K/D/A/CS counters; gold, winner, duration and result labels remain observation-only.
- General final-gold reconstruction, end-time interpretation and broad replay compatibility remain unresolved. A complete filesystem snapshot does not prove completed gameplay, and a successful slot replacement does not prove game playback.

## Historical research results

The original README advertised 100% for names, teams, modes, hero hashes, entity IDs, frame-count "match length" and weapon items. The underlying denominator and dataset were not recorded here, so those percentages are retained only as **historical claims with undocumented scope**. Frame coverage is not exact match duration. Its 99% winner claim cited one replay and cannot support a general accuracy rate. Current safe/index acceptance does not use those claims.

The earlier hero mapping listed 57 heroes, with 37 directly confirmed and 20 inferred. That is mapping coverage in the historical research, not a guarantee for all clients or recordings. The dated native capture study compared 294 K/D/A values across ten coherent fixtures; its exclusions and clock limits are preserved in the [September integration record](vg/docs/NATIVE_STATS_INTEGRATION_2026-09-07.md).

Current research references: [event catalog](vg/docs/EVENT_CATALOG_2026-09-08.md), [endgame boundaries](vg/docs/ENDGAME_BOUNDARY_2026-09-08.md), [death-action sources](vg/docs/DEATH_EVENTS_2026-09-09.md), [161-code candidate inventory](vg/docs/vg-binary-event-candidates-2026-09-09.md), and [postgame follow-up](vg/docs/POSTGAME_OFFLINE_2026-09-09.md). They retain unresolved candidates rather than promoting them to accepted final statistics.

## Historical binary research notes

The following layouts, ranges and heuristic rates describe the earlier research fixtures. They are not a current compatibility guarantee or authorization to publish final scores. Use the field decisions in current decoder output.

### VGR Binary Format

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

### Previously investigated
- Player identity (name, UUID, team, entity ID, hero)
- Hero hash fingerprinting (4-byte unique identifier per hero)
- Game phase detection via action code distribution
- Item purchase event detection (`0xBC`)
- Skill level-up detection (`0x3E`)
- Historical winner candidates used turret clustering and crystal patterns; current safe/index output withholds final winner.

### In Progress
- **K/D/A**: Native snapshots and SET/ADD updates now restore observed counters. Ten coherent capture fixtures matched all 294 compared K/D/A values; this does not establish final-score accuracy for every replay. Mixed or unsupported clock profiles remain withheld. See the native integration evidence above.
- **Inferred hero validation** (20 heroes at ~80% confidence via suffix pattern + release chronology)

## Disclaimer

This project is for **educational and research purposes only**. It analyzes locally-stored replay files generated by the game client. No server exploitation, network interception, or game modification is involved.

This project is not affiliated with Super Evil Megacorp (SEMC) or the Vainglory Community Edition team. All game assets and trademarks belong to their respective owners.

## License

MIT
