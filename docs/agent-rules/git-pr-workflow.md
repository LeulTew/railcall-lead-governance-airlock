# Git & Pull Request Workflow

## 1. Branching Model
- **Main Branch (`main`)**: Production-ready, verified code. Protected against direct broken commits.
- **Feature Branches**: `feat/<descriptor>`, `fix/<descriptor>`, `refactor/<descriptor>`.

---

## 2. Commit Message Standards
Use conventional commit prefixes:
- `feat:` New workflow nodes, handlers, or capabilities
- `fix:` Bug fixes in validation, error handling, or DAG resolution
- `test:` Unit and integration tests
- `docs:` Operator documentation, README updates, or listing manifests
- `refactor:` Code improvements without behavioral changes

---

## 3. Pre-Commit / Pre-Push Checklist
Before committing and pushing changes:
1. Run local unit tests: `pytest tests/` (all tests passing).
2. Lint check: zero flake8/ruff lint warnings.
3. Validate RailCall build: `railcall build workflow.csv` produces a valid signed receipt.
4. Verify no secret tokens, API keys, or `.env` files are staged.
