# Owned Windows player-state capture

The root operator owns the interactive worker, OS input, replay injection and
cleanup. `vg.tools.player_state_capture` supplies a bounded passive capture
command and offline evidence import/verification. It never launches a game or
takes ownership of an existing unrelated process.

## Offline evidence commands

```sh
python -B -m vg.tools.player_state_capture import --spec capture-spec.json --output-dir captures/new-capture
python -B -m vg.tools.player_state_capture verify --capture-dir captures/new-capture --require-restored --output verify.json
python -B -m vg.tools.player_state_capture challenge --capture-dir captures/new-capture --mutation foreign-pid --output challenge.json
python -B -m vg.tools.player_state_capture align --capture-dir captures/new-capture --sample-sequence 42 --output-dir captures/new-capture-aligned
python -B -m vg.tools.player_state_capture export-reference --capture-dir captures/new-capture --manifest frozen-reference/manifest.json --output-dir reference-with-capture
```

All outputs must be new. Import freezes hashes of the actual source sections,
native JSONL, screenshots and action log; it creates `capture.json`,
`verification.json` and `freeze.json`. A failed import keeps its failure report
and exits 1. Missing/malformed inputs and collisions exit 2. A successful
`observation_only` report means evidence integrity passed, not state accuracy.
The challenge command changes only an in-memory receipt and requires an actual
valid baseline; missing screenshots, altered native hashes and foreign PIDs
must be rejected.

A capture specification contains:

```json
{
  "capture_id": "a1-c33-inventory",
  "recording_id": "C33",
  "partition": "development",
  "trial": "c33",
  "process": {"pid": 123, "create_time": 123.5, "exe": "D:/owned/Vainglory.exe", "sha256": "EXACT_BUILD_HASH"},
  "source_files": [{"section": 0, "path": "original.0.vgr", "sha256": "ORIGINAL_FILE_HASH"}],
  "native_artifact_id": "native",
  "alignment": {"kind": "unverified"},
  "artifacts": [
    {"artifact_id": "native", "role": "native", "path": "native.jsonl"},
    {"artifact_id": "actions", "role": "actions", "path": "commands.jsonl"},
    {"artifact_id": "screen", "role": "screenshot", "path": "board.png"}
  ]
}
```

Source hashes must come from the frozen recording inventory. Artifact hashes
may be supplied and checked, or filled from the original captured bytes on
import. Paths resolve relative to the specification. Native identity must match
the exact PID, creation time, executable path and supported hash. Screenshots
must be PNGs named in successful OS screenshot receipts for that owned PID.
Both successful observer completion and detach are required. A player-state
log containing only null sessions or zero actors fails with `no_observation`,
even if its observer exited without an exception. Inventory action traces are
retained as partial observations, never converted into whole-state truth.

For `--require-restored`, link the actual `slot_backup`, `slot_restored`,
`worker_cleanup`, `worker_exited` and `restored_inventory` artifacts, plus every
backup file with role `original_backup`. The verifier compares original backup
hashes and timestamps to the later readback of that exact trial. It requires
the captured game PID, its observer/worker and task to be absent. A new unrelated
owned run may exist; the readback certifies the original capture's cleanup at
its recorded time, not perpetual absence of all future games.

## Alignment and independent export

Export requires successful restoration and a proven native boundary. The `align`
command supports version 2's passive native reader snapshots at EOF. It
requires unchanged reader state across the player reads, either a native pause
flag or an exhausted reader (final section plus one, file handle closed),
the post-dispatch `needs_record` state, native slot-name/injection correspondence,
and an exact unique match of native buffered content and timestamp to the final
record in the original final section. It reads only original record framing;
no counter/inventory decoder supplies expected values or boundary corrections.
A new aligned receipt is written without editing the original frozen capture.

A separate manual claim such as “the game was paused” cannot promote a sample. A hashed
`native_boundary` artifact must match exactly one `player_state_boundary` event
in the original native JSONL, including PID/creation identity, sample sequence,
ordered loaded source hashes, applied section/record offset, `phase: after_apply`
and raw game-clock bits. `recorded_end_paused` additionally requires native
paused and recorded-end flags. An exact timed boundary additionally requires the
sample itself to carry `atomic_record_boundary: true` and that boundary.

The passive pool sampler reports `atomic_record_boundary: false`; it never
pretends its asynchronous memory reads are a hook inside the dispatch loop.
Version 2 includes the native reader buffer before and after those reads.
EOF can be certified through the above independent byte match. The exhausted
reader case records the actual pause state as false; a running playback timer
does not create another source record after the final applied buffer.
Version 1 and interior samples remain observation-only. Timed native
reader alignment is explicitly unsupported by `align` at this stage.

Export creates a new frozen reference registry and preserves the original
development/holdout split. It copies native names, actor links, KDA, exact gold
bits, displayed CS (native resource14) and all native inventory multiplicities
under `native_items`. HUD `items` stay unobserved until independently verified
original Item names establish the native visibility predicate. The
compatibility name `minion_kills` denotes scoreboard CS; it does not claim a
lane-only count or a proved creature taxonomy. Hero labels stay unobserved until
separately evidenced original assets establish them. A partial export cannot
satisfy the strict six-field comparator.

## Windows passive runner

```sh
python -B -m vg.tools.player_state_capture capture --profile owned-profile.json --spec capture-spec.json --seconds 3 --output-dir capture-new
python -B -m vg.tools.player_state_capture restore --profile owned-profile.json --trial c33 --output restored-readback.json
```

The only implemented profile is `winsrv-owned-20261004`. Its JSON contains
`profile`, exact existing `remote_root`, `process` with the four identity fields
above, and `worker` with its independently recorded PID and creation time.
The runner pins the actual a1 `probe.py`, `control.py`, `interactive.py`, WTS
session helpers and restore script by SHA256. It uses the fixed LAA executable
and dependency paths already present in those scripts. Changed scripts fail
closed; an arbitrary command string is never accepted.

Before sampling it queries fresh WTS state, checks the one live game's file hash
and PID creation identity, checks its parent worker and the worker's own status,
and compares the installed JS probe to the packaged version. It takes a real
OS screenshot through that worker, invokes its bounded passive probe, captures
the action transcript and rechecks source hashes. Injection and game navigation
remain explicit root OS actions. The capture output initially remains unaligned.
The restore command requires all game processes to be stopped, verifies the
original backup and absent archive, invokes only the frozen restore script, then
reads back each restored file hash. It does not terminate a game to make this
precondition pass.

## Recorded validation

The real a1 C33 inventory import verifies 7 source sections, 69 native action
rows plus the ready event, the OS screenshot/action linkage and the restored
13-file original slot with exact hashes/timestamps and process cleanup. It is
observation-only because it lacks a native applied-record boundary.
The separate failed C33 state attempt is rejected as `no_observation` despite
normal observer completion. Private artifact locations and exact invocations
are recorded in the executor receipt; unit-test fixtures are not native truth.
