# B-BOT V3: continuous multi-timeframe strategy research — implementation plan
Date: 2026-10-14. This is a **research-only** expansion. R4 production and the uploaded original V3 engine are immutable.

## Verified starting point
- Hosted Windows research executes the original `strategy_lab/roadmap_manager.py` under a single-writer research workflow.
- A 15-minute cron requests bounded jobs. It is **not** a 10-minute checkpoint and does **not** provide per-frame parallelism.
- Authenticated V3 remote checkpoints exist. Periodic checkpoints, chained long jobs, hosted deduplication beyond the original capped trial ledger, and GA/Optuna integration with the official proposal path remain unverified/unimplemented.
- Workflow success does not prove an accepted trading strategy.

## Architecture
1. **Proposal tier:** Bounded, explicit strategy grammar; deterministic structures with canonical hashes. GA mutates/crosses *allowed* structures/parameters; Optuna optimizes training hyperparameters. Neither has permission to read blind/OOS outcomes for optimization.
2. **Official validation:** The original V3 controller, dataset contract, frozen blind tests, WF/OOS, hard-pass and deployment gates are unchanged. Original research is the ONLY authority for approval.
3. **Worker isolation:** One separate hosted job per authorized timeframe (initial set: 30m/1h/6h/12h/1d/1w, subject to canonical local policy); independent per-frame experiment ledger, progress marker, and immutable evidence. No shared writable SQLite database.
4. **Scheduling:** Remove 15-minute research starts ONLY AFTER a safe chained-run scheduler is tested. Target <=330 minutes/job, graceful stop >=20 minutes before the GitHub job timeout. Periodic checkpoint every 10 minutes **and** after terminal candidate records. An hourly watchdog may recover missing runs; scheduling is not guaranteed 24/7 availability. Enforce one active worker PER frame, not one global research lock.
5. **Durability:** Each trial commits COMPLETED/FAILED identity + frame + params + data/rules/code hashes + reason; incomplete work is not a completed trial. Checkpoint progress only after durable trial commit. On startup verify authenticated state and reconcile committed terminal records before resume.
6. **Storage:** Split small immutable outcome/index records from bulky evidence and regenerable candles. Hash and authenticate any encrypted remote objects. Deduplicate identical market datasets; version caches and enforce quotas. Never silently delete PASS/FAIL identities, even when the original live ledger rolls over. Purging large evidence requires separate approved retention policy.
7. **Merge:** A single validated central merger reads per-frame approved outcomes and emits signed/versioned release manifests; no concurrent workers write the release manifest.
8. **Production boundary:** GitHub never trades and has no EC2 credentials. EC2 pulls validated outputs only after explicit integration tests; SHADOW→CANARY→SMALL→NORMAL policy and R4 order/exit/recovery code remain unchanged.

## Implementation milestones and gates

| Phase | Deliverable | Gate |
| --- | --- | --- |
| A | Read-only research grammar, per-frame immutable SQLite experiment ledger, atomic progress marker, unit tests | No imports from live trading code; tests pass; duplicate and failure history preserved |
| B | Private original-source candidate adapter (GA/Optuna) | Frozen fixture parity, OOS isolation, no official-rule changes |
| C | Separate frame workers + long-run chained orchestration | Concurrent workers with isolated data; stop/resume and corruption tests; budget caps |
| D | 10-min checkpoints + secure durable aggregation | Interrupted-job replay with zero loss/duplicate accepted trials, provenance verified |
| E | Multi-TF data caching and durable evidence archival | Dataset hashes, quota alarms, recoverable archives, reproducibility tests |
| F | EC2 read-only pull + staged approval | Signed manifest, tamper/replay rejection, shadow/canary rollback rehearsal |

## This branch
Phase A **implemented**: `research_addon/structure_proposals.py`, `experiment_ledger.py`, `frame_progress.py` and `tests/test_multiframe_foundation.py`.
Phase B prototype **implemented in research-only isolation**: `research_addon/training_orchestrator.py` invokes GA and Optuna over deterministic structure proposals, keeps a per-frame ledger, and resumes only after completed batches. A manual-only `.github/workflows/multiframe-training-smoke.yml` defines six parallel **synthetic** workers and uploads consistent per-frame SQLite snapshots, with seven-day artifact retention. This is neither actual V3 research nor long-term remote persistence. CI on commit `449045f1` passed; later additions require their own CI verification.\n\n**Not implemented on this branch:** official V3 candidate adapter, actual market-data backtest in per-frame workers, automatically chained 5h30 jobs, periodic ten-minute remote checkpoints, independently durable frame state beyond artifact retention, central merger, production EC2 integration. Current 15-minute research workflow is unchanged. Do not label this branch a completed 24/7 deployment.

## Safety
Only merge after test review. No branch here alters the currently running `continuous-research.yml`, the original private `strategy_lab` code, or EC2 R4.

## Fourth increment (experimental only)
- Added `frame_snapshot.py` using SQLite online backup, SHA-256 manifest, corruption rejection, and restore-to-empty-directory. Snapshot files are **not encrypted**, so they must never be published with real private strategy results or account data; protected authenticated remote transport is a separate pending milestone.
- Added `frame_supervisor.py` to bound an explicitly supplied child research command; default budget 19,800 seconds with 1,200 seconds reserved for graceful stop and local snapshot every 600 seconds. This is a subprocess safety wrapper, not a currently scheduled long-running job.
- Added dedicated snapshot and supervisor tests. They run synthetic data only.
- Manual six-frame workflow remains a synthetic smoke, not an official research run. All changes are isolated from main and R4.
- **Still needed before production of a 24h research service:** official V3 candidate adapter, secure remote per-frame durable checkpoint + encryption, on-resume restore, chain scheduling with concurrency guards and quotas, live candle datasets and replay verification, monitor/watchdog, evidence retention strategy and operational tests.

## Fifth increment — encrypted transport foundation
- Existing 4th-increment GitHub synthetic CI succeeded: run 38547369652.
- Added `encrypted_frame_transport.py`: AES-256-GCM frame-bound encryption of a SQLite-consistent frame snapshot; rejects wrong frame, incorrect key, corruption, unexpected files, and excessively expanded archives. Unit test covers roundtrip and rejection paths.
- Real ciphertext upload, authenticated index branch publishing, collision-proof per-frame concurrency, restore-before-run, and automatic 5h30 chained execution are **not wired**. Do not publish plaintext snapshots or use short-lived GitHub artifacts as permanent archives.
- Production 15-minute original research workflow and R4 remain unchanged. This module is not an official V3 strategy approval or a live scheduler.
