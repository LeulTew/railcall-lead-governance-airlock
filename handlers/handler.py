"""
RailCall Lead Governance Airlock — Main Module Handler Dispatcher
Entry points for all declared module commands.
"""

from typing import Any, Dict, Optional

from handlers.validate import validate_lead as _validate_lead
from handlers.dedup import check_existing_lead as _check_existing_lead
from handlers.enrich import score_lead as _score_lead
from handlers.airlock import stage_airlock_preview as _stage_airlock_preview
from handlers.hubspot import create_deal as _create_deal, archive_deal as _archive_deal
from handlers.slack import post_lead_alert as _post_lead_alert
from handlers.airtable import log_event as _log_event
from handlers.crypto_receipt import mint_signed_receipt as _mint_signed_receipt


def validate_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validates inbound lead payload, normalizes fields, and detects disposable email domains."""
    return _validate_lead(payload, context)


def check_existing_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Computes SHA-256 idempotency fingerprint and checks against recent triage cache."""
    return _check_existing_lead(payload, context)


def score_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enriches profile, calculates ICP lead score (0-100), assigns tier and routing AE."""
    return _score_lead(payload, context)


def preview_airlock(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Stages structured before/after diffs for operator approval or automated policy sign-off."""
    return _stage_airlock_preview(payload, context)


def create_hubspot_deal(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Creates Contact and Deal in HubSpot CRM with dry-run support and rate-limit backoff."""
    return _create_deal(payload, context)


def archive_hubspot_deal(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Saga rollback handler to archive HubSpot deal on downstream pipeline failure."""
    return _archive_deal(payload, context)


def notify_slack_ae(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatches rich Block Kit alert card to the sales AE channel."""
    return _post_lead_alert(payload, context)


def log_airtable(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Appends immutable row to Airtable pipeline audit table."""
    return _log_event(payload, context)


def main(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fallback main dispatcher."""
    command = payload.get("command", "validate_lead")
    data = payload.get("data", payload)
    fn = globals().get(command)
    if fn and callable(fn):
        return fn(data, context)
    return {"status": "error", "error": f"Unknown command '{command}'"}
