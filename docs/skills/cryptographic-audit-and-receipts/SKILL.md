---
name: cryptographic-audit-and-receipts
description: "Procedures for generating, signing, and verifying tamper-evident receipts on RailCall with Ed25519 publisher keys, offline receipt verification (railcall verify), and audit trail storytelling."
---

# Cryptographic Audit & Signed Receipts Standard

This skill details how RailCall signs and cryptographically proves every workflow action, ensuring compliance, auditability, and tamper resistance.

---

## 1. The Signed Receipt Lifecycle

```
[Workflow DAG Execution]
        │
        ├── Collects inputs, node execution diffs, and timestamps
        ├── Computes SHA-256 state root across all node outputs
        │
        ▼
[Ed25519 Signature Minting]
        │
        ├── Station signs receipt using ~/.railcall/publisher_key.json
        │
        ▼
[Local Immutable Ledger]
        │
        └── Stored locally under ~/.railcall/receipts/<run_id>.json
```

---

## 2. Offline Verification (`railcall verify`)

Anyone receiving a RailCall workflow execution output can independently verify the authenticity and integrity of the execution without contacting external servers:

```bash
# Verify the most recent workflow execution receipt
railcall verify

# Verify a specific receipt file
railcall verify ~/.railcall/receipts/rc_receipt_20260824_abc123.json
```

**Verification Guarantees**:
1. **Publisher Authenticity**: Confirms the receipt was minted by the designated publisher keypair.
2. **Payload Non-Tampering**: Confirms that input parameters, intermediate transforms, and external effect payloads match the signed hash.
3. **Execution Integrity**: Proves that every effect node followed the approved preview gate.

---

## 3. Human-Readable Audit Storytelling

Receipts must tell a clear, coherent operational story for stakeholders:
- **Good Receipt Summary**:
  `"Lead triage workflow executed for contact 'alex@acme.com' (Enterprise Score: 92/100). Dry-run approved by @jordan. HubSpot Deal #4401 created, assigned to Enterprise AE @taylor, logged to Airtable base 'Q3 Pipeline'. Zero errors, total run time: 420ms."`
- **Bad Receipt Summary**:
  `"Completed pipeline execution. Status: success. Data: {...}"`
