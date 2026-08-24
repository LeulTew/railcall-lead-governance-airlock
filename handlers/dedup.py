"""
Deduplication & State Hashing Transform Handler
"""

import hashlib
import time
from typing import Any, Dict, Optional, Set

# In-memory store for idempotency keys with timestamp expiry
_DEDUP_CACHE: Dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 86400.0  # 24 hours


def clear_dedup_cache() -> None:
    """Utility to clear deduplication cache during testing."""
    _DEDUP_CACHE.clear()


def compute_idempotency_key(email: str, company: str, time_bucket: Optional[int] = None) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for a lead.
    If time_bucket is provided, partitions keys into distinct rolling windows.
    """
    norm_email = email.strip().lower()
    norm_company = company.strip().lower()
    raw = f"lead:{norm_email}:{norm_company}"
    if time_bucket is not None:
        raw += f":bucket_{time_bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_existing_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform node: Checks whether the inbound lead has already been processed within the dedup window.
    """
    # Accept data either directly or nested under 'data' from previous node
    lead_data = payload.get("data", payload)
    email = lead_data.get("email", "").strip().lower()
    company = lead_data.get("company", "").strip().lower()

    if not email:
        return {
            "status": "error",
            "action": "skipped",
            "error": "Missing email for deduplication check.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    now = time.time()
    idempotency_key = compute_idempotency_key(email, company)

    # Clean up expired cache entries older than DEDUP_WINDOW_SECONDS
    expired_keys = [k for k, ts in _DEDUP_CACHE.items() if (now - ts) > DEDUP_WINDOW_SECONDS]
    for k in expired_keys:
        _DEDUP_CACHE.pop(k, None)

    # Check for duplicate
    if idempotency_key in _DEDUP_CACHE:
        prior_ts = _DEDUP_CACHE[idempotency_key]
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "is_duplicate": True,
            "summary": f"Deduplication notice: Lead {email} was already triaged {int(now - prior_ts)}s ago. Skipping CRM creation.",
            "data": lead_data,
            "receipt_meta": {
                "idempotency_key": idempotency_key,
                "first_seen_timestamp": prior_ts,
                "timestamp": now,
                "cost_cents": 0,
            },
        }

    # Record first-seen timestamp
    _DEDUP_CACHE[idempotency_key] = now

    return {
        "status": "ok",
        "action": "passed",
        "is_duplicate": False,
        "summary": f"Deduplication passed: Unique lead {email} registered.",
        "data": lead_data,
        "receipt_meta": {
            "idempotency_key": idempotency_key,
            "timestamp": now,
            "cost_cents": 0,
        },
    }
