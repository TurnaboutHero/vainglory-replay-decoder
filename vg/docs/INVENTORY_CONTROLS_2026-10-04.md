# Inventory consumer controls, 2026-10-04

The [25-control evidence package](evidence/2026-10-04-opcode-controls/inventory/controls.json) records 22 safe inventory operations and three separately staged SET operations against C03 actor 1509. Each control links its exact source section, timestamp bits and content bytes to constructor arguments, copied queue action, apply action and native inventory before/after state. The controls are synthetic: they establish consumer behavior for these inputs, not gameplay emission or complete replay inventory recovery. The `043d`, `0444` and `044b` atlas gates are verified for the bounded consumer controls described below, following independent review and runtime-owner acceptance.

| Observed scenario | Controls | Native result |
| --- | ---: | --- |
| Remove original five items | 5 | Live pointers move to deferred storage; occupied count decreases |
| Grant distinct Flare instances A/B | 2 | Separate pointers occupy first vacant slots, each quantity 1 |
| Sentinel grant with two eligible Flare stacks | 1 | First nonfull stack A gains one; B unchanged |
| Consume Flare A twice and B once | 3 | A quantity 2 -> 1 retains its pointer; next consume removes it; B also moves to deferred storage |
| Eight blade grants and ninth capacity attempt | 9 | Eight new instances fill capacity; ninth leaves inventory unchanged |
| Missing consume instance and missing SET actor | 2 | No captured state change |
| SET 65538 on original instance 2000 | 1 | Low 16 bits yield quantity 2 with the original pointer retained |
| SET 65536 on original instance 2001 | 1 | Quantity becomes 0 while the pointer remains live and occupied count stays 5 |
| Consume that zero-quantity original instance | 1 | Same pointer enters deferred slot 0, quantity 0, item flag 1; occupied count becomes 4 |

All 25 transitions preserve the captured noninventory primary-player fields, including six native statistics, and the captured other-player state. Sampled clock/roster globals are unchanged. Full native inventory states are continuous between adjacent synthetic controls within each run. Dirty bits were already set throughout; these captures do not prove a clean-to-dirty transition. Deferred insertion does not prove eventual destruction, and native slot order does not establish HUD order. No resolved-actor missing-instance SET behavior is claimed.

For `043d`, the accepted boundaries are distinct same-definition instances, sentinel selection of the first of two nonfull stacks, eight occupied slots with rejection of a ninth grant, and first-vacancy native array order. The initial five-item inventory and its per-action removals are captured in this package. The separately reviewed [original replay controls](OPCODE_CONTROLS_2026-10-04.md) provide the fresh/existing `03f3` baseline evidence cited by this gate. For `0444`, the accepted controls are instance lookup with the original pointer retained across `65538 -> 2` and `65536 -> 0`, plus the separate missing-actor no-op.

For `044b`, the original required experiment is preserved verbatim in the atlas: “C33three14-byte consumes are matched. Need stack decrement/removal, quantity rejection guards, and an independently aligned allsixfields snapshot.” The runtime owner clarified that “quantity rejection guards” expressed the hypothesis that zero quantity would reject consumption. That hypothesis is **refuted**: zero quantity removes the live pointer into deferred storage without underflow. Together with `2 -> 1` pointer retention, `1 -> 0` removal and missing-instance no-op, this resolves the sampled quantity-boundary inquiry by falsification. No quantity-rejection branch was observed or proved. This acceptance interpretation does not establish universal guard coverage, alternate flag behavior, natural producer rejection or eventual destruction. The six-field comparisons use the captured native snapshots; atomic rendered acceptance remains outside the claim.

Run from repository root using Python 3 (standard library only):

```sh
python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/audit.py
python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/test_audit.py
```

The audit recomputes wire argument decoding, action fingerprints and queue/apply identity, native transition rules, pointer occupancy, within-run continuity and captured-field stability. Each actor resolution must match the current dispatch, heap action, opcode-specific handler and sampled actor identity. New allocation pointers are observed rather than predicted. The package stores full primary inventory snapshots, other primary fields, selected native chain observations and other-player snapshot hashes. It does not need the private workspace. Twelve tests verify valid data and reject quantity, queue pointer, other-player hash, premature zero-quantity removal and resolution provenance corruption, including substitution of another control's resolution.

For access to the original private capture/source files, add their outer workspace root:

```sh
python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/audit.py --workspace /path/to/vg-workspace
```

This mode checks the raw capture hashes, source-manifest hashes, all 81 section hashes per fixture, exact injected frame offsets, original modified-section reconstruction after removing injected records, selected native observations and primary/other-player snapshots. Package fields include workspace-relative paths and exact raw capture line numbers.

| Run | Capture SHA256 | Manifest SHA256 |
| --- | --- | --- |
| safe22 | `90b638b5f74c529a036a14f5086dfcfdf1634e6dcb3e79b44b3147fc86b0baa8` | `975592d440fba1d5376ebfcbdcf3415c1920ea814642e7e479bed383b935052c` |
| set3 | `1e1f8e367f878475581fc1e1ce2795ee08f7a8dfcfa99ee94bfd62a798f0dccd` | `18e392268071cd7e0606ef1aa384d1ae7e0345a2753afede110e04931838219d` |

Both captures finish their observation interval with no pending tracked actions. This is not evidence of continued process liveness afterward. Process lifecycle and slot restoration are separate runtime-owner evidence. Rule branches present in the auditor but absent from the scenario table are not established by these controls. See the [broader opcode controls](OPCODE_CONTROLS_2026-10-04.md) for other families and evidence boundaries.
