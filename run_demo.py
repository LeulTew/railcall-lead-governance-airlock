#!/usr/bin/env python3
"""
Interactive CLI Runner & Demo for RailCall Lead Governance Airlock
Demonstrates the complete Airlock cycle: Preview -> Approve -> Execute -> Signed Receipt
"""

import json
import time
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from handlers.validate import validate_lead
from handlers.dedup import check_existing_lead
from handlers.enrich import score_lead
from handlers.airlock import stage_airlock_preview
from handlers.hubspot import create_deal
from handlers.slack import post_lead_alert
from handlers.airtable import log_event
from handlers.crypto_receipt import mint_signed_receipt, verify_receipt
from handlers.budget import BudgetLedger


def print_banner():
    print("=" * 70)
    print("  RAILCALL LEAD GOVERNANCE AIRLOCK - GAUNTLET DEMO RUNNER")
    print("  Protocol: Ingestion -> Preview Diff -> Policy Gate -> Sagas -> Signed Receipt")
    print("  Contest:  Track B - Best Workflow (contest:2026Q3)")
    print("=" * 70 + "\n")


def run_airlock_pipeline(lead_input: dict, auto_approve: bool = True, policy_mode: str = "balanced"):
    budget = BudgetLedger(max_spend_cents=500)

    print("[STAGE 0: INGESTION] Received Inbound Trigger Payload:")
    print(json.dumps(lead_input, indent=2))
    print("-" * 70)

    # 1. Transform: Validate
    print("[NODE 1: TRANSFORM] Executing 'validate_lead'...")
    val_res = validate_lead(lead_input)
    if val_res["status"] != "ok":
        print(f"[ERROR] Rejected: {val_res['error']}")
        return val_res
    print(f"[OK] {val_res['summary']}")
    budget.record_node_cost("validate_lead", 0)
    print("-" * 70)

    # 2. Transform: Dedup
    print("[NODE 2: TRANSFORM] Executing 'check_existing_lead'...")
    dedup_res = check_existing_lead(val_res)
    print(f"[OK] {dedup_res['summary']}")
    if dedup_res.get("action") == "duplicate_skipped":
        print("[NOTICE] Idempotency intercept: Skipping downstream CRM mutations.")
        return dedup_res
    budget.record_node_cost("check_existing_lead", 0)
    print("-" * 70)

    # 3. Transform: Enrich & Score
    print("[NODE 3: TRANSFORM] Executing 'score_lead' (ICP Engine)...")
    enrich_res = score_lead(dedup_res)
    profile = enrich_res["data"]
    print(f"[OK] Score: {profile['lead_score']}/100 | Tier: {profile['tier']} | AE: {profile['assigned_ae']}")
    print(f"     Breakdown: Domain={profile['score_breakdown']['domain_authority']} Seniority={profile['score_breakdown']['title_seniority']} Intent={profile['score_breakdown']['intent_signal']}")
    budget.record_node_cost("score_lead", 0)
    print("-" * 70)

    # 4. Airlock Gate: Preview & Policy Check
    print("[STAGE 1: AIRLOCK PREVIEW GATE] Staging Proposed Mutations...")
    airlock_res = stage_airlock_preview(enrich_res, context={"policy_mode": policy_mode})
    print(f"[OK] Policy Verdict: {airlock_res['policy_verdict']}")

    print("\n" + "#" * 60)
    print("--- [OPERATOR AIRLOCK PREVIEW CARD] ---")
    print(f"Contact:      {profile['name']} <{profile['email']}>")
    print(f"Company:      {profile['company']} (Domain: {profile['domain']})")
    print(f"Deal Name:    {profile['deal_name']}")
    print(f"Deal Value:   ${profile['estimated_deal_value']:,}")
    print(f"Assigned AE:  {profile['assigned_ae']}")
    print(f"Slack Alerts: {profile['ae_slack_channel']}")
    print(f"Auto-Approve: {'YES (Policy Passed)' if airlock_res['auto_approved'] else 'NO (Requires Manual Decision)'}")
    print("#" * 60 + "\n")

    # 5. Operator Decision Check
    if not airlock_res["auto_approved"] and not auto_approve:
        decision = input(">> Authorize downstream state mutations? [Y/n]: ").strip().lower()
        if decision not in {"y", "yes", ""}:
            print("[NOTICE] Operator rejected airlock approval. Pipeline halted safely.")
            return {"status": "rejected_by_operator"}

    print("[STAGE 2: AIRLOCK APPROVED] Execution authorized.")
    print("-" * 70)

    # 6. Effect Nodes Execution (Dry-run safe default)
    print("[STAGE 3: EXECUTION] Executing Governed Effect Nodes...")
    hub_exec = create_deal(enrich_res, context={"dry_run": True})
    print(f"  * HubSpot CRM: {hub_exec['summary']}")
    budget.record_node_cost("hubspot_deal", 0)

    slack_exec = post_lead_alert(hub_exec, context={"dry_run": True})
    print(f"  * Slack AE:    {slack_exec['summary']}")
    budget.record_node_cost("slack_alert", 0)

    airtable_exec = log_event(slack_exec, context={"dry_run": True})
    print(f"  * Airtable:    {airtable_exec['summary']}")
    budget.record_node_cost("airtable_log", 0)
    print("-" * 70)

    # 7. Mint Signed Receipt
    print("[STAGE 4: SIGNED RECEIPT MINTING] Minting Cryptographic Proof...")
    mutations_map = {
        "hubspot_deal": hub_exec["action"],
        "slack_alert": slack_exec["action"],
        "airtable_log": airtable_exec["action"],
    }
    receipt = mint_signed_receipt(
        workflow_slug="leultew/lead-governance-airlock",
        version="1.0.0",
        lead_data=profile,
        mutations=mutations_map,
        spend_cents=budget.current_spend_cents,
        max_spend_cents=budget.max_spend_cents,
    )

    print("\n--- MINTED SIGNED AUDIT RECEIPT ---")
    print(json.dumps(receipt, indent=2))
    print("=" * 70)

    # 8. Offline Verification Test
    is_valid, verify_msg = verify_receipt(receipt)
    print(f"🛡️  [OFFLINE VERIFICATION] {verify_msg}")
    print("=" * 70)
    print("Pipeline completed cleanly with zero errors.")
    return receipt


if __name__ == "__main__":
    print_banner()
    sample_lead = {
        "email": "sarah.connor@cyberdyne.io",
        "name": "Sarah Connor",
        "company": "Cyberdyne Systems",
        "title": "VP of Engineering",
        "message": "We need 500 enterprise seats for our automated defense platform with SOC2 compliance.",
        "phone": "+1-555-0199",
    }
    run_airlock_pipeline(sample_lead, auto_approve=True, policy_mode="balanced")
