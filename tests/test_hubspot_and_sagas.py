"""
Unit & Resilience tests for HubSpot Handler & Saga Rollback
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from handlers.hubspot import create_deal, archive_deal, _make_resilient_request
import urllib.error


class TestHubSpotAndSagas(unittest.TestCase):

    def test_dry_run_preview_generation(self):
        lead_data = {
            "email": "marcus@initech.com",
            "name": "Marcus Wright",
            "company": "Initech",
            "deal_name": "Initech - Enterprise Inbound",
            "pipeline_stage": "qualifiedtobuy",
            "estimated_deal_value": 25000,
            "lead_score": 90,
            "assigned_ae": "Taylor Vance (Enterprise AE)",
        }
        res = create_deal({"data": lead_data, "dry_run": True})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "dry_run_preview")
        self.assertIn("preview_diff", res)
        diff = res["preview_diff"]
        self.assertEqual(diff["object"], "deal")
        self.assertEqual(diff["properties"]["dealname"], "Initech - Enterprise Inbound")
        self.assertEqual(diff["properties"]["amount"], "25000")
        self.assertTrue(res["receipt_meta"]["dry_run"])

    def test_missing_access_token_fails_live_run_gracefully(self):
        lead_data = {"email": "marcus@initech.com", "company": "Initech"}
        with patch.dict(os.environ, {}, clear=True):
            res = create_deal({"data": lead_data, "dry_run": False})
            self.assertEqual(res["status"], "error")
            self.assertEqual(res["action"], "failed")
            self.assertIn("HUBSPOT_ACCESS_TOKEN", res["error"])

    def test_saga_rollback_dry_run_skipped(self):
        res = archive_deal({"data": {"deal_id": "dry_run_deal_preview_id"}, "dry_run": True})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "rollback_skipped")

    @patch("handlers.hubspot._make_resilient_request")
    def test_live_deal_creation_success(self, mock_req):
        # Mock contact creation then deal creation
        mock_req.side_effect = [
            (201, {"id": "contact_123"}),
            (201, {"id": "deal_456"}),
        ]
        with patch.dict(os.environ, {"HUBSPOT_ACCESS_TOKEN": "test_token"}):
            lead_data = {
                "email": "marcus@initech.com",
                "name": "Marcus Wright",
                "company": "Initech",
                "deal_name": "Initech - Enterprise Deal",
                "pipeline_stage": "qualifiedtobuy",
                "estimated_deal_value": 25000,
            }
            res = create_deal({"data": lead_data, "dry_run": False})
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["action"], "created")
            self.assertEqual(res["data"]["deal_id"], "deal_456")
            self.assertEqual(res["data"]["contact_id"], "contact_123")

    @patch("handlers.hubspot._make_resilient_request")
    def test_saga_rollback_live_success(self, mock_req):
        mock_req.return_value = (204, {})
        with patch.dict(os.environ, {"HUBSPOT_ACCESS_TOKEN": "test_token"}):
            res = archive_deal({"data": {"deal_id": "deal_456"}, "dry_run": False})
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["action"], "rolled_back")
            self.assertIn("Archived HubSpot deal #deal_456", res["summary"])

    @patch("urllib.request.urlopen")
    def test_resilient_backoff_on_429(self, mock_urlopen):
        # First call raises 429, second call succeeds
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        err_fp = MagicMock()
        err_fp.read.return_value = b'{"error": "rate_limit"}'

        err_429 = urllib.error.HTTPError(
            url="https://api.hubapi.com",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "0"},
            fp=err_fp,
        )
        mock_urlopen.side_effect = [err_429, mock_resp]

        status, body = _make_resilient_request("https://api.hubapi.com", max_retries=2, base_backoff=0.01)
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
