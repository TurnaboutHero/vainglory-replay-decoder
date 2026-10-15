"""Synthetic boundary models only. No gameplay or wire acceptance."""
def teleport_gate(actor_exists, state_code, bypass=False):
    return bool(actor_exists and (bypass or state_code not in (3,4)))
def timer_write(existing, value, mode_byte):
    if mode_byte != 0:return existing
    return {'remaining': value, 'aux': existing['aux'] if existing is not None else 0}
def recall_slot(slots, selected):
    return next((i for i,v in enumerate(slots) if v == selected), 0xffffffff)
def state_edge(current_index, target_index, allowed_mask):
    return current_index == 31 or (current_index != target_index and bool(allowed_mask & (1 << target_index)))
