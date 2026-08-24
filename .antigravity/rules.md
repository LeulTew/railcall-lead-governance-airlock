# Antigravity Rules — RailCall Governance Airlock

Canonical rules live in [`docs/agent-rules/`](../docs/agent-rules/README.md) and skills live in [`docs/skills/`](../docs/skills/).

1. **Closed-Loop Engineering**:
   - Write real, functional handlers using Python 3.10+.
   - Validate every handler with automated unit tests before integrating into DAG.
   - Enforce dry-run mode by default and ensure state alterations emit preview payloads.
2. **Airlock Governance**:
   - Every effect node must have an explicit `action_id` and rollback handler.
   - Guard execution with `max_spend_cents` to prevent runaway API spend.
3. **Contest Compliance (`contest:2026Q3`)**:
   - Adhere strictly to the 100-point rubric in [`docs/CONTEST_BRIEF.md`](../docs/CONTEST_BRIEF.md).
   - Use the self-evaluation review skill in [`docs/skills/railcall-contest-evaluator-review/SKILL.md`](../docs/skills/railcall-contest-evaluator-review/SKILL.md) to audit changes against reference benchmarks.
