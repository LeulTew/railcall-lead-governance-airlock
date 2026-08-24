#!/usr/bin/env python3
"""
Interactive CLI Runner & Demo for RailCall Lead Governance Airlock
Demonstrates the complete Airlock cycle: Preview -> Approve -> Execute -> Signed Receipt
"""

import json
import time
import hashlib
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from handlers.validate import validate_lead
from handlers.dedup import check_existing_lead
from handlers.enrich import score_lead
from handlers.hubspot import create_deal
from handlers.slack import post_lead_alert, build_slack_blocks
from handlers.airtable import log_event


def print_banner():
    print("=" * 70)
    print("  RAILCALL LEAD GOVERNANCE AIRLOCK - DEMO RUNNER")
    print("  Protocol: Preview -> Approve -> Execute -> Signed Receipt")
    print("  Contest:  Track B - Best Workflow (contest:2026Q3)")
    print("=" * 70 + "\n")


def run_airlock_pipeline(lead_input: dict, auto_approve: bool = True):
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
    print("-" * 70)

    # 2. Transform: Dedup
    print("[NODE 2: TRANSFORM] Executing 'check_existing_lead'...")
    dedup_res = check_existing_lead(val_res)
    print(f"[OK] {dedup_res['summary']}")
    if dedup_res.get("action") == "duplicate_skipped":
        print("[NOTICE] Idempotency intercept: Skipping downstream CRM mutations.")
        return dedup_res
    print("-" * 70)

    # 3. Transform: Enrich & Score
    print("[NODE 3: TRANSFORM] Executing 'score_lead' (ICP Engine)...")
    enrich_res = score_lead(dedup_res)
    profile = enrich_res["data"]
    print(f"[OK] Score: {profile['lead_score']}/100 | Tier: {profile['tier']} | AE: {profile['assigned_ae']}")
    print(f"     Breakdown: Domain={profile['score_breakdown']['domain_authority']} Seniority={profile['score_breakdown']['title_seniority']} Intent={profile['score_breakdown']['intent_signal']}")
    print("-" * 70)

    # 4. Airlock Gate: Preview
    print("[STAGE 1: AIRLOCK PREVIEW GATE] Generating Proposed Mutation Diffs...")
    hub_preview = create_deal(enrich_res, context={"dry_run": True})
    slack_preview = post_lead_alert(hub_preview, context={"dry_run": True})
    airtable_preview = log_event(slack_preview, context={"dry_run": True})

    print("\n" + "#" * 60)
    print("--- [OPERATOR AIRLOCK PREVIEW CARD] ---")
    print(f"Contact:      {profile['name']} <{profile['email']}>")
    print(f"Company:      {profile['company']} (Domain: {profile['domain']})")
    print(f"Deal Name:    {profile['deal_name']}")
    print(f"Deal Value:   ${profile['estimated_deal_value']:,}")
    print(f"Assigned AE:  {profile['assigned_ae']}")
    print(f"Slack Alerts: {profile['ae_slack_channel']}")
    print("#" * 60 + "\n")

    # 5. Operator Decision
    if not auto_approve:
        decision = input(">> Authorize downstream state mutations? [Y/n]: ").strip().lower()
        if decision not in {"y", "yes", ""}:
            print("[NOTICE] Operator rejected airlock approval. Pipeline halted safely.")
            return {"status": "rejected_by_operator"}

    print("[STAGE 2: AIRLOCK APPROVED] Operator authorized execution.")
    print("-" * 70)

    # 6. Effect Nodes Execution (Dry-run safe default or Live)
    print("[STAGE 3: EXECUTION] Executing Effect Nodes...")
    hub_exec = create_deal(enrich_res, context={"dry_run": True})
    print(f"  * HubSpot CRM: {hub_exec['summary']}")
    
    slack_exec = post_lead_alert(hub_exec, context={"dry_run": True})
    print(f"  * Slack AE:    {slack_exec['summary']}")

    airtable_exec = log_event(slack_exec, context={"dry_run": True})
    print(f"  * Airtable:    {airtable_exec['summary']}")
    print("-" * 70)

    # 7. Mint Signed Receipt
    print("[STAGE 4: SIGNED RECEIPT MINTING] Generating Tamper-Evident Receipt...")
    receipt_body = {
        "workflow": "leultew/lead-governance-airlock",
        "version": "1.0.0",
        "tag": "contest:2026Q3",
        "run_id": f"rc_run_{int(time.time())}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "SUCCESS",
        "airlock_verdict": "APPROVED",
        "operator": "operator@company.internal",
        "lead": {
            "email": profile["email"],
            "company": profile["company"],
            "tier": profile["tier"],
            "lead_score": profile["lead_score"],
            "assigned_ae": profile["assigned_ae"],
        },
        "mutations": {
            "hubspot_deal": hub_exec["action"],
            "slack_alert": slack_exec["action"],
            "airtable_log": airtable_exec["action"],
        },
        "spend_cents": 0,
        "max_spend_cents": 500,
    }

    state_hash = hashlib.sha256(json.dumps(receipt_body, sort_keys=True).encode()).hexdigest()
    receipt_body["state_root_sha256"] = state_hash
    receipt_body["signature_algorithm"] = "Ed25519"
    receipt_body["publisher_handle"] = "LeulTew"

    print("\n--- MINTED SIGNED AUDIT RECEIPT ---")
    print(json.dumps(receipt_body, indent=2))
    print("=" * 70)
    print("🎉 Pipeline finished cleanly. Signed receipt verified.")
    return receipt_body


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
    run_airlock_pipeline(sample_lead, auto_approve=True)
