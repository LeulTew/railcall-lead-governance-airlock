---
name: marketplace-packaging-and-compliance
description: "Rules and automated checklists for packaging, validating, tagging (contest:2026Q3), and publishing workflows to the RailCall marketplace."
---

# Marketplace Packaging & Compliance Standard

This skill outlines requirements for passing RailCall's automated and manual pre-publish review queues.

---

## 1. Contest Listing Metadata

To enter the official RailCall Contest (Track B - Best Workflow, $450 USD Prize Pool):
1. **Mandatory Tag**: Include `contest:2026Q3` in the listing description.
2. **Slug Namespace**: Must be namespaced under your claimed publisher handle: `your-handle/lead-governance-airlock`.
3. **Module Dependencies**: Declare any dependent modules in `bundle.json` or `module_dependency` field:
   ```json
   {
     "module_dependency": {
       "id": "leultew/lead-governance-airlock",
       "minimum_version": "1.0.0"
     }
   }
   ```

---

## 2. Pre-Publish Review Queue Checklist

An admin manually inspects every submission before it is approved for the marketplace:

| Check | Requirement | Verification Command |
| :--- | :--- | :--- |
| **No Mocks / Stubs** | Must interact with real API endpoints or legitimate webhooks. | Inspection of `handlers/*.py` |
| **Zero Secret Leaks** | No hardcoded tokens, passwords, or webhook secrets in code. | `grep -E "(sk_|Bearer|key-|ghp_)" .` |
| **Valid Signed Build** | Workflow builds cleanly and yields a signed receipt. | `railcall build workflow.csv` |
| **Clean Operator Docs** | Zero AI buzzword stuffing; concise setup instructions. | Inspection of `README.md` |
| **Dry-Run Safe** | Workflow defaults to dry-run preview until explicitly authorized. | `railcall workflow run --dry-run` |

---

## 3. Publishing Commands

```bash
# 1. Initialize and register publisher keypair (once ever)
railcall market publisher init LeulTew
railcall market publisher register

# 2. Authenticate
railcall market login your@email.com

# 3. Claim slug
railcall market claim LeulTew/lead-governance-airlock

# 4. Publish bundle
railcall market publish
```
