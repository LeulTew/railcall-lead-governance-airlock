"""
Lead Validation, Sanitization & Schema Guard Transform Handler
Implements Sub-issues 1.1, 1.2, 1.3, 1.4 (Epic 1)
"""

import json
import re
import time
import urllib.parse
from typing import Any, Dict, Optional, Tuple, Union

# Comprehensive disposable email blacklist
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "trashmail.com",
    "sharklasers.com", "10minutemail.com", "yopmail.com", "throwawaymail.com",
    "dispostable.com", "guerrillamailblock.com", "guerrillamail.net", "guerrillamail.biz",
    "temp-mail.org", "fakeinbox.com", "maildrop.cc", "mohmal.com", "burnermail.io",
    "mytemp.email", "getairmail.com", "generator.email", "tempail.com", "tmail.ws"
}

# Strict RFC 5322 compatible regex
EMAIL_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9_'^&/+-])+(?:\.(?:[a-zA-Z0-9_'^&/+-])+)*@"
    r"(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})$"
)

# Control characters and zero-width unicode characters
CONTROL_AND_ZERO_WIDTH_REGEX = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]")
HTML_TAG_REGEX = re.compile(r"<[^>]*?>")


def sanitize_string(val: Any, max_length: int = 500) -> str:
    """
    Strips control characters, zero-width spaces, HTML tags, and truncates length safely.
    """
    if val is None:
        return ""
    as_str = str(val)
    # 1. Strip HTML tags
    no_html = HTML_TAG_REGEX.sub("", as_str)
    # 2. Strip control and zero-width characters
    cleaned = CONTROL_AND_ZERO_WIDTH_REGEX.sub("", no_html).strip()
    return cleaned[:max_length]


def normalize_domain(domain_str: str) -> str:
    """
    Normalizes domain names including Internationalized Domain Names (IDNs via Punycode).
    """
    cleaned = domain_str.strip().lower()
    try:
        # IDNA Punycode normalization
        return cleaned.encode("idna").decode("ascii")
    except Exception:
        return cleaned


def extract_domain(email_str: str) -> Optional[str]:
    """Extracts and normalizes domain from an email address string."""
    _, domain = extract_and_normalize_email(email_str)
    return domain


def extract_and_normalize_email(raw_email: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates, extracts, and normalizes email and domain.
    """
    sanitized = sanitize_string(raw_email, max_length=254).lower()
    if not sanitized or "@" not in sanitized:
        return None, None

    parts = sanitized.split("@")
    if len(parts) != 2:
        return None, None

    local_part, raw_domain = parts[0], parts[1]
    norm_domain = normalize_domain(raw_domain)
    full_email = f"{local_part}@{norm_domain}"

    if not EMAIL_REGEX.match(full_email):
        return None, None

    return full_email, norm_domain


def parse_inbound_payload(raw_body: Union[str, bytes, dict], content_type: str = "application/json") -> Dict[str, Any]:
    """
    Parses multi-format inbound payloads (JSON, form-urlencoded).
    """
    if isinstance(raw_body, dict):
        return raw_body

    if isinstance(raw_body, bytes):
        raw_text = raw_body.decode("utf-8", errors="replace")
    else:
        raw_text = str(raw_body)

    if not raw_text.strip():
        return {}

    if "application/x-www-form-urlencoded" in content_type:
        parsed = urllib.parse.parse_qs(raw_text)
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw_text": raw_text}


def validate_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform node: Validates inbound lead payload, strips hostile inputs, and rejects burner emails.
    """
    inbound_data = payload.get("data", payload)

    raw_email = inbound_data.get("email", "")
    email, domain = extract_and_normalize_email(raw_email)

    # 1. Missing or malformed email check
    if not email or not domain:
        return {
            "status": "error",
            "action": "rejected",
            "error": "Validation failed: A valid RFC-compliant 'email' is required.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    # 2. Disposable email domain check
    if domain in DISPOSABLE_DOMAINS:
        return {
            "status": "error",
            "action": "rejected",
            "error": f"Validation failed: Disposable email domain '{domain}' is blacklisted.",
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    raw_name = sanitize_string(inbound_data.get("name", ""), max_length=150)
    raw_company = sanitize_string(inbound_data.get("company", ""), max_length=150)
    raw_title = sanitize_string(inbound_data.get("title", ""), max_length=100)
    raw_message = sanitize_string(inbound_data.get("message", ""), max_length=2000)
    raw_phone = sanitize_string(inbound_data.get("phone", ""), max_length=50)

    # Derive company if missing
    free_domains = {"gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com", "aol.com", "protonmail.com"}
    derived_company = raw_company
    if not derived_company and domain not in free_domains:
        derived_company = domain.split(".")[0].capitalize()

    sanitized_data = {
        "email": email,
        "name": raw_name if raw_name else email.split("@")[0].capitalize(),
        "company": derived_company if derived_company else "Unknown",
        "title": raw_title,
        "domain": domain,
        "message": raw_message,
        "phone": raw_phone,
        "is_corporate_domain": domain not in free_domains,
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
