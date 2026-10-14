# Durable GitHub research state — manual diagnostic

This workflow is manual-only (workflow_dispatch); it does **not** perform B-BOT research or update AWS.

1. All research-addon unit tests run before state is changed.
2. An Actions job fetches isolated `research-state` branch (creates it if missing).
3. Checkpoint schema / fingerprints are checked by `checkpoint_store.load`.
4. A **synthetic diagnostic record** (not strategy/evidence/approval) is appended.
5. The checkpoint is atomically written locally, reopened, then committed to the state branch.
6. Runs are serialized via `concurrency`; failed pushes or corrupt states fail closed.

Important:
- `research-state` is **public** because this GitHub repository is public. Never store account information, strategies considered confidential, raw account data, API keys, private market feed or secrets in it.
- GitHub token in the workflow has content-write permission for this diagnostic. Keep this permission limited to state-related jobs, not untrusted PR jobs.
- Disable/avoid untrusted workflows and ensure repo branch protection or rulesets cannot be bypassed.
- This is a **test harness**, not a production research ledger: it has no schema for dataset versions, experimental evidence, candidate lineage, sealed once-only verification, optimizer resume, or signed release.
- Workflow only accepts main as invocation source. GitHub Actions must be permitted by organization policy; manual run and successful persisted state still need confirmation.
- AWS synchronization and live trading deployment are intentionally absent.
