# Claude Code Instructions — RailCall Governance Airlock

Canonical engineering rules live in [`docs/agent-rules/`](docs/agent-rules/README.md).
Specialized domain skills live in [`docs/skills/`](docs/skills/).

## Commands
- Run test suite: `pytest tests/` or `python -m unittest discover tests/`
- Lint & format check: `flake8 .` / `black --check .` / `ruff check .`
- Build RailCall workflow locally: `railcall build workflow.csv`
- Dry-run workflow execution: `railcall workflow run .`
- Verify cryptographic signed receipt: `railcall verify`
- Marketplace publish: `railcall market publish`

## Non-negotiables
- Adhere to the Airlock Protocol: *Preview $\to$ Approve $\to$ Execute $\to$ Signed Receipt*.
- Enforce strict input validation, rate limiting (exponential backoff), and SHA-256 deduplication.
- Never hardcode secrets; use environment variables and Station integration keys.
- Write crisp, operational, human-centric documentation without LLM fluff.
