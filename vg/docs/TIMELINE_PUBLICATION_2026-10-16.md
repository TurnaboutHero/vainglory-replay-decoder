# Timeline report publication

Baseline: `6fa72116bcf34a8d23a7c355b2973b443b034638`.

Previously, `event_timeline --output` opened the destination with `w` before
traversing the records. A malformed later section or JSON/write error could
therefore erase a previous report or leave partial JSONL.

The file-output path now freezes the destination's absence or regular-file
identity and its parent identity before input discovery/catalog loading. It
streams JSONL into an owned temporary file in the resolved destination directory,
flushes and fsyncs the complete result, then rechecks input identities, replay
siblings, output aliases and the destination before publication. Existing files
are replaced with `os.replace`; an initially absent destination uses exclusive
`os.link` creation so a last-moment arrival cannot be overwritten. A filesystem
without the required hard-link support reports an error rather than falling back
to an unsafe overwrite. No report rows are accumulated in memory.

Observed destination overwrite, creation, deletion, same-byte inode replacement,
link substitution or parent replacement raises `publication_conflict` and CLI
exit2. External bytes are preserved; the publisher does not restore an old backup
over them. Input changes raise `input_changed`. Path, permission, serialization,
write, flush, fsync and rename errors also return2 without truncating the previous
report. Input/sibling/catalog alias protections remain in force. Output symlinks
and non-regular destinations are rejected.

`stdout` remains a direct JSONL stream with the same row serialization; a late
error may leave already emitted stdout rows, as before. It does not use staging.

## Relation to existing report storage

The implementation reuses `ReportInputs`, `file_identity` and
`validate_report_outputs`. It follows the existing report-set publisher's
stage/fsync/recheck/replace pattern and recovery's rule of preserving foreign
bytes. It does not reuse the transaction's destination digest captured after
staging: for a long streaming decode that would miss changes during parsing.
The timeline freezes it earlier and also checks inode and modification metadata.
A single-file JSONL publication needs no multi-output receipt or backup generation.
The existing report-set APIs are unchanged.

Existing-target conflict detection is optimistic: there is a small check-to-rename
window, just as in the existing publisher. It is not an OS-level compare-and-swap
or a lock on non-cooperating external writers. The absent-target hard-link path
does provide exclusive creation. Do not describe this implementation as universal
concurrent-writer exclusion.

Normally, failed/successful publication removes the owned temporary. Cleanup checks
both parent and temporary inode/device before deletion. If another process moves
the parent directory, it deliberately leaves the owned stage in the moved folder
instead of deleting an unrelated file at a reused pathname. Such a conflict may
therefore leave `.report-name.<random>.tmp` in that moved folder for manual cleanup.
Neither the previous report nor a foreign stage in the replacement directory is
deleted. Forced process termination/power-loss recovery is not added here.

## Verification

```text
python -m unittest tests.test_event_timeline_publication -v
Ran 14 tests — OK
```

The new tests cover complete streaming replacement/creation, late malformed input
with an existing/absent report, mid-stream JSON/encoding/write failures,
flush/fsync/replace permission failures, output path errors, source mutation/new
siblings, overwrite/create/delete/same-byte replacement conflicts, exclusive
creation races, parent replacement and conservative cleanup, early destination
capture, and stdout behavior. Permission failures are deterministic injected
errors; successful file publication also runs on the real local filesystem.

Only this report-loss fix is in scope. No additional reverse-engineering, game
execution, server access, publication or merge is performed.

Additional regression/review: modules `test_event_timeline_publication`,
`test_event_timeline`, `test_timeline_identity`, `test_item_event_timeline`,
`test_item_activation_timeline`, and `test_impact_event_timeline`: 59 discovered,
58 executed and passed, zero failures/errors/skips. The single explicit exclusion
is `tests.test_event_timeline.EventTimelineTests.test_cli_rejects_discoverable_outputs_through_symlink_paths`
(the existing Windows symlink privilege limitation). No pass is claimed for that
case. The 14 new tests are included in these 58, not additive. Independent code
review found no remaining blocker within the documented optimistic contract.
The baseline Linux 1,205-test result reported by the parent is not reused as
validation of this change. Compilation and staged whitespace checks passed.

## Dot-side publication hardening

Independent Linux review reproduced two gaps in the first fix: a replaced stage
pathname could be published as if it were the owned temporary, and a destination
changed during the final full-input hashing pass could be overwritten because the
destination check preceded that pass.

The final input/alias validation now runs before the final destination check.
The publisher then verifies that the stage is still the same regular-file inode
and has the size/modification/change metadata captured from the flushed, fsynced
open descriptor. A substituted or subsequently modified stage raises
`publication_conflict` before publication. Failure cleanup preserves a foreign
replacement stage or a detected same-inode external edit; a successfully linked
owned stage is still removed normally. Parent replacement continues to preserve
both the original report in the moved directory and foreign paths in its
replacement. A deliberately preserved stage may need manual inspection/cleanup.

Four additional tests cover replacement stages for existing/absent destinations,
destination changes during the final input check, same-inode stage modification
after fsync, and parent replacement during that check. All 18 publication tests
pass on Linux. These checks narrow the optimistic check-to-publish interval;
they do not add an OS-level compare-and-swap or eliminate the final syscall race.
