"""
Unit tests for Airlock Policy Evaluation & Preview Staging
"""

import unittest
from handlers.airlock import evaluate_auto_approval_policy, format_markdown_airlock_card, stage_airlock_preview


class TestAirlockPolicy(unittest.TestCase):

    def test_balanced_policy_enterprise_lead_auto_approves(self):
        profile = {
            "email": "vp@salesforce.com",
            "company": "Salesforce",
            "is_corporate_domain": True,
            "lead_score": 90,
            "tier": "Enterprise",
        }
        auto_app, reason = evaluate_auto_approval_policy(profile, policy_mode="balanced")
        self.assertTrue(auto_app)
        self.assertIn("Auto-approved", reason)

    def test_balanced_policy_free_domain_requires_review(self):
        profile = {
            "email": "user@gmail.com",
            "company": "Unknown",
            "is_corporate_domain": False,
            "lead_score": 45,
            "tier": "Growth/SMB",
        }
        auto_app, reason = evaluate_auto_approval_policy(profile, policy_mode="balanced")
        self.assertFalse(auto_app)
        self.assertIn("Free email domain", reason)

    def test_strict_policy_always_requires_operator(self):
        profile = {
            "email": "ceo@microsoft.com",
            "company": "Microsoft",
            "is_corporate_domain": True,
            "lead_score": 100,
        }
        auto_app, reason = evaluate_auto_approval_policy(profile, policy_mode="strict")
        self.assertFalse(auto_app)
        self.assertIn("Strict policy", reason)

    def test_stage_airlock_preview_diff_structure(self):
        profile = {
            "name": "Sarah Connor",
            "email": "sarah@cyberdyne.io",
            "company": "Cyberdyne Systems",
            "domain": "cyberdyne.io",
            "deal_name": "Cyberdyne Systems - Enterprise Inbound",
            "estimated_deal_value": 25000,
            "pipeline_stage": "qualifiedtobuy",
            "assigned_ae": "Taylor Vance (Enterprise AE)",
            "ae_slack_channel": "#enterprise-deals",
            "lead_score": 95,
            "is_corporate_domain": True,
            "score_breakdown": {"domain_authority": 30, "title_seniority": 30, "intent_signal": 20},
        }
        res = stage_airlock_preview({"data": profile})
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["action"], "airlock_staged")
        self.assertTrue(res["auto_approved"])
        self.assertIn("hubspot", res["preview_diff"])
        self.assertIn("slack", res["preview_diff"])
        self.assertIn("airtable", res["preview_diff"])


if __name__ == "__main__":
    unittest.main()
