# Code Quality & Architectural Standards

## 1. Core Principles
- **Airlock Governance First**: Every action that modifies external state (CRM, database, messaging) must be previewable and reversible.
- **Strict Typing**: All Python code must use explicit type annotations (`typing` / `types`). Zero implicit `Any` where shapes are known.
- **Fail-Safe & Idempotent**: Handlers must safely handle duplicate runs, partial payloads, and upstream timeouts without creating orphaned state.

---

## 2. Python Handler Structure (`handlers/*.py`)
All module commands must follow a standardized structure:
1. **Input Validation**: Validate payload against strict dataclass or Pydantic model immediately upon entry.
2. **Dry-Run Support**: If `dry_run=True`, calculate and return the preview diff without mutating external APIs.
3. **Structured Returns**: Handlers must return a dictionary with a consistent contract:
   ```json
   {
     "status": "ok | error",
     "action": "created | updated | skipped | dry_run",
     "summary": "Human-readable description of what occurred",
     "data": { ... },
     "receipt_meta": {
       "idempotency_key": "sha256...",
       "timestamp": "ISO-8601",
       "cost_cents": 0
     }
   }
   ```
4. **Exception Handling**: Catch external network/API errors explicitly. Return clean error objects with actionable remediation instructions instead of unhandled stack traces.

---

## 3. DAG & Engine Spec Standards
- **Node Separation**:
  - **Transform Nodes**: Pure functions (validation, enrichment scoring, deduplication hashing, route calculation). Zero side effects.
  - **Effect Nodes**: Actions communicating with external services (`action_id`). Must declare rollback actions (`saga_rollback`).
- **Ceiling Budget (`max_spend_cents`)**: Always declare budget caps in `engine_spec` to prevent cost runaway.
- **For-Each Fan-Out**: Use bounded fan-outs with explicit concurrency limits.

---

## 4. Testing & Verification
- Unit test coverage for every handler's positive path, missing fields path, rate limit (429) simulation, and dry-run mode.
- Closed-loop verification cycle before committing any change:
  $$\text{Reproduce} \longrightarrow \text{Plan Diff} \longrightarrow \text{Surgical Edit} \longrightarrow \text{Run Tests} \longrightarrow \text{Self-Correct}$$
