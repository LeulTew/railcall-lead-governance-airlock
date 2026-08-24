# Architecture Specification — Lead Governance Airlock

## 1. System Objective
An enterprise-grade, governed automation workflow running on the RailCall Station runtime. Automates inbound lead processing across multiple SaaS systems with strict human-in-the-loop preview, automated deduplication, enrichment scoring, deal creation, Slack AE alert dispatch, and cryptographic audit receipts.

---

## 2. Component Diagram

```
[Inbound Lead Webhook]
          │
          ▼
┌───────────────────────────────────────────────┐
│ 1. Input Sanitization & Validation (Transform)│
│    - Strips invalid chars, validates email    │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 2. Deduplication & State Check (Transform)    │
│    - Checks CRM & local cache by SHA-256 hash │
│    - Prevents double-processing               │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 3. Lead Enrichment & Scoring (Transform)      │
│    - Clearbit / Apollo domain enrichment      │
│    - Evaluates company tier & deal size       │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 4. Airlock Governance Gate (Gate Node)        │
│    - Formats Markdown preview diff            │
│    - Operator / Policy Approval Checkpoint    │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 5. HubSpot CRM Deal Creation (Effect Node)    │
│    - Writes Deal + Contact to HubSpot         │
│    - Saga Rollback: archive deal on failure   │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 6. Slack AE Notification (Effect Node)        │
│    - Dispatches rich card to sales channel    │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 7. Airtable Pipeline Audit Log (Effect Node)  │
│    - Writes immutable record to Airtable base │
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 8. Ed25519 Signed Audit Receipt (Station Core)│
│    - Mints tamper-evident cryptographic proof │
│    - Verifiable offline via `railcall verify` │
└───────────────────────────────────────────────┘
```

---

## 3. Failure Mode & Resilience Matrix

| Failure Mode | Mitigation Strategy | Resulting Behavior |
| :--- | :--- | :--- |
| **Missing Form Fields** | Schema sanitization with fallback defaults | Validates payload safely; tags missing fields in review diff |
| **Duplicate Webhook / Form Submit** | Deterministic SHA-256 idempotency key check | Returns cached receipt; skips duplicate CRM write |
| **HubSpot API 429 Rate Limit** | Exponential backoff with jitter (3 retries) | Retries transparently without dropping lead |
| **Downstream Airtable Error** | Saga rollback triggers on HubSpot deal | Cancels deal creation, alerts operator, leaves zero partial state |
| **Runaway Spend** | Enforced `max_spend_cents: 500` cap in DAG spec | Halts pipeline before exceeding budget |
