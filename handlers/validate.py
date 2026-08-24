"""
Lead Validation & Sanitization Transform Handler
"""

import re
import time
from typing import Any, Dict, Optional, Tuple

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "guerrillamail.com",
    "trashmail.com",
    "sharklasers.com",
    "10minutemail.com",
    "yopmail.com",
    "throwawaymail.com",
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
CONTROL_CHARS_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def sanitize_string(val: Any, max_length: int = 500) -> str:
    """Strips control characters, leading/trailing whitespace, and truncates length."""
    if val is None:
        return ""
    cleaned = CONTROL_CHARS_REGEX.sub("", str(val)).strip()
    return cleaned[:max_length]


def extract_domain(email: str) -> Optional[str]:
    """Extracts domain from email address."""
    parts = email.split("@")
    if len(parts) == 2:
        return parts[1].lower().strip()
    return None


def validate_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform node: Validates inbound lead payload, normalizes fields, and detects disposable domains.
    """
    raw_email = sanitize_string(payload.get("email", ""), max_length=254).lower()
    raw_name = sanitize_string(payload.get("name", ""), max_length=150)
    raw_company = sanitize_string(payload.get("company", ""), max_length=150)
    raw_title = sanitize_string(payload.get("title", ""), max_length=100)
    raw_message = sanitize_string(payload.get("message", ""), max_length=2000)
    raw_phone = sanitize_string(payload.get("phone", ""), max_length=50)

    # 1. Check required email field
    if not raw_email:
        return {
            "status": "error",
            "action": "rejected",
            "error": "Validation failed: 'email' is required.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    # 2. Syntax validation
    if not EMAIL_REGEX.match(raw_email):
        return {
            "status": "error",
            "action": "rejected",
            "error": f"Validation failed: '{raw_email}' is not a valid email syntax.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    domain = extract_domain(raw_email)
    if not domain:
        return {
            "status": "error",
            "action": "rejected",
            "error": "Validation failed: Unable to extract domain from email.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    # 3. Disposable domain check
    if domain in DISPOSABLE_DOMAINS:
        return {
            "status": "error",
            "action": "rejected",
            "error": f"Validation failed: Disposable email domain '{domain}' is not permitted.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    # Derive company name from domain if missing
    derived_company = raw_company
    if not derived_company and domain not in {"gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com"}:
        derived_company = domain.split(".")[0].capitalize()

    sanitized_data = {
        "email": raw_email,
        "name": raw_name if raw_name else raw_email.split("@")[0].capitalize(),
        "company": derived_company if derived_company else "Unknown",
        "title": raw_title,
        "domain": domain,
        "message": raw_message,
        "phone": raw_phone,
        "is_corporate_domain": domain not in {"gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com"},
    }

    return {
        "status": "ok",
        "action": "validated",
        "summary": f"Validated lead {sanitized_data['email']} ({sanitized_data['company']})",
        "data": sanitized_data,
        "receipt_meta": {
            "timestamp": time.time(),
            "cost_cents": 0,
        },
    }
