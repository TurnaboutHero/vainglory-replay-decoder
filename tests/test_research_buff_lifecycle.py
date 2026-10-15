"""Synthetic decisions from reviewed static branches, not a native buff emulator.

Caller eligibility, factory lookup, scripts, time units, and object lifetimes are
external preconditions. These tests never apply historical events to replay state.
"""
import unittest


def lifetime_dispatch(event):
    return {'create': 'behavior_apply', 'remove': 'behavior_inverse',
            'reapply': 'stub', 'stack_change': 'stub', 'expiry_callback': 'stub'}[event]


def timer_route(state, flags, remaining, mode_nonzero, predicate=True, elapsed=0):
    """Timer-only decision after the initial bit9 reactivation phase.

    Caller has already cleared bit4/reloaded duration when the initial native
    reactivation condition holds. Only ordinary finite time values are modeled.
    Predicate failure suppresses subtraction, not the subsequent expiry check.
    """
    if state == 2 or flags & (1 << 4):
        return 'no_countdown'
    if not flags & (1 << 12) or predicate:
        remaining -= elapsed
    if remaining > 0:
        return 'not_expired'
    if not flags & (1 << 7):
        return 'expiry_handler'
    return 'submit_command' if mode_nonzero else 'no_local_expiry_call'


def expiry_route(state, flags, remaining_after_callbacks, stacks, capacity,
                 remove_when_empty):
    """Bounded ordinary stack values; scripts already evaluated."""
    assert 0 <= stacks <= capacity <= 65535
    if state in (1, 2):
        return 'skip', stacks
    if remaining_after_callbacks > 0:
        return 'callback_extended', stacks
    if flags & (1 << 10):
        count = max(0, stacks - 1)
        return ('remove' if count == 0 and remove_when_empty else 'reload'), count
    if flags & (1 << 11):
        return ('remove' if remove_when_empty else 'set_bit4'), 0
    if flags & (1 << 9):
        count = min(capacity, stacks + 1)
        return ('reload' if count < capacity else 'set_bit4'), count
    return 'remove', 0


class BuffLifecycleModels(unittest.TestCase):
    def test_lifetime_apply_inverse_but_no_generic_update(self):
        self.assertEqual(lifetime_dispatch('create'), 'behavior_apply')
        self.assertEqual(lifetime_dispatch('remove'), 'behavior_inverse')
        for event in ('reapply', 'stack_change', 'expiry_callback'):
            self.assertEqual(lifetime_dispatch(event), 'stub')

    def test_timer_zero_does_not_imply_removal(self):
        self.assertEqual(timer_route(0, 1 << 7, 0, False), 'no_local_expiry_call')
        self.assertEqual(timer_route(0, 1 << 7, 0, True), 'submit_command')
        for mode in (False, True):
            self.assertEqual(timer_route(0, 0, 0, mode), 'expiry_handler')

    def test_countdown_state_flag_and_predicate_gates(self):
        self.assertEqual(timer_route(2, 0, -1, False), 'no_countdown')
        self.assertEqual(timer_route(0, 1 << 4, -1, False), 'no_countdown')
        self.assertEqual(timer_route(0, 1 << 12, 1, False, False, 2), 'not_expired')
        self.assertEqual(timer_route(0, 1 << 12, 0, False, False, 2), 'expiry_handler')
        self.assertEqual(timer_route(0, 1 << 12, 1, False, True, 2), 'expiry_handler')
        self.assertEqual(timer_route(0, 0, 1, False), 'not_expired')

    def test_callback_extension_and_state_guards(self):
        self.assertEqual(expiry_route(1, 0, 0, 1, 3, True), ('skip', 1))
        self.assertEqual(expiry_route(0, 0, 1, 1, 3, True), ('callback_extended', 1))

    def test_stack_decrement_removal_is_conditional(self):
        self.assertEqual(expiry_route(0, 1 << 10, 0, 2, 3, True), ('reload', 1))
        self.assertEqual(expiry_route(0, 1 << 10, 0, 1, 3, True), ('remove', 0))
        self.assertEqual(expiry_route(0, 1 << 10, 0, 1, 3, False), ('reload', 0))

    def test_zero_or_grow_stack_routes(self):
        self.assertEqual(expiry_route(0, 1 << 11, 0, 2, 3, False), ('set_bit4', 0))
        self.assertEqual(expiry_route(0, 1 << 11, 0, 2, 3, True), ('remove', 0))
        self.assertEqual(expiry_route(0, 1 << 9, 0, 1, 3, False), ('reload', 2))
        self.assertEqual(expiry_route(0, 1 << 9, 0, 2, 3, False), ('set_bit4', 3))

    def test_native_branch_priority(self):
        flags = (1 << 10) | (1 << 11) | (1 << 9)
        self.assertEqual(expiry_route(0, flags, 0, 2, 3, True), ('reload', 1))
        self.assertEqual(expiry_route(0, 0, 0, 2, 3, False), ('remove', 0))


if __name__ == '__main__':
    unittest.main()
