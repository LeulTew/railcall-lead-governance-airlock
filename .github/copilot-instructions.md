# GitHub Copilot Instructions — RailCall Governance Airlock

Canonical rules live in [`docs/agent-rules/`](../docs/agent-rules/README.md).
Skills live in [`docs/skills/`](../docs/skills/).

- **Language & Framework**: Python 3.10+, RailCall Station runtime, Pydantic/dataclasses for schema validation, `urllib3`/`requests` or `httpx` with retry backoff for API integration.
- **Architecture**: Directed Acyclic Graph (DAG) with explicit Transform vs Effect nodes, Sagas/Rollbacks, and Ed25519-signed receipt generation.
- **Copywriting**: Write zero-slop, operational documentation. Avoid hype adjectives or formulaic AI sentence structures.
