# RailCall Lead Governance Airlock

[![Contest](https://img.shields.io/badge/Contest-contest%3A2026Q3-FF155D.svg)](https://railcall.ai/contest)
[![Track](https://img.shields.io/badge/Track%20B-Vertical%20Workflow%20Templates%20(RevOps)-7C3AED.svg)](https://railcall.ai/contest)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Governed inbound lead triage, enrichment, and AE routing for the **RailCall Runtime** (`contest:2026Q3`).

---

## 1. What It Does & Who It's For

**For**: RevOps teams and Sales Operations leaders processing high-volume inbound leads.

**What It Does**: Triages inbound prospects through the **Airlock Protocol** ($\text{Preview} \to \text{Approve} \to \text{Execute} \to \text{Signed Receipt}$):
1. **Validation & Sanitization**: Strips hostile input and rejects disposable email domains (`mailinator.com`, 1,000+ trie filter).
2. **Deduplication**: SHA-256 fingerprinting with dual-layer cache (memory + persistent SQLite) stops replayed webhooks from creating duplicate CRM deals.
3. **ICP Scoring**: Evaluates domain authority, seniority, and intent keywords (0–100 score) and routes to Enterprise, Mid-Market, or SMB AEs.
4. **Airlock Gate**: Stages structured mutation diffs for operator approval or automated policy sign-off.
5. **CRM & AE Dispatch**: Creates HubSpot Deals and posts Slack Block Kit alerts.
6. **Saga Rollbacks**: Unwinds and archives created HubSpot deals if downstream steps fail.
7. **Signed Receipts**: Mints Ed25519-signed receipts verified offline via `railcall verify`.

---

## 2. Install & Fresh Run (<1 Minute)

Zero external dependencies (pure Python 3.9+ standard library):

```bash
# Clone and verify test suite (32 tests in 0.03s)
git clone https://github.com/LeulTew/railcall-lead-governance-airlock.git
cd railcall-lead-governance-airlock
python -m unittest discover -s tests -v
```

---

## 3. Working Example & Expected Output

Run the dry-run CLI execution:

```bash
python -m handlers.cli execute fixtures/leads/01_enterprise_cyberdyne.json -o receipt.json
```

**Expected Output**:
```json
{
  "workflow": "leultew/lead-governance-airlock",
  "version": "1.0.0",
  "tag": "contest:2026Q3",
  "run_id": "rc_run_1787601961",
  "status": "SUCCESS",
  "airlock_verdict": "APPROVED",
  "lead": {
    "email": "sarah.connor@cyberdyne.io",
    "company": "Cyberdyne Systems",
    "tier": "Enterprise",
    "lead_score": 100,
    "assigned_ae": "Taylor Vance (Enterprise AE)"
  },
  "mutations": {
    "hubspot_deal": "dry_run_preview",
    "slack_alert": "dry_run_preview",
    "airtable_log": "dry_run_preview"
  },
  "spend_cents": 0,
  "max_spend_cents": 500,
  "state_root_sha256": "bacddf7fb6edb8eb558fd9a27ad40dc35d1bc752a391ab52d352ec78e5e24ae3",
  "signature_algorithm": "Ed25519",
  "publisher_handle": "LeulTew"
}
```

Verify receipt offline:
```bash
python -m handlers.cli verify receipt.json
# Output: [PASSED] Receipt verified: Valid Ed25519 signature and non-tampered state root
```

---

## 4. Credentials & Configuration

Copy `.env.example` to `.env` or set in RailCall Station:
- `HUBSPOT_ACCESS_TOKEN`: Private app token with `crm.objects.deals.write` scope.
- `SLACK_WEBHOOK_URL`: Incoming webhook for sales AE channel.
- `AIRTABLE_API_KEY`: (Optional) Secondary audit sink token.
- *Default Mode*: `RC_DRY_RUN=true` simulates mutations safely without credentials.

---

## 5. Known Limitations

- SQLite deduplication defaults to local disk ledger (`.state_dedup.db`); multi-region distributed clusters should mount a shared volume or Redis instance.
- Airtable rate limit is capped at 5 req/sec per base.
