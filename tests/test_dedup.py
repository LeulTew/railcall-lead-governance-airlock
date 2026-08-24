"""
Unit tests for Deduplication & State Hashing Handler
"""

import unittest
from handlers.dedup import check_existing_lead, compute_idempotency_key, clear_dedup_cache


class TestDedupLead(unittest.TestCase):

    def setUp(self):
        clear_dedup_cache()

    def test_unique_lead_passes_dedup(self):
        payload = {
            "data": {
                "email": "elena.rostova@datadog.com",
                "company": "Datadog",
            }
        }
        res = check_existing_lead(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "passed")
        self.assertFalse(res["is_duplicate"])
        self.assertIn("idempotency_key", res["receipt_meta"])

    def test_duplicate_lead_within_window_is_skipped(self):
        payload = {
            "data": {
                "email": "elena.rostova@datadog.com",
                "company": "Datadog",
            }
        }
        # First call passes
        res1 = check_existing_lead(payload)
        self.assertEqual(res1["action"], "passed")

        # Immediate second call is detected as duplicate
        res2 = check_existing_lead(payload)
        self.assertEqual(res2["status"], "ok")
        self.assertEqual(res2["action"], "duplicate_skipped")
        self.assertTrue(res2["is_duplicate"])
        self.assertIn("Deduplication notice", res2["summary"])

    def test_deterministic_hashing(self):
        key1 = compute_idempotency_key("User@domain.COM ", "ACME Corp ")
        key2 = compute_idempotency_key("user@domain.com", "acme corp")
        self.assertEqual(key1, key2)


if __name__ == "__main__":
    unittest.main()
