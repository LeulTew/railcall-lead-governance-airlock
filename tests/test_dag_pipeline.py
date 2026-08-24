"""
End-to-End DAG Simulation & Pipeline Integration Tests
"""

import unittest
from unittest.mock import patch
from handlers.validate import validate_lead
from handlers.dedup import check_existing_lead, clear_dedup_cache
from handlers.enrich import score_lead
from handlers.hubspot import create_deal, archive_deal
from handlers.slack import post_lead_alert
from handlers.airtable import log_event


class TestDAGPipeline(unittest.TestCase):

    def setUp(self):
        clear_dedup_cache()

    def test_full_dag_happy_path_dry_run(self):
        trigger_payload = {
            "email": "cto@acmecorp.com",
            "name": "Sarah Connor",
            "company": "Acme Corp",
            "title": "Chief Technology Officer",
            "message": "Looking for pricing for 100 enterprise developer licenses.",
        }

        # Step 1: Validate
        val_res = validate_lead(trigger_payload)
        self.assertEqual(val_res["status"], "ok")

        # Step 2: Dedup Check
        dedup_res = check_existing_lead(val_res)
        self.assertEqual(dedup_res["status"], "ok")
        self.assertEqual(dedup_res["action"], "passed")

        # Step 3: Enrich & Score
        enrich_res = score_lead(dedup_res)
        self.assertEqual(enrich_res["status"], "ok")
        self.assertEqual(enrich_res["data"]["tier"], "Enterprise")
        self.assertGreaterEqual(enrich_res["data"]["lead_score"], 80)

        # Step 4: HubSpot Dry-run Preview
        hub_res = create_deal(enrich_res, context={"dry_run": True})
        self.assertEqual(hub_res["status"], "ok")
        self.assertEqual(hub_res["action"], "dry_run_preview")
        self.assertIn("preview_diff", hub_res)

        # Step 5: Slack Dry-run Preview
        slack_res = post_lead_alert(hub_res, context={"dry_run": True})
        self.assertEqual(slack_res["status"], "ok")
        self.assertEqual(slack_res["action"], "dry_run_preview")

        # Step 6: Airtable Dry-run Preview
        airtable_res = log_event(slack_res, context={"dry_run": True})
        self.assertEqual(airtable_res["status"], "ok")
        self.assertEqual(airtable_res["action"], "dry_run_preview")

    def test_dag_duplicate_lead_bypass_preserves_idempotency(self):
        trigger_payload = {
            "email": "lead@company.com",
            "company": "Company Inc",
        }

        # First run succeeds
        v1 = validate_lead(trigger_payload)
        d1 = check_existing_lead(v1)
        self.assertEqual(d1["action"], "passed")
        s1 = score_lead(d1)
        self.assertEqual(s1["action"], "scored")

        # Second immediate run is intercepted by dedup node
        v2 = validate_lead(trigger_payload)
        d2 = check_existing_lead(v2)
        self.assertEqual(d2["action"], "duplicate_skipped")

        # Downstream nodes safely bypass without mutations
        s2 = score_lead(d2)
        self.assertEqual(s2["action"], "duplicate_skipped")
        h2 = create_deal(s2)
        self.assertEqual(h2["action"], "duplicate_skipped")
        sl2 = post_lead_alert(h2)
        self.assertEqual(sl2["action"], "duplicate_skipped")

    def test_saga_rollback_on_downstream_exception(self):
        """
        Simulates an effect failure downstream that triggers the saga rollback on HubSpot.
        """
        # Assume HubSpot deal was created
        created_deal_state = {
            "data": {
                "deal_id": "deal_test_999",
                "email": "user@failtest.com",
                "company": "FailTest Corp",
            },
            "dry_run": False,
        }

        # Downstream failure occurs
        with patch("handlers.hubspot._make_resilient_request") as mock_req:
            mock_req.return_value = (204, {})
            with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "mock_token"}):
                rollback_res = archive_deal(created_deal_state)
                self.assertEqual(rollback_res["status"], "ok")
                self.assertEqual(rollback_res["action"], "rolled_back")
                self.assertEqual(rollback_res["data"]["archived_deal_id"], "deal_test_999")


if __name__ == "__main__":
    unittest.main()
