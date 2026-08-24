"""
Unit tests for Distributed Saga Rollback Orchestrator
"""

import unittest
from unittest.mock import patch
from handlers.saga import SagaExecutionLog


class TestSagaOrchestrator(unittest.TestCase):

    def test_saga_unwinds_in_reverse_order(self):
        saga = SagaExecutionLog()

        saga.record_step(
            node_id="create_hubspot_deal",
            action="created",
            output_data={"deal_id": "deal_9876", "company": "Test Corp"},
            rollback_handler="handlers.hubspot:archive_deal",
        )
        saga.record_step(
            node_id="notify_slack_ae",
            action="posted",
            output_data={"channel": "#sales"},
            rollback_handler=None,
        )

        with patch("handlers.saga.archive_deal") as mock_archive:
            mock_archive.return_value = {"status": "ok", "action": "rolled_back", "summary": "Archived deal"}
            
            report = saga.unwind_saga(
                failure_node_id="log_airtable",
                error_message="Airtable API connection timeout",
            )

            self.assertEqual(report["status"], "rolled_back")
            self.assertEqual(report["failure_trigger"]["node_id"], "log_airtable")
            self.assertEqual(len(report["unwind_receipts"]), 2)
            # First unwound is notify_slack_ae (reverse order)
            self.assertEqual(report["unwind_receipts"][0]["target_node"], "notify_slack_ae")
            # Second unwound is create_hubspot_deal
            self.assertEqual(report["unwind_receipts"][1]["target_node"], "create_hubspot_deal")
            mock_archive.assert_called_once()


if __name__ == "__main__":
    unittest.main()
