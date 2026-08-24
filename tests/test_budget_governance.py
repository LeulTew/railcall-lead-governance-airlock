"""
Unit tests for Budget Governance & Spend Ceiling Enforcement
"""

import unittest
from handlers.budget import BudgetLedger


class TestBudgetGovernance(unittest.TestCase):

    def test_ledger_records_costs_within_ceiling(self):
        ledger = BudgetLedger(max_spend_cents=500)
        
        ok1, _ = ledger.record_node_cost("enrich_and_score", 15, "Enrichment API call")
        self.assertTrue(ok1)

        ok2, _ = ledger.record_node_cost("hubspot_deal", 0, "CRM deal creation")
        self.assertTrue(ok2)

        summary = ledger.get_summary()
        self.assertEqual(summary["current_spend_cents"], 15)
        self.assertEqual(summary["remaining_cents"], 485)

    def test_ledger_intercepts_cost_overrun(self):
        ledger = BudgetLedger(max_spend_cents=100)
        
        # Spend 80 cents
        ledger.record_node_cost("step_1", 80)

        # Attempt to spend 30 cents (total 110 cents > 100 max)
        ok, msg = ledger.record_node_cost("step_2", 30)
        self.assertFalse(ok)
        self.assertIn("Budget breached", msg)


if __name__ == "__main__":
    unittest.main()
