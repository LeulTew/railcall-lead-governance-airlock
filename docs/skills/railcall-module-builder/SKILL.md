---
name: railcall-module-builder
description: "Guidelines and reference implementations for building RailCall custom modules, Python command handlers, module manifests (module.json), and testing suites."
---

# RailCall Module Builder Standard

This skill outlines how to build, test, and package Python modules for RailCall.

---

## 1. Module File Hierarchy

```
module-root/
├── module.json                # Module manifest & command schema
├── handlers/
│   ├── __init__.py
│   ├── validate.py            # Input validation & schema checking
│   ├── dedup.py               # In-memory / cache deduplication logic
│   ├── enrich.py              # Enrichment & scoring transforms
│   ├── hubspot.py             # HubSpot API integration & saga rollback
│   ├── slack.py               # Slack webhook & channel dispatcher
│   └── airtable.py            # Airtable base logger
├── templates/
│   └── lead_preview.md        # Operator airlock preview template
├── tests/
│   ├── test_validate.py
│   ├── test_dedup.py
│   ├── test_hubspot.py
│   └── test_saga_rollback.py
└── README.md                  # Module technical & operational docs
```

---

## 2. Manifest Definition (`module.json`)

```json
{
  "slug": "leultew/lead-governance-airlock",
  "version": "1.0.0",
  "name": "Lead Governance Airlock",
  "description": "Governed inbound lead enrichment, deduplication, and AE dispatch",
  "author": "LeulTew",
  "license_required": false,
  "commands": {
    "validate_lead": {
      "handler": "handlers/validate.py:validate_lead",
      "description": "Validates inbound lead payload and strips invalid characters",
      "inputs": {
        "email": { "type": "string", "required": true },
        "name": { "type": "string", "required": false },
        "company": { "type": "string", "required": false },
        "message": { "type": "string", "required": false }
      }
    },
    "score_lead": {
      "handler": "handlers/enrich.py:score_lead",
      "description": "Calculates lead priority score and determines sales routing",
      "inputs": {
        "email": { "type": "string", "required": true },
        "company": { "type": "string", "required": false }
      }
    },
    "create_hubspot_deal": {
      "handler": "handlers/hubspot.py:create_deal",
      "description": "Creates a new deal and contact in HubSpot CRM",
      "inputs": {
        "lead_data": { "type": "object", "required": true },
        "dry_run": { "type": "boolean", "default": true }
      }
    }
  }
}
```

---

## 3. Standard Handler Implementation Pattern

```python
"""
Standard Handler Template for RailCall Modules
"""
from typing import Any, Dict
import hashlib
import time

def create_deal(payload: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates a deal in HubSpot CRM with dry-run support and idempotency.
    """
    dry_run = payload.get("dry_run", False)
    lead = payload.get("lead_data", {})
    
    email = lead.get("email", "").strip().lower()
    if not email:
        return {
            "status": "error",
            "action": "skipped",
            "error": "Missing required field: email",
            "receipt_meta": {"timestamp": time.time()}
        }
    
    # Compute deterministic idempotency key
    idempotency_key = hashlib.sha256(f"deal:{email}:{lead.get('company', '')}".encode()).hexdigest()
    
    if dry_run:
        return {
            "status": "ok",
            "action": "dry_run",
            "summary": f"Preview: Would create HubSpot deal for {lead.get('name', email)} at {lead.get('company', 'Unknown')}",
            "preview_diff": {
                "object": "deal",
                "properties": {
                    "dealname": f"{lead.get('company', 'New Lead')} - Inbound",
                    "pipeline": "default",
                    "dealstage": "appointmentscheduled",
                    "amount": lead.get("estimated_value", 5000)
                }
            },
            "receipt_meta": {
                "idempotency_key": idempotency_key,
                "cost_cents": 0
            }
        }
    
    # Live execution logic with real API calls...
    return {
        "status": "ok",
        "action": "created",
        "summary": f"Created HubSpot deal #9812 for {email}",
        "data": {
            "deal_id": "9812",
            "contact_id": "4021"
        },
        "receipt_meta": {
            "idempotency_key": idempotency_key,
            "cost_cents": 0
        }
    }
```
