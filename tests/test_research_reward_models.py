"""Finite ordinary resource arithmetic, not reward eligibility or native execution."""
import unittest


def individual_gold(balance, positive_income, operand, add=True,
                    target_resolved=True, presentation_enabled=True):
    """Small integer examples only; no native float32/modifier/lifetime emulator.

    Presentation is intentionally separate. The required second target lookup
    has already been represented by target_resolved.
    """
    if not target_resolved:
        return balance, positive_income
    new_balance = max(0, balance + operand if add else operand)
    new_income = positive_income + operand if add and operand > 0 else positive_income
    return new_balance, new_income


class RewardModels(unittest.TestCase):
    def test_presentation_does_not_select_resource_recipient(self):
        self.assertEqual(individual_gold(10, 20, 5, presentation_enabled=False), (15, 25))
        self.assertEqual(individual_gold(10, 20, 5, presentation_enabled=True), (15, 25))

    def test_positive_add_increments_income_but_debit_does_not(self):
        self.assertEqual(individual_gold(10, 20, 5), (15, 25))
        self.assertEqual(individual_gold(10, 20, -50), (0, 20))

    def test_set_does_not_create_positive_income(self):
        self.assertEqual(individual_gold(10, 20, 50, add=False), (50, 20))
        self.assertEqual(individual_gold(10, 20, -50, add=False), (0, 20))

    def test_unresolved_target_cannot_mutate_resource(self):
        self.assertEqual(individual_gold(10, 20, 5, target_resolved=False), (10, 20))


if __name__ == '__main__':
    unittest.main()
