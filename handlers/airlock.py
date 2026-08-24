"""
Airlock Governance & Preview Diff Engine
Implements Sub-issues 4.1, 4.2, 4.3, 4.4 (Epic 4)
"""

import json
import time
from typing import Any, Dict, Optional, Tuple


def evaluate_auto_approval_policy(profile: Dict[str, Any], policy_mode: str = "balanced") -> Tuple[bool, str]:
    """
    Evaluates whether an inbound lead qualifies for automated approval or requires manual operator sign-off.
    """
    score = profile.get("lead_score", 0)
    is_corporate = profile.get("is_corporate_domain", False)
    domain = profile.get("domain", "")

    if policy_mode == "strict":
        # Strict mode: All mutations require manual operator authorization
        return False, "Strict policy: Manual operator authorization required."

    if policy_mode == "lenient":
        # Lenient mode: Auto-approve any corporate lead with score >= 50
        if is_corporate and score >= 50:
            return True, f"Lenient policy: Auto-approved corporate lead (Score: {score})."
        return False, "Lenient policy: Non-corporate domain requires operator review."

    # Balanced mode (Default)
    if is_corporate and score >= 80:
        return True, f"Balanced policy: Auto-approved High-Confidence Enterprise Lead (Score: {score}/100)."
    
    if not is_corporate:
        return False, "Balanced policy: Free email domain requires operator verification."

    return False, f"Balanced policy: Score {score}/100 below 80 threshold for auto-approval."


def format_markdown_airlock_card(profile: Dict[str, Any]) -> str:
    """
    Renders human-readable markdown preview diff for operator review.
    """
    score_breakdown = profile.get("score_breakdown", {})
    return f"""# Lead Governance Airlock — Action Authorization

### Inbound Prospect Profile
- **Contact**: {profile.get('name')} <{profile.get('email')}>
- **Company**: **{profile.get('company')}** (Domain: `{profile.get('domain')}`)
- **Title**: {profile.get('title') or 'Not Specified'}
- **Corporate Domain**: {'Yes (Verified)' if profile.get('is_corporate_domain') else 'No (Free Mail)'}

### Enrichment & Scoring
- **ICP Lead Score**: **{profile.get('lead_score', 0)} / 100** ({profile.get('tier', 'Unknown')})
- **Sub-scores**: Domain={score_breakdown.get('domain_authority', 0)}/30 | Seniority={score_breakdown.get('title_seniority', 0)}/30 | Intent={score_breakdown.get('intent_signal', 0)}/20

### Proposed State Mutations (Dry-Run Preview)
1. **HubSpot CRM**: Create Deal `{profile.get('deal_name')}` (Est. Amount: **${profile.get('estimated_deal_value', 0):,}**, Stage: `{profile.get('pipeline_stage')}`)
2. **Slack Alert**: Dispatch priority card to `{profile.get('ae_slack_channel')}` assigned to **{profile.get('assigned_ae')}**
3. **Airtable**: Append telemetry record to `Inbound Leads` table
"""


def stage_airlock_preview(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Airlock Gate Node: Stages structured preview diffs and evaluates governance policy.
    """
    lead_data = payload.get("data", payload)

    if payload.get("action") == "duplicate_skipped" or payload.get("is_duplicate"):
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "summary": "Airlock gate bypassed for duplicate lead.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    policy_mode = context.get("policy_mode", "balanced") if context else "balanced"
    auto_approved, policy_reason = evaluate_auto_approval_policy(lead_data, policy_mode=policy_mode)
    markdown_card = format_markdown_airlock_card(lead_data)

    preview_diff = {
        "hubspot": {
            "action": "create_deal_and_contact",
            "deal_name": lead_data.get("deal_name"),
            "amount": lead_data.get("estimated_deal_value"),
            "stage": lead_data.get("pipeline_stage"),
        },
        "slack": {
            "action": "post_channel_alert",
            "channel": lead_data.get("ae_slack_channel"),
            "assigned_ae": lead_data.get("assigned_ae"),
        },
        "airtable": {
            "action": "append_audit_row",
            "table": "Inbound Leads",
        },
    }

    return {
        "status": "ok",
        "action": "airlock_staged",
        "auto_approved": auto_approved,
        "policy_verdict": policy_reason,
        "summary": f"Airlock staged for {lead_data.get('email')} -> {policy_reason}",
        "markdown_card": markdown_card,
        "preview_diff": preview_diff,
        "data": lead_data,
        "receipt_meta": {
            "auto_approved": auto_approved,
            "policy_mode": policy_mode,
            "timestamp": time.time(),
            "cost_cents": 0,
        },
    }
