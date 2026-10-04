# Validation receipt

Executed from repository root on 2026-10-04. Both audit commands exited 0.

```text
$ python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/audit.py
{"ok": true, "controls": 25, "runs": {"safe22": 22, "set3": 3}, "external_files_rechecked": false, "source_native_emit_verified": false}

$ python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/audit.py --workspace /Users/gimhunhui/Documents/Codex/2026-10-02/vg
{"ok": true, "controls": 25, "runs": {"safe22": 22, "set3": 3}, "external_files_rechecked": true, "source_native_emit_verified": false}

$ python3 -B vg/docs/evidence/2026-10-04-opcode-controls/inventory/test_audit.py -v
test_complete_package (__main__.InventoryAuditTests) ... ok
test_consistent_wrong_opcode_handler_rejected (__main__.InventoryAuditTests) ... ok
test_missing_actor_nonzero_pointer_rejected (__main__.InventoryAuditTests) ... ok
test_other_player_side_effect_rejected (__main__.InventoryAuditTests) ... ok
test_quantity_corruption_rejected (__main__.InventoryAuditTests) ... ok
test_queue_pointer_corruption_rejected (__main__.InventoryAuditTests) ... ok
test_resolution_action_pointer_mismatch_rejected (__main__.InventoryAuditTests) ... ok
test_resolution_dispatch_mismatch_rejected (__main__.InventoryAuditTests) ... ok
test_resolution_from_another_control_rejected (__main__.InventoryAuditTests) ... ok
test_resolution_handler_mismatch_rejected (__main__.InventoryAuditTests) ... ok
test_resolved_actor_pointer_mismatch_rejected (__main__.InventoryAuditTests) ... ok
test_zero_pointer_retention_corruption_rejected (__main__.InventoryAuditTests) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.040s

OK
```

Observed package hashes:

```text
audit.py 13148 86f36129514466d1d838b2aeb09b173522f78d83ce2db88cf9e45d0997e30742
controls.json 553944 e54d1f3029b150eb359163d465ca6354d53ec09d7bd9a709504c839b25967416
test_audit.py 3386 f4dc6659ceb298a39f69d1772d302564c5d4d2204f6524370be28dee9d418866
documentation_exists True
```

Scenario-to-artifact mapping: the 25 cases in `controls.json` are replayed by `audit.py`; output `ok: true` requires decoded wire arguments, constructor/queue/apply identity, native inventory rules and captured-field continuity to agree. External mode additionally requires source and capture hashes and extracted observations to agree. Twelve tests in `test_audit.py` include eleven intentional evidence corruptions, each required to raise an assertion. Seven resolution negatives were observed failing before the binding fix; all twelve tests pass after it. Resolution checks bind dispatch, heap action, opcode-specific handler and sampled actor identity, including a null pointer for a missing actor.

The atlas now records bounded verified consumer gates for `043d`, `0444` and `044b`. The original `044b` experiment wording is preserved there alongside the explicit acceptance interpretation: zero-rejection was a hypothesis, refuted by zero-quantity removal without underflow. This resolves the sampled quantity boundary without claiming a quantity-rejection branch or universal guards. Native emission remains unverified; captured native statistics do not certify atomic rendered six-field accuracy. See [the inventory report](../../../INVENTORY_CONTROLS_2026-10-04.md) for the accepted scenarios and limits.
