---
name: railcall-contest-evaluator-review
description: "Production-grade review, evaluation, and baseline comparison rubric for RailCall workflows. Implements a 100-point contest scoring model, benchmark comparison against reference modules, and pragmatic self-audit gates."
---

# RailCall Contest Evaluator & Baseline Review Protocol

This skill equips agents and reviewers to evaluate any RailCall automation workflow against the official contest criteria, benchmark against live reference implementations, and execute pragmatic self-audits.

---

## 1. 100-Point Contest Scoring Rubric

Every workflow must be evaluated against these four core dimensions:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOTAL: 100 POINTS                                                     │
├──────────────────────────────┬────────┬────────────────────────────────┤
│ Category                     │ Weight │ Key Criteria                   │
├──────────────────────────────┼────────┼────────────────────────────────┤
│ 1. End-to-End Business Story │ 30 pts │ Real trigger to value, real API│
│ 2. Fault Tolerance & Rel.    │ 25 pts │ 429s, missing data, dedup, sagas│
│ 3. Signed Receipts & Airlock │ 25 pts │ Clear audit trail, hash verify │
│ 4. Operator Polish & Docs    │ 20 pts │ Zero-slop README, setup clarity│
└──────────────────────────────┴────────┴────────────────────────────────┘
```

### Detailed Breakdown:

### A. End-to-End Business Story (30 Points)
- **Real Trigger to Real Value (15 pts)**: Solves a high-stakes, recurring business problem (e.g., Enterprise Lead Triage & CRM Settle) rather than a trivial "hello world" demo.
- **Real External APIs (15 pts)**: Interacts with actual APIs (HubSpot, Slack, Airtable, Apollo, etc.) with real request/response contracts and zero placeholder mocks.

### B. Fault Tolerance, Edge Cases & Reliability (25 Points)
- **Rate Limit Handling (8 pts)**: Implements exponential backoff with jitter on HTTP 429/503.
- **Missing / Malformed Field Tolerance (7 pts)**: Gracefully handles null/missing payload fields without crashing.
- **Deduplication (5 pts)**: Prevents accidental duplicate operations using SHA-256 idempotency fingerprints.
- **Saga Rollback Recovery (5 pts)**: Automatically rolls back prior effect nodes if a downstream step fails.

### C. Signed Receipts & Airlock Governance (25 Points)
- **Airlock Preview $\to$ Approve Gate (10 pts)**: Clear preview of mutations before state alterations happen.
- **Signed Audit Trail (10 pts)**: Ed25519-signed receipts prove what was previewed vs executed.
- **Offline Verifiability (5 pts)**: Can be verified independently via `railcall verify`.

### D. Operator Polish & Zero-Slop Standard (20 Points)
- **Zero AI Slop in Docs (10 pts)**: Clear, concise, operator-oriented documentation without generic marketing filler.
- **Clean Configuration & Setup (10 pts)**: Easy-to-follow setup, environment variable guidance, and valid listing metadata (`contest:2026Q3`).

---

## 2. Baseline Benchmark Comparison Matrix

Compare your workflow against established reference modules:

| Feature / Criterion | Reference: `sami666/hubspot` | Reference: `dave/retainer-billing-run` | Reference: `imanchuk/incident-airlock` | **Target: Our Workflow** |
| :--- | :--- | :--- | :--- | :--- |
| **Airlock Preview** | Single action preview | Multi-node DAG preview | Alert triage diff | **Full Multi-Node DAG Preview** |
| **Saga Rollback** | Basic archive on error | Credit memo reversal | Rollback cloud config | **Automatic Reverse DAG Rollback** |
| **Spend Ceiling** | None | `max_spend_cents: 2000` | N/A | **Enforced `max_spend_cents: 500`** |
| **Deduplication** | Email query | Invoice hash table | Alert dedup window | **Deterministic SHA-256 Fingerprint** |
| **Rate-Limit Retry** | Basic retry | Backoff loop | Retry on 429 | **Backoff with Full Jitter** |
| **Offline Verify** | Pass | Pass | Pass | **100% Pass via `railcall verify`** |
| **Contest Polish** | Baseline example | Baseline example | Baseline example | **Contest-Ready Polish (95+ pts)** |

---

## 3. 5-Phase Self Pragmatic Review & Audit Checklist

Execute this checklist before any pull request or marketplace submission:

### Phase 1: Code & Handler Verification
- [ ] Are all Python handlers strictly typed with no bare `except:` blocks?
- [ ] Does every mutating handler support `dry_run=True`?
- [ ] Are return shapes consistent (`status`, `action`, `summary`, `data`, `receipt_meta`)?

### Phase 2: DAG & Engine Spec Audit
- [ ] Does `engine_spec` declare all providers and `max_spend_cents`?
- [ ] Are transform nodes strictly side-effect free?
- [ ] Do all effect nodes have associated `saga_rollback` handlers?

### Phase 3: Edge Case & Fault Injection Test
- [ ] Test with completely empty / missing optional fields: does it succeed or fail gracefully?
- [ ] Test with duplicate trigger payloads: does deduplication prevent duplicate writes?
- [ ] Simulate API 429 response: does backoff retry correctly?
- [ ] Simulate downstream API failure: does saga rollback trigger and restore state?

### Phase 4: Security & Secret Scan
- [ ] Zero hardcoded tokens or webhook URLs in repository.
- [ ] All sensitive keys retrieved from environment or RailCall station integrations.

### Phase 5: Receipts & Documentation Polish
- [ ] Does `railcall verify` pass on the generated receipt?
- [ ] Is `README.md` free of LLM buzzwords and fluff?
- [ ] Is `contest:2026Q3` present in the listing description?
