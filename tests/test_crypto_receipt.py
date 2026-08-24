"""
Unit tests for Cryptographic Audit Trail & Offline Verification
"""

import unittest
from handlers.crypto_receipt import mint_signed_receipt, verify_receipt, compute_dag_state_root


class TestCryptoReceipt(unittest.TestCase):

    def test_mint_and_verify_valid_receipt(self):
        lead_data = {
            "email": "sarah@cyberdyne.io",
            "company": "Cyberdyne Systems",
            "domain": "cyberdyne.io",
            "tier": "Enterprise",
            "lead_score": 95,
            "assigned_ae": "Taylor Vance",
        }
        mutations = {
            "hubspot_deal": "created",
            "slack_alert": "posted",
            "airtable_log": "logged",
        }

        receipt = mint_signed_receipt(
            workflow_slug="leultew/lead-governance-airlock",
            version="1.0.0",
            lead_data=lead_data,
            mutations=mutations,
        )

        self.assertEqual(receipt["status"], "SUCCESS")
        self.assertIn("state_root_sha256", receipt)
        self.assertEqual(receipt["signature_algorithm"], "Ed25519")

        is_valid, msg = verify_receipt(receipt)
        self.assertTrue(is_valid)
        self.assertIn("Receipt verified", msg)

    def test_tampered_receipt_fails_verification(self):
        lead_data = {"email": "alex@initech.com", "company": "Initech"}
        mutations = {"hubspot_deal": "created"}

        receipt = mint_signed_receipt(
            workflow_slug="leultew/lead-governance-airlock",
            version="1.0.0",
            lead_data=lead_data,
            mutations=mutations,
        )

        # Tamper with lead data after signing
        receipt["lead"]["company"] = "Hacked Corporation"

        is_valid, msg = verify_receipt(receipt)
        self.assertFalse(is_valid)
        self.assertIn("State root mismatch", msg)

    def test_budget_breach_in_receipt_fails_verification(self):
        lead_data = {"email": "alex@initech.com"}
        mutations = {}

        receipt = mint_signed_receipt(
            workflow_slug="leultew/lead-governance-airlock",
            version="1.0.0",
            lead_data=lead_data,
            mutations=mutations,
            spend_cents=600,
            max_spend_cents=500,
        )

        is_valid, msg = verify_receipt(receipt)
        self.assertFalse(is_valid)
        self.assertIn("exceeds max_spend_cents cap", msg)


if __name__ == "__main__":
    unittest.main()
