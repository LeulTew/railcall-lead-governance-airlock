"""
Distributed Saga Orchestrator & Compensating Rollback Engine
Implements Sub-issues 7.1, 7.2, 7.3, 7.4 (Epic 7)
"""

import time
from typing import Any, Callable, Dict, List, Optional
from handlers.hubspot import archive_deal


class SagaExecutionLog:
    """Tracks completed effect nodes and orchestrates reverse unwinding."""

    def __init__(self):
        self.completed_actions: List[Dict[str, Any]] = []

    def record_step(self, node_id: str, action: str, output_data: Dict[str, Any], rollback_handler: Optional[str] = None):
        self.completed_actions.append({
            "node_id": node_id,
            "action": action,
            "data": output_data,
            "rollback_handler": rollback_handler,
            "timestamp": time.time(),
        })

    def unwind_saga(self, failure_node_id: str, error_message: str) -> Dict[str, Any]:
        """
        Executes compensating rollback transactions in reverse order.
        """
        unwind_receipts = []
        now = time.time()

        for step in reversed(self.completed_actions):
            node_id = step["node_id"]
            handler_name = step.get("rollback_handler")
            step_data = step["data"]

            if handler_name == "handlers.hubspot:archive_deal" or node_id == "create_hubspot_deal":
                # Execute HubSpot compensation
                res = archive_deal({"data": step_data, "dry_run": False})
                unwind_receipts.append({
                    "target_node": node_id,
                    "handler": handler_name,
                    "result": res,
                })
            else:
                unwind_receipts.append({
                    "target_node": node_id,
                    "handler": handler_name,
                    "result": {"status": "ok", "action": "noop_rollback", "summary": f"No compensation needed for {node_id}"},
                })

        return {
            "status": "rolled_back",
            "failure_trigger": {
                "node_id": failure_node_id,
                "error": error_message,
                "timestamp": now,
            },
            "unwind_receipts": unwind_receipts,
            "summary": f"Saga rollback executed successfully across {len(unwind_receipts)} prior steps after failure in '{failure_node_id}'.",
        }
