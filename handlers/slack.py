"""
Slack AE Alert Notification Effect Handler
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


from handlers.vault import get_secret


def build_slack_blocks(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds an interactive Slack Block Kit card payload.
    """
    name = data.get("name", "Prospect")
    email = data.get("email", "")
    company = data.get("company", "Unknown")
    score = data.get("lead_score", 0)
    tier = data.get("tier", "Growth")
    ae = data.get("assigned_ae", "Unassigned")
    deal_id = data.get("deal_id", "N/A")
    deal_name = data.get("deal_name", "Inbound Deal")
    est_value = data.get("estimated_deal_value", 0)
    hubspot_url = data.get("hubspot_url", f"https://app.hubspot.com/contacts/deals/{deal_id}")

    tier_emoji = "🔥" if tier == "Enterprise" else "⚡" if tier == "Mid-Market" else "🌱"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{tier_emoji} New {tier} Inbound Lead: {company}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Contact:*\n{name} (<mailto:{email}|{email}>)"},
                {"type": "mrkdwn", "text": f"*ICP Score:*\n`{score} / 100` ({tier})"},
                {"type": "mrkdwn", "text": f"*Assigned AE:*\n{ae}"},
                {"type": "mrkdwn", "text": f"*Est. Pipeline Value:*\n${est_value:,}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*HubSpot Deal:* <{hubspot_url}|{deal_name}> (`#{deal_id}`)",
            },
        },
        {"type": "divider"},
    ]

    return {"blocks": blocks, "text": f"New {tier} Lead: {company} ({score}/100) assigned to {ae}"}


def post_lead_alert(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Effect node: Posts a rich Block Kit alert to the designated sales Slack channel.
    """
    lead_data = payload.get("data", payload)
    
    # Bypass for duplicate leads
    if payload.get("action") == "duplicate_skipped" or payload.get("is_duplicate"):
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "summary": "Slack notification bypassed for duplicate lead.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    dry_run = payload.get("dry_run", context.get("dry_run", True) if context else True)
    webhook_url = (get_secret("SLACK_WEBHOOK_URL") or "").strip()

    slack_card = build_slack_blocks(lead_data)

    # 1. Dry-run preview branch
    if dry_run:
        return {
            "status": "ok",
            "action": "dry_run_preview",
            "summary": f"DRY-RUN: Staged Slack alert for AE channel {lead_data.get('ae_slack_channel', '#sales')}",
            "preview_diff": slack_card,
            "data": lead_data,
            "receipt_meta": {
                "dry_run": True,
                "target_channel": lead_data.get("ae_slack_channel", "#sales"),
                "timestamp": time.time(),
                "cost_cents": 0,
            },
        }

    # 2. Live execution branch
    if not webhook_url:
        return {
            "status": "warning",
            "action": "skipped_no_webhook",
            "summary": "Slack notification skipped: SLACK_WEBHOOK_URL not configured.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    try:
        req_data = json.dumps(slack_card).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "RailCall-Governance-Airlock/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            if status in {200, 204}:
                return {
                    "status": "ok",
                    "action": "posted",
                    "summary": f"Dispatched Slack alert to {lead_data.get('ae_slack_channel')} for {lead_data.get('assigned_ae')}",
                    "data": lead_data,
                    "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
                }
    except Exception as e:
        return {
            "status": "error",
            "action": "failed",
            "error": f"Failed to post Slack notification: {str(e)}",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    return {
        "status": "error",
        "action": "failed",
        "error": "Unexpected response from Slack webhook endpoint.",
        "data": lead_data,
        "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
    }
