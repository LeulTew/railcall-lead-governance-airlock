# Agent Rules Gateway

This directory contains the canonical rules governing architecture, coding standards, security, copywriting, and git workflows for the RailCall Governance Airlock project.

## Index of Rules

| Rule File | Description |
| :--- | :--- |
| [`code-quality.md`](code-quality.md) | Python standards, handler purity, DAG nodes, schema typing, error boundaries, atomic diffs |
| [`security-and-compliance.md`](security-and-compliance.md) | Zero hardcoded secrets, PII scrubbing, token isolation, rate-limit safety |
| [`zero-ai-slop-copywriting.md`](zero-ai-slop-copywriting.md) | Human-centric operator copy, banned LLM cliches, clear technical explanations |
| [`git-pr-workflow.md`](git-pr-workflow.md) | Git branch conventions, commit formatting, CI verification |

---

## Tool-Specific Discovery Mirrors
The rules in this directory are the single source of truth. When rules are updated, synchronize the mirrors:
- `AGENTS.md` (root directory)
- `CLAUDE.md` (root directory)
- `.antigravity/rules.md`
- `.github/copilot-instructions.md`
