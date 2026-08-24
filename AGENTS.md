# RailCall Airlock Workflow Engineering Rules

## 1. Project Mission & Identity
This repository contains a production-grade, governed automation workflow designed for the **RailCall Runtime & Marketplace**. Every action in this workflow adheres to the **Airlock Protocol**:
$$\text{Preview} \longrightarrow \text{Approve} \longrightarrow \text{Execute} \longrightarrow \text{Signed Receipt}$$

Targeting the **RailCall Contest (Track B - Best End-to-End Automation, $450 USD Prize Pool)**, scored against the official 100-point rubric with tag `contest:2026Q3`.

---

## 2. Agent Rules Gateway

Canonical project rules are organized in [`docs/agent-rules/`](docs/agent-rules/README.md). Load the relevant rule topic for your task:

| Topic | Focus Area | Canonical Rule File |
| :--- | :--- | :--- |
| **Code Quality & Architecture** | Python 3.10+ handlers, DAG engine spec, typing, error boundaries | [`docs/agent-rules/code-quality.md`](docs/agent-rules/code-quality.md) |
| **Security & Secrets** | Zero hardcoded keys, PII sanitization, environment governance | [`docs/agent-rules/security-and-compliance.md`](docs/agent-rules/security-and-compliance.md) |
| **Zero-Slop Copywriting** | Operator-focused documentation, no marketing fluff or LLM tropes | [`docs/agent-rules/zero-ai-slop-copywriting.md`](docs/agent-rules/zero-ai-slop-copywriting.md) |
| **Git & PR Workflow** | Atomic commits, branch hygiene, pre-push verification | [`docs/agent-rules/git-pr-workflow.md`](docs/agent-rules/git-pr-workflow.md) |

---

## 3. Specialized Project Skills

Specialized domain skills are located in [`docs/skills/`](docs/skills/):

| Skill Name | Purpose |
| :--- | :--- |
| [`railcall-workflow-architecture`](docs/skills/railcall-workflow-architecture/SKILL.md) | `workflow.csv`, `engine_spec`, transform/effect nodes, sagas, `max_spend_cents` |
| [`railcall-module-builder`](docs/skills/railcall-module-builder/SKILL.md) | Python module handlers, `module.json` manifest, CLI execution |
| [`resilient-api-integrations`](docs/skills/resilient-api-integrations/SKILL.md) | 429 backoff, SHA-256 deduplication, schema validation, real API error handling |
| [`cryptographic-audit-and-receipts`](docs/skills/cryptographic-audit-and-receipts/SKILL.md) | Ed25519 signing, tamper-evident receipts, offline `railcall verify` |
| [`marketplace-packaging-and-compliance`](docs/skills/marketplace-packaging-and-compliance/SKILL.md) | Contest tagging (`contest:2026Q3`), clean README, zero-leak check |
| [`railcall-contest-evaluator-review`](docs/skills/railcall-contest-evaluator-review/SKILL.md) | 100-pt rubric review, reference baseline comparison, self-pragmatic audit |
| [`agent-efficiency-and-mcp-workflows`](docs/skills/agent-efficiency-and-mcp-workflows/SKILL.md) | Dynamic reasoning budgets, context hygiene, surgical patching |

---

## 4. Non-Negotiable Operational Directives

1. **Working on Real APIs**: Never commit mock or stub fallbacks as final implementation.
2. **Deterministic Governance**: All effect nodes modifying state must emit structured preview diffs and require operator approval.
3. **No AI Slop in Docs or Receipts**: Keep all READMEs, receipts, and listings operational, concrete, and concise.
4. **Closed-Loop Verification**: Always verify handlers locally with automated tests and check receipts using `railcall verify` before pushing or publishing.
