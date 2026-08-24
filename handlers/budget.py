"""
Budget Governance & Spend Ceiling Enforcement
Implements Sub-issues 11.1, 11.2, 11.3, 11.4 (Epic 11)
"""

import time
from typing import Any, Dict, Optional, Tuple


class BudgetLedger:
    """Tracks and bounds execution costs in cents per workflow run."""

    def __init__(self, max_spend_cents: int = 500):
        self.max_spend_cents = max_spend_cents
        self.current_spend_cents = 0
        self.ledger_entries = []

    def record_node_cost(self, node_id: str, cost_cents: int, description: str = "") -> Tuple[bool, str]:
        """
        Records cost for a node execution. Rejects and halts if budget cap is breached.
        """
        projected = self.current_spend_cents + cost_cents
        if projected > self.max_spend_cents:
            return False, f"Budget breached: Node '{node_id}' projected cost {projected}c exceeds max_spend_cents {self.max_spend_cents}c."

        self.current_spend_cents = projected
        self.ledger_entries.append({
            "node_id": node_id,
            "cost_cents": cost_cents,
            "description": description,
            "timestamp": time.time(),
        })
        return True, f"Cost {cost_cents}c recorded for '{node_id}'. Total spend: {self.current_spend_cents}c/{self.max_spend_cents}c."

    def get_summary(self) -> Dict[str, Any]:
        return {
            "current_spend_cents": self.current_spend_cents,
            "max_spend_cents": self.max_spend_cents,
            "remaining_cents": self.max_spend_cents - self.current_spend_cents,
            "entries_count": len(self.ledger_entries),
        }
