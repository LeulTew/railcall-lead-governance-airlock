# RailCall Lead Governance Airlock

[![Contest](https://img.shields.io/badge/Contest-contest%3A2026Q3-FF155D.svg)](https://railcall.ai/contest)
[![Runtime](https://img.shields.io/badge/RailCall_Station-v0.59-0F172A.svg)](https://railcall.ai/docs)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A governance-first automation workflow for inbound lead triage, enrichment, and sales dispatch built for the **RailCall Runtime & Marketplace**.

Every lead action executes through the **Airlock Protocol**:
$$\text{Trigger} \longrightarrow \text{Preview Diff} \longrightarrow \text{Operator Approval} \longrightarrow \text{CRM \& Slack Execution} \longrightarrow \text{Signed Audit Receipt}$$

---

## Key Features

- **Governed Multi-Node DAG (`engine_spec`)**: Pure transform nodes for validation, deduplication, and lead scoring, paired with controlled effect nodes for CRM mutations.
- **Deterministic Deduplication**: Computes SHA-256 idempotency fingerprints to eliminate duplicate CRM deal creation across replayed webhooks.
- **Saga Rollback Recovery**: Automatically rolls back created HubSpot records if downstream Slack or Airtable actions experience unrecoverable failures.
- **Resilient Rate-Limit Handling**: Exponential backoff with jitter on HTTP 429/503 errors across all external SaaS integrations.
- **Tamper-Evident Receipts**: Mints Ed25519-signed execution receipts verifiable offline via `railcall verify`.
- **Runtime Budget Ceiling**: Strict `max_spend_cents: 500` ceiling enforced directly by the DAG execution engine.

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- RailCall Station CLI:
  ```bash
  curl -fsSL https://railcall.ai/install.sh | bash
  ```

### 2. Local Build & Dry-Run
```bash
# Build the workflow DAG and generate initial signed plan
railcall build workflow.csv

# Execute dry-run preview (generates preview diff without mutating CRM)
railcall workflow run .

# Verify the signed audit receipt offline
railcall verify
```

### 3. Running Test Suite
```bash
pytest tests/
```

---

## Repository Structure

```
├── .antigravity/            # Antigravity/Gemini rule mirrors
├── .github/                 # Copilot instructions & CI workflows
├── docs/
│   ├── agent-rules/         # Canonical architecture, quality & security rules
│   ├── skills/              # Specialized domain skills & evaluator review
│   ├── CONTEST_BRIEF.md     # Official contest rubric and requirements
│   └── ARCHITECTURE_SPEC.md # Full technical specification
├── handlers/                # Python module command handlers
├── templates/               # Operator airlock preview templates
├── tests/                   # Automated unit & resilience test suite
├── module.json              # Module manifest
├── workflow.csv             # Workflow DAG definition with engine_spec
├── AGENTS.md                # Central agent rules gateway
└── README.md                # Project documentation
```

---

## Contest Entry Details
- **Track**: Track B - Best Workflow ($450 USD Prize Pool)
- **Tag**: `contest:2026Q3`
- **Publisher Handle**: `LeulTew`
