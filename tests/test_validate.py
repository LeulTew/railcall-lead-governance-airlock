"""
Unit tests for Lead Validation & Sanitization Handler
"""

import unittest
from handlers.validate import validate_lead, sanitize_string, extract_domain


class TestValidateLead(unittest.TestCase):

    def test_valid_corporate_lead(self):
        payload = {
            "email": "sarah.connor@cyberdyne.io",
            "name": "Sarah Connor",
            "company": "Cyberdyne Systems",
            "title": "Director of Security",
            "message": "We need 500 enterprise seats for our automated defense platform.",
            "phone": "+1-555-0199",
        }
        res = validate_lead(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "validated")
        data = res["data"]
        self.assertEqual(data["email"], "sarah.connor@cyberdyne.io")
        self.assertEqual(data["company"], "Cyberdyne Systems")
        self.assertEqual(data["domain"], "cyberdyne.io")
        self.assertTrue(data["is_corporate_domain"])

    def test_missing_required_email(self):
        payload = {"name": "Anonymous", "company": "Acme Corp"}
        res = validate_lead(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["action"], "rejected")
        self.assertIn("required", res["error"])

    def test_malformed_email_syntax(self):
        payload = {"email": "not-an-email", "name": "Tester"}
        res = validate_lead(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["action"], "rejected")
        self.assertIn("valid RFC-compliant 'email'", res["error"])

    def test_disposable_domain_rejection(self):
        payload = {"email": "spammer@mailinator.com", "name": "Spam User"}
        res = validate_lead(payload)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["action"], "rejected")
        self.assertIn("Disposable email domain", res["error"])

    def test_string_sanitization_strips_control_characters(self):
        dirty_name = "Alex\x00\x1f Johnson\x7f"
        clean_name = sanitize_string(dirty_name)
        self.assertEqual(clean_name, "Alex Johnson")

    def test_derived_company_from_domain(self):
        payload = {"email": "contact@stripe.com"}
        res = validate_lead(payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["company"], "Stripe")


if __name__ == "__main__":
    unittest.main()
