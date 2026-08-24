"""
Deduplication & State Hashing Transform Handler
Implements Sub-issues 2.1, 2.2, 2.3, 2.4 (Epic 2)
"""

import hashlib
import os
import sqlite3
import threading
import time
from typing import Any, Dict, Optional, Tuple

_LOCK = threading.Lock()
_IN_MEMORY_CACHE: Dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 86400.0  # 24 hours
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".state_dedup.db")


def _init_sqlite_table(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes SQLite deduplication table if not existing."""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dedup_ledger (
                    fingerprint TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    company TEXT,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    hit_count INTEGER DEFAULT 1
                )
                """
            )
            conn.commit()
    except Exception:
        pass


def clear_dedup_cache(db_path: str = DEFAULT_DB_PATH) -> None:
    """Clears both in-memory and SQLite deduplication records."""
    with _LOCK:
        _IN_MEMORY_CACHE.clear()
        try:
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    conn.execute("DELETE FROM dedup_ledger")
                    conn.commit()
        except Exception:
            pass


def compute_idempotency_key(email: str, company: str, time_bucket: Optional[int] = None) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for a lead.
    """
    norm_email = email.strip().lower()
    norm_company = company.strip().lower()
    raw = f"lead:{norm_email}:{norm_company}"
    if time_bucket is not None:
        raw += f":bucket_{time_bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_existing_lead(
    payload: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    use_sqlite: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Transform node: Evaluates whether the lead has been processed within the dedup window.
    Supports thread-safe in-memory check with optional SQLite persistence.
    """
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

    with _LOCK:
        # 1. Clean in-memory entries older than DEDUP_WINDOW_SECONDS
        expired_keys = [k for k, ts in _IN_MEMORY_CACHE.items() if (now - ts) > DEDUP_WINDOW_SECONDS]
        for k in expired_keys:
            _IN_MEMORY_CACHE.pop(k, None)

        is_duplicate = False
        prior_timestamp = now

        # 2. Check In-Memory Cache
        if idempotency_key in _IN_MEMORY_CACHE:
            is_duplicate = True
            prior_timestamp = _IN_MEMORY_CACHE[idempotency_key]
        else:
            # 3. Optional SQLite persistent check
            if use_sqlite:
                _init_sqlite_table(db_path)
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT first_seen, hit_count FROM dedup_ledger WHERE fingerprint = ?",
                            (idempotency_key,),
                        )
                        row = cursor.fetchone()
                        if row and (now - row[0]) <= DEDUP_WINDOW_SECONDS:
                            is_duplicate = True
                            prior_timestamp = row[0]
                            conn.execute(
                                "UPDATE dedup_ledger SET last_seen = ?, hit_count = hit_count + 1 WHERE fingerprint = ?",
                                (now, idempotency_key),
                            )
                            conn.commit()
                        else:
                            conn.execute(
                                "INSERT OR REPLACE INTO dedup_ledger (fingerprint, email, company, first_seen, last_seen, hit_count) VALUES (?, ?, ?, ?, ?, 1)",
                                (idempotency_key, email, company, now, now),
                            )
                            conn.commit()
                except Exception:
                    pass

        if is_duplicate:
            elapsed_seconds = int(now - prior_timestamp)
            return {
                "status": "ok",
                "action": "duplicate_skipped",
                "is_duplicate": True,
                "summary": f"Deduplication notice: Lead {email} was already triaged {elapsed_seconds}s ago. Skipping CRM mutations.",
                "data": lead_data,
                "receipt_meta": {
                    "idempotency_key": idempotency_key,
                    "first_seen_timestamp": prior_timestamp,
                    "timestamp": now,
                    "cost_cents": 0,
                },
            }

        # Record unique lead in in-memory cache
        _IN_MEMORY_CACHE[idempotency_key] = now

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
