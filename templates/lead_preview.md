# Lead Governance Airlock — Approval Required

> **Airlock Stage**: `PREVIEW` $\longrightarrow$ **Pending Operator Decision**
> **Idempotency Fingerprint**: `{{ data.idempotency_key }}`

---

### Inbound Prospect Profile
- **Contact Name**: {{ data.name }}
- **Email**: `{{ data.email }}`
- **Company**: **{{ data.company }}** (Domain: `{{ data.domain }}`)
- **Title**: {{ data.title | default("Not Specified") }}
- **Corporate Domain**: {% if data.is_corporate_domain %}✅ Verified Corporate{% else %}⚠️ Free Email Domain{% endif %}

---

### Enrichment & Scoring Breakdown
- **ICP Lead Score**: **{{ data.lead_score }} / 100**
- **Calculated Tier**: `{{ data.tier }}`
- **Sub-Scores**:
  - Domain Authority: `{{ data.score_breakdown.domain_authority }} / 30`
  - Title Seniority: `{{ data.score_breakdown.title_seniority }} / 30`
  - Company Profile: `{{ data.score_breakdown.company_profile }} / 20`
  - Intent Signal: `{{ data.score_breakdown.intent_signal }} / 20`

---

### Proposed Downstream Mutations (Dry-Run Preview)
1. **HubSpot CRM**:
   - Create Contact `{{ data.name }} <{{ data.email }}>`
   - Create Deal `{{ data.deal_name }}` (Stage: `{{ data.pipeline_stage }}`, Est. Value: **\${{ data.estimated_deal_value }}**)
   - Associate Contact $\leftrightarrow$ Deal
2. **Slack AE Notification**:
   - Dispatch rich priority card to `{{ data.ae_slack_channel }}`
   - Assign to AE **{{ data.assigned_ae }}** (`{{ data.ae_email }}`)
3. **Airtable Audit Sink**:
   - Append immutable row to `Q3 Inbound Leads` table

---

*Approve this airlock gate to execute live mutations and mint an Ed25519-signed audit receipt.*
