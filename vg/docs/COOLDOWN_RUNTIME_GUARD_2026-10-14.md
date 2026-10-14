# Cooldown runtime attempt: foreground guard refusal

Code baseline `33611314a29d2ad57a4c56a2f6da569b22ec9641`, branch
`codex/rea-item-activation`. The separate cooldown parser/static evidence at
`311232a1deaa60835068a1939eaf1ec023e21ac0` was read, not merged or reimplemented.
This increment adds a blocked-attempt receipt, not decoded state or runtime
validation of cooldown behavior.

## Fresh preflight and first access

After the runtime coordinator handed Windows ownership to this session, fresh
checks found no existing game/QA workers, no VG scheduled tasks, and an unlocked
WTS session. Both reference executable hashes matched. Before launch, 661 files
under the actual replay temporary directories were backed up with original
content SHA-256 and exact Windows creation/write FILETIMEs. The backup was new
and byte-checked.

The unchanged interactive worker ran in the logged-in session as PID 30544.
It launched a new owned LAA game, PID 69176; executable path/hash, process
creation identity and worker-parent lineage were independently recorded.
The LAA hash was
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.

One normal focus operation was attempted before the first screenshot. The
guarded screenshot at **2026-10-14 13:29:31.882330–13:29:31.998209 UTC** refused:

```text
desktop: Default
foreground_name: OP.GG.exe
owned_game_pid: 69176
error: Owned game not foreground on Default desktop; refused
```

This refusal concerns the actual foreground window, not the earlier LockApp
case. An unlocked Default desktop does not prove that the owned game is
foreground. No game screenshot was captured. Per the operator's stop condition,
there were no focus/screenshot/input retries after this refusal, no gameplay
click/key commands, no observer attachment, no replay substitution and no
cooldown hypothesis trials. The existing OP.GG process was left alone.

## Cleanup and original preservation

Only the newly owned game and worker were stopped. The sender's exit-worker
acknowledgement timed out because that existing worker branch does not include
`end_utc`; its exit receipt and independent process-identity checks established
that the worker was absent. This timeout was not counted as cleanup success
without those checks.

Restoration independently checked all **661 original files**: exact file list,
content SHA-256, creation FILETIME and last-write FILETIME matched the fresh
backup. No file content needed recreation/repair and no new replay family needed
archival. Pending command was absent. The single owned scheduled task was
identified by its exact script action and removed. Both executable hashes were
unchanged. The final cleanup receipt is dated 13:33:55.973596 UTC.

[The path-free blocked receipt](evidence/2026-10-14-cooldown-runtime-guard/blocked.json)
retains these counts, the refusal, ownership metadata and hashes of private
command/identity/worker-exit/task-cleanup receipts. Raw backups, replay files,
process traces and binaries are not included.

## Remaining evidence and next input

All three shoe cases remain **NOT_RUN**: same-definition distinct instances
sharing a state, preservation across sale/rebuy, and independence of different
tiers. Fountain definition 487/key `0x6f056481` remains a separate static
positive control; it does not identify shoe keys or establish live countdowns.
Exact remaining seconds remain unavailable without timer identity/handle,
charges/pause, apply/queue/tick and playback-frame observations. Event timestamp
subtraction is not a substitute.

A conservative collector extension was prepared outside the product tree and
passed 35 offline Node-VM/syntax checks. It was never loaded into the game;
mock pointer checks are not runtime validation of offsets, lifetimes or native
handle validity. No collector or reducer is promoted by this documentation.

To resume, the operator must provide a new resume instruction and keep the
actual owned Vainglory window foreground for fresh guarded capture. If OP.GG or
another application takes foreground, resolve that on the operator side; do
not weaken the guard, terminate unrelated processes, or bypass the desktop.
Windows retries are currently withheld. No merge, main push or deployment was
performed.
