---
name: railcall-workflow-architecture
description: "Architectural blueprint for building production-grade RailCall workflows with Directed Acyclic Graphs (DAGs), engine_spec blocks, transform and effect nodes, sagas/rollback mechanisms, max_spend_cents ceilings, and tamper-evident audit trails."
---

# RailCall Workflow Architecture & Engine Spec Standard

This skill guides the design and implementation of governed automation workflows running on the RailCall Station runtime (`station-v0.51+`).

---

## 1. The Airlock Protocol

Every workflow in RailCall follows the four-stage governance cycle:
```
[Trigger / Payload]
        │
        ▼
   [PREVIEW]  ── (Transforms, validations, dry-run diff generation)
        │
        ▼
   [APPROVE]  ── (Human / Policy Gate: operator reviews structured diff)
        │
        ▼
   [EXECUTE]  ── (Effect nodes invoke real external APIs with idempotency)
        │
        ▼
[SIGNED RECEIPT] ── (Ed25519-signed, tamper-evident audit record minted)
```

---

## 2. DAG Engine Specification (`engine_spec`)

A runnable RailCall workflow is defined in `workflow.csv` with a comprehensive `engine_spec` JSON structure:

```json
{
  "engine_version": "1.0",
  "name": "enterprise-lead-airlock",
  "description": "Governed inbound lead enrichment, deduplication, and AE dispatch",
  "capabilities": {
    "providers": ["hubspot", "slack", "airtable", "apollo"],
    "max_spend_cents": 500
  },
  "nodes": [
    {
      "id": "validate_payload",
      "type": "transform",
      "handler": "handlers.validate:validate_lead",
      "inputs": ["trigger.body"]
    },
    {
      "id": "check_duplicate",
      "type": "transform",
      "handler": "handlers.dedup:check_existing_lead",
      "inputs": ["validate_payload.sanitized_data"],
      "depends_on": ["validate_payload"]
    },
    {
      "id": "enrich_and_score",
      "type": "transform",
      "handler": "handlers.enrich:score_lead",
      "inputs": ["check_duplicate.lead_record"],
      "depends_on": ["check_duplicate"]
    },
    {
      "id": "preview_airlock",
      "type": "airlock_gate",
      "preview_template": "templates/lead_preview.md",
      "inputs": ["enrich_and_score.scored_profile"],
      "depends_on": ["enrich_and_score"]
    },
    {
      "id": "create_hubspot_deal",
      "type": "effect",
      "action_id": "hubspot.create_deal",
      "handler": "handlers.hubspot:create_deal",
      "saga_rollback": "handlers.hubspot:archive_deal",
      "inputs": ["preview_airlock.approved_payload"],
      "depends_on": ["preview_airlock"]
    },
    {
      "id": "notify_slack_ae",
      "type": "effect",
      "action_id": "slack.post_message",
      "handler": "handlers.slack:post_lead_alert",
      "inputs": ["create_hubspot_deal.deal_info"],
      "depends_on": ["create_hubspot_deal"]
    },
    {
      "id": "log_airtable",
      "type": "effect",
      "action_id": "airtable.create_record",
      "handler": "handlers.airtable:log_event",
      "inputs": ["create_hubspot_deal.deal_info"],
      "depends_on": ["create_hubspot_deal"]
    }
  ]
}
```

---

## 3. Node Classification Rules

### A. Transform Nodes (`type: "transform"`)
- Pure, deterministic functions.
- Handle data cleansing, schema verification, hashing, deduplication checking, calculations, and dry-run diff formatting.
- **Rule**: NEVER call mutating external write endpoints in a transform node.

### B. Effect Nodes (`type: "effect"`)
- Perform state-mutating actions on external services (POST, PUT, DELETE, PATCH).
- Must declare an `action_id` and an associated `saga_rollback` handler whenever reversible.
- Must accept `idempotency_key` derived from the workflow execution ID to prevent double-writes.

### C. Airlock Gate Nodes (`type: "airlock_gate"`)
- Render human-readable diffs for operator review.
- Blocks downstream execution until authorized by an operator or policy engine.

---

## 4. Saga Rollback Protocol

When a multi-step effect pipeline fails midway (e.g., HubSpot deal created successfully, but subsequent Airtable logging triggers an unrecoverable failure):
1. The engine catches the effect node exception.
2. Identifies all previously executed effect nodes in reverse topological order.
3. Invokes each node's `saga_rollback` handler passing the previous node's output receipt.
4. Records the rollback execution in the final signed audit receipt.
