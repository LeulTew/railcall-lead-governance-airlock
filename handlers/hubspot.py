"""
HubSpot CRM Integration & Saga Rollback Effect Handler
"""

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

from handlers.vault import get_secret

HUBSPOT_API_BASE = "https://api.hubapi.com"


def _make_resilient_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    base_backoff: float = 0.5,
) -> Tuple[int, Dict[str, Any]]:
    """
    Executes an HTTP request with exponential backoff and jitter on rate limits (429/503).
    """
    if headers is None:
        headers = {}
    
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    headers.setdefault("Content-Type", "application/json")
    headers.setdefault("User-Agent", "RailCall-Governance-Airlock/1.0")

    last_status = 0
    last_response: Dict[str, Any] = {}

    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as response:
                last_status = response.status
                raw_body = response.read().decode("utf-8")
                last_response = json.loads(raw_body) if raw_body else {}
                return last_status, last_response
        except urllib.error.HTTPError as e:
            last_status = e.code
            try:
                raw_err = e.read().decode("utf-8")
                last_response = json.loads(raw_err) if raw_err else {"error": str(e)}
            except Exception:
                last_response = {"error": str(e)}

            # Handle 429 Too Many Requests or 503 Service Unavailable
            if last_status in {429, 503} and attempt < max_retries:
                # Check for Retry-After header or compute exponential backoff with full jitter
                retry_after_header = e.headers.get("Retry-After") if hasattr(e, "headers") else None
                if retry_after_header and retry_after_header.isdigit():
                    sleep_duration = float(retry_after_header)
                else:
                    sleep_duration = min(8.0, base_backoff * (2 ** attempt)) * random.uniform(0.7, 1.3)
                time.sleep(sleep_duration)
                continue

            return last_status, last_response
        except urllib.error.URLError as e:
            if attempt < max_retries:
                sleep_duration = base_backoff * (2 ** attempt) * random.uniform(0.7, 1.3)
                time.sleep(sleep_duration)
                continue
            return 0, {"error": f"Network connection failed: {str(e.reason)}"}

    return last_status, last_response


def create_deal(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Effect node: Creates Deal and Contact records in HubSpot CRM.
    Supports dry-run preview mode and respects rate limits.
    """
    lead_data = payload.get("data", payload)
    
    # Handle skipped duplicate leads gracefully
    if payload.get("action") == "duplicate_skipped" or payload.get("is_duplicate"):
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "summary": "HubSpot deal creation bypassed for duplicate lead.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    dry_run = payload.get("dry_run", context.get("dry_run", True) if context else True)
    access_token = (get_secret("HUBSPOT_ACCESS_TOKEN") or "").strip()

    email = lead_data.get("email", "").strip().lower()
    name = lead_data.get("name", "")
    company = lead_data.get("company", "New Lead")
    deal_name = lead_data.get("deal_name", f"{company} - Inbound Deal")
    stage = lead_data.get("pipeline_stage", "appointmentscheduled")
    amount = lead_data.get("estimated_deal_value", 5000)
    score = lead_data.get("lead_score", 50)

    # 1. Preview / Dry-run branch
    if dry_run:
        preview_deal_object = {
            "object": "deal",
            "properties": {
                "dealname": deal_name,
                "pipeline": "default",
                "dealstage": stage,
                "amount": str(amount),
                "lead_score": str(score),
                "assigned_ae": lead_data.get("assigned_ae", "Unassigned"),
            },
            "associations": [
                {
                    "to": {"type": "contact", "email": email},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}],
                }
            ],
        }
        return {
            "status": "ok",
            "action": "dry_run_preview",
            "summary": f"DRY-RUN: Staged HubSpot deal '{deal_name}' (Amount: ${amount}, Stage: {stage})",
            "preview_diff": preview_deal_object,
            "data": {
                **lead_data,
                "deal_id": "dry_run_deal_preview_id",
                "contact_id": "dry_run_contact_preview_id",
            },
            "receipt_meta": {
                "dry_run": True,
                "timestamp": time.time(),
                "cost_cents": 0,
            },
        }

    # 2. Live Execution Branch (requires HUBSPOT_ACCESS_TOKEN)
    if not access_token:
        return {
            "status": "error",
            "action": "failed",
            "error": "Live execution requires HUBSPOT_ACCESS_TOKEN environment variable.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    headers = {"Authorization": f"Bearer {access_token}"}

    # Step A: Create or Update Contact
    contact_payload = {
        "properties": {
            "email": email,
            "firstname": name.split()[0] if name else "",
            "lastname": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "company": company,
            "jobtitle": lead_data.get("title", ""),
            "phone": lead_data.get("phone", ""),
        }
    }
    status, contact_res = _make_resilient_request(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts",
        method="POST",
        headers=headers,
        data=contact_payload,
    )
    contact_id = contact_res.get("id") or "contact_upserted"

    # Step B: Create Deal
    deal_payload = {
        "properties": {
            "dealname": deal_name,
            "pipeline": "default",
            "dealstage": stage,
            "amount": str(amount),
        }
    }
    status, deal_res = _make_resilient_request(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/deals",
        method="POST",
        headers=headers,
        data=deal_payload,
    )

    if status not in {200, 201}:
        return {
            "status": "error",
            "action": "failed",
            "error": f"HubSpot deal creation failed (HTTP {status}): {deal_res.get('message', 'Unknown error')}",
            "data": lead_data,
            "receipt_meta": {"http_status": status, "timestamp": time.time(), "cost_cents": 0},
        }

    deal_id = deal_res.get("id", "live_deal_created")

    return {
        "status": "ok",
        "action": "created",
        "summary": f"Created HubSpot deal #{deal_id} for {company} (Assigned: {lead_data.get('assigned_ae')})",
        "data": {
            **lead_data,
            "deal_id": deal_id,
            "contact_id": contact_id,
            "hubspot_url": f"https://app.hubspot.com/contacts/deals/{deal_id}",
        },
        "receipt_meta": {
            "deal_id": deal_id,
            "contact_id": contact_id,
            "timestamp": time.time(),
            "cost_cents": 0,
        },
    }


def archive_deal(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Saga Rollback Handler: Archives/deletes the created HubSpot deal if downstream steps fail.
    """
    lead_data = payload.get("data", payload)
    deal_id = lead_data.get("deal_id")
    dry_run = payload.get("dry_run", context.get("dry_run", False) if context else False)

    if not deal_id or deal_id == "dry_run_deal_preview_id":
        return {
            "status": "ok",
            "action": "rollback_skipped",
            "summary": "Saga rollback skipped (dry-run or no deal_id present).",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    access_token = (get_secret("HUBSPOT_ACCESS_TOKEN") or "").strip()
    if not access_token:
        return {
            "status": "warning",
            "action": "rollback_unauthorized",
            "summary": f"Saga rollback could not authenticate to archive deal #{deal_id}.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    headers = {"Authorization": f"Bearer {access_token}"}
    status, res = _make_resilient_request(
        f"{HUBSPOT_API_BASE}/crm/v3/objects/deals/{deal_id}",
        method="DELETE",
        headers=headers,
    )

    if status in {200, 204}:
        return {
            "status": "ok",
            "action": "rolled_back",
            "summary": f"Saga rollback executed: Archived HubSpot deal #{deal_id} after downstream pipeline failure.",
            "data": {"archived_deal_id": deal_id},
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    return {
        "status": "error",
        "action": "rollback_failed",
        "error": f"Failed to archive deal #{deal_id} during saga rollback (HTTP {status})",
        "receipt_meta": {"http_status": status, "timestamp": time.time(), "cost_cents": 0},
    }
