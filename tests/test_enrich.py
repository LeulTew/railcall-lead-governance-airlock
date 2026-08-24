"""
Unit tests for Lead Enrichment & ICP Scoring Handler
"""

import unittest
from handlers.enrich import score_lead, calculate_lead_score, determine_tier_and_routing


class TestEnrichAndScore(unittest.TestCase):

    def test_enterprise_tier_lead(self):
        lead = {
            "email": "satya@microsoft.com",
            "name": "Satya Nadella",
            "company": "Microsoft",
            "domain": "microsoft.com",
            "title": "Chief Executive Officer",
            "message": "Interested in 5000 enterprise seats and custom security compliance contract.",
            "is_corporate_domain": True,
        }
        score, breakdown = calculate_lead_score(lead)
        self.assertGreaterEqual(score, 80)
        self.assertEqual(breakdown["domain_authority"], 30)
        self.assertEqual(breakdown["title_seniority"], 30)

        res = score_lead({"data": lead})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["tier"], "Enterprise")
        self.assertEqual(res["data"]["estimated_deal_value"], 25000)
        self.assertIn("Enterprise AE", res["data"]["assigned_ae"])

    def test_midmarket_tier_lead(self):
        lead = {
            "email": "dave@mediumbiz.co",
            "name": "Dave Miller",
            "company": "MediumBiz Co",
            "domain": "mediumbiz.co",
            "title": "Software Developer",
            "message": "Looking to evaluate tools for our team.",
            "is_corporate_domain": True,
        }
        res = score_lead({"data": lead})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["tier"], "Mid-Market")
        self.assertEqual(res["data"]["estimated_deal_value"], 10000)
        self.assertIn("Mid-Market AE", res["data"]["assigned_ae"])

    def test_smb_tier_lead(self):
        lead = {
            "email": "solo@gmail.com",
            "name": "Solo Dev",
            "company": "Unknown",
            "domain": "gmail.com",
            "title": "Freelancer",
            "message": "Hi",
            "is_corporate_domain": False,
        }
        res = score_lead({"data": lead})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["data"]["tier"], "Growth/SMB")
        self.assertEqual(res["data"]["estimated_deal_value"], 3500)


if __name__ == "__main__":
    unittest.main()
