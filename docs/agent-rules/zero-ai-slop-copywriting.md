# Zero AI Slop & Technical Copywriting Rules

> [!IMPORTANT]
> **Contest Rule Requirement**:
> "No AI slop - LLM-assisted is fine; a README that reads like it was generated with zero context isn't."
> All project documentation, listing text, error logs, and operator notices must follow strict human-centric, operator-first standards.

---

## 1. Banned Buzzwords & AI Tropes
Never use formulaic LLM buzzwords in documentation, code comments, or listing descriptions:
- ❌ *Banned Buzzwords*: "seamlessly", "world-class", "elevate", "unleash", "streamline", "cutting-edge", "supercharge", "robust powerhouse", "game-changer", "empower".
- ❌ *Banned AI Tropes*:
  - Excessive em-dash / hyphen spam (`—`, `-`) connecting disjointed clauses.
  - "In today's fast-paced digital world..."
  - "Let's dive in!" / "Without further ado..."
  - Vague metric claims without real backing ("10x faster", "99.999% efficiency").

---

## 2. Operator-First Writing Standards
1. **Concrete & Functional**:
   - Write clear, declarative explanations of what happens at each step:
     - *Bad*: "Supercharge your sales velocity by seamlessly routing leads with next-gen intelligence."
     - *Good*: "Validates inbound lead payload, queries CRM by email to check for duplicate deals, scores lead by company size, and previews the AE Slack dispatch before writing to HubSpot."
2. **Clear Parameter & Error Docs**:
   - Explicitly list required inputs, optional flags, failure responses, and retry behavior.
3. **Receipt Storytelling**:
   - The signed receipt summary must explain the exact sequence of events in plain English (e.g., *"Previewed deal creation for Acme Corp (Score: 85); approved by operator @sarah; created HubSpot deal #9812; signed receipt sha256:abc..."*).
