---
name: resilient-api-integrations
description: "Best practices for building robust, fault-tolerant API integrations with exponential backoff for rate limits (HTTP 429), SHA-256 deduplication, schema sanitization, and structured error boundaries."
---

# Resilient API Integrations Standard

This skill establishes patterns to ensure external API communications withstand rate limits, transient network dropouts, malformed payloads, and duplicate webhooks.

---

## 1. Rate Limiting & Exponential Backoff with Jitter

When communicating with third-party APIs (HubSpot, Slack, Airtable, Apollo):
- Respect `Retry-After` headers on HTTP 429 / 503 responses.
- Implement exponential backoff with full jitter:
  $$t_{\text{wait}} = \min(t_{\text{max}}, t_{\text{base}} \times 2^{\text{attempt}}) \times \text{uniform}(0.5, 1.5)$$
- Enforce a maximum retry budget (e.g., 3 retries, maximum 15s total sleep) before failing gracefully to prevent workflow execution timeouts.

---

## 2. Deterministic Deduplication Hashing
To prevent double-processing on replayed webhooks or concurrent retries:
1. Normalize identifying fields (e.g., lowercase email, stripped domain name, ISO-date window).
2. Generate a SHA-256 fingerprint:
   $$\text{hash} = \text{SHA256}(\text{service} + ":" + \text{normalized\_key} + ":" + \text{action})$$
3. Check against the execution cache/store before invoking write endpoints.

---

## 3. Schema Sanitization & Missing Field Tolerance
- **Null Safety**: All fields must be extracted using safe getters (`payload.get("key", default)`).
- **Type Coercion**: Cast numeric values (e.g., phone numbers, employee counts, revenue) with try-except fallback to sensible defaults.
- **String Sanitization**: Strip non-printable control characters and truncate oversized fields before dispatching to CRM or Slack APIs.

---

## 4. Circuit Breakers & Non-Blocking Sinks
- Separate **critical paths** (e.g., CRM Deal creation) from **secondary telemetry sinks** (e.g., Airtable analytics log).
- If a secondary sink fails after max retries, record a partial warning in the receipt rather than aborting the entire business operation.
