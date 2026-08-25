"""
Airtable Pipeline Telemetry & Audit Logger Effect Handler
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from handlers.vault import get_secret

AIRTABLE_API_BASE = "https://api.airtable.com/v0"


def log_event(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Effect node: Appends an immutable telemetry row into an Airtable pipeline audit base.
    Operates as a resilient secondary sink.
    """
    lead_data = payload.get("data", payload)
    
    # Bypass for duplicate leads
    if payload.get("action") == "duplicate_skipped" or payload.get("is_duplicate"):
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "summary": "Airtable log bypassed for duplicate lead.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    dry_run = payload.get("dry_run", context.get("dry_run", True) if context else True)
    api_key = (get_secret("AIRTABLE_API_KEY") or "").strip()
    base_id = (get_secret("AIRTABLE_BASE_ID") or "").strip()
    table_name = (get_secret("AIRTABLE_TABLE_NAME") or "Inbound Leads").strip()

    row_record = {
        "fields": {
            "Email": lead_data.get("email", ""),
            "Name": lead_data.get("name", ""),
            "Company": lead_data.get("company", ""),
            "Domain": lead_data.get("domain", ""),
            "Lead Score": lead_data.get("lead_score", 0),
            "Tier": lead_data.get("tier", "Growth"),
            "Assigned AE": lead_data.get("assigned_ae", "Unassigned"),
            "Estimated Value": lead_data.get("estimated_deal_value", 0),
            "HubSpot Deal ID": str(lead_data.get("deal_id", "N/A")),
            "Processed At": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    }

    # 1. Dry-run preview branch
    if dry_run:
        return {
            "status": "ok",
            "action": "dry_run_preview",
            "summary": f"DRY-RUN: Staged Airtable record for {lead_data.get('email')} in table '{table_name}'",
            "preview_diff": row_record,
            "data": lead_data,
            "receipt_meta": {
                "dry_run": True,
                "table": table_name,
                "timestamp": time.time(),
                "cost_cents": 0,
            },
        }

    # 2. Live execution branch
    if not api_key or not base_id:
        return {
            "status": "warning",
            "action": "skipped_unconfigured",
            "summary": "Airtable logging skipped: AIRTABLE_API_KEY or AIRTABLE_BASE_ID not configured.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    url = f"{AIRTABLE_API_BASE}/{base_id}/{urllib.parse.quote(table_name)}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "RailCall-Governance-Airlock/1.0",
    }

    try:
        req_data = json.dumps(row_record).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            if status in {200, 201}:
                raw_body = response.read().decode("utf-8")
                res_json = json.loads(raw_body)
                record_id = res_json.get("id", "rec_created")
                return {
                    "status": "ok",
                    "action": "logged",
                    "summary": f"Recorded lead in Airtable table '{table_name}' (Record: {record_id})",
                    "data": {**lead_data, "airtable_record_id": record_id},
                    "receipt_meta": {
                        "airtable_record_id": record_id,
                        "timestamp": time.time(),
                        "cost_cents": 0,
                    },
                }
    except Exception as e:
        # Non-blocking warning sink
        return {
            "status": "warning",
            "action": "log_failed_non_blocking",
            "summary": f"Airtable sink error: {str(e)} (non-blocking)",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    return {
        "status": "warning",
        "action": "skipped",
        "summary": "Airtable response was not 200/201.",
        "data": lead_data,
        "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
    }
