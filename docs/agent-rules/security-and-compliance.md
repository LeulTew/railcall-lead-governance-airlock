# Security, Credentials & Compliance Standards

## 1. Zero Secrets in Repositories (Absolute Mandate)
- **Never hardcode**: API keys, OAuth tokens, bearer secrets, webhook URLs, database passwords, private keys, or signing secrets.
- **Station Integrations**: Rely on RailCall Studio's local secret management (`Studio -> Integrations`) or environment variables prefixed with `RC_` / `SERVICE_`.
- **Pre-Publish Scan**: Before any `railcall market publish`, execute an automated entropy and regex scan across all repo files for leaked tokens.

---

## 2. PII & Data Handling
- **Airlock Sanitization**: Strip or redact unnecessary sensitive fields (credit cards, unneeded phone numbers, raw passwords) before passing payloads into LLM or third-party enrichment APIs.
- **Local Receipt Integrity**: Signed receipts store cryptographic hashes of actions and summaries. Avoid dumping unencrypted sensitive user payloads into plaintext public logs.

---

## 3. Cryptographic Keypair Governance
- **Ed25519 Local Isolation**: Publisher private keys generated via `railcall market publisher init` reside exclusively under `~/.railcall/publisher_key.json` with `0600` permissions.
- **Never export or bundle private keys** into workflow archives, git commits, or marketplace bundles.
- Only the public key is registered with the RailCall marketplace.
