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

## Sixth increment — content-addressed frame state objects
- Added `remote_frame_objects.py` for per-frame AES-GCM checkpoint object identity, local immutable object publication, index-based authenticated restore, and corruption rejection; tested with synthetic SQLite records.
- This **does not** yet upload data to GitHub, commit remote indexes, ensure central concurrency isolation, chain jobs, or provide long-term remote state. The object path is intentionally transport-independent; plaintext real V3 results must never enter the public branch.
- Only deploy after testing independent per-frame remote branch/lock semantics, authentication, secret management, crash consistency, quotas, and recovery under actual GitHub Actions.

## Seventh increment — manual encrypted Git remote smoke (not running)
- `git_frame_checkpoint.py`, `frame_checkpoint_cli.py`: stage and restore frame-bound encrypted snapshots using immutable objects and an authenticated plaintext-free index.
- `.github/workflows/multiframe-persistence-smoke.yml`: manual-only, six-frame *synthetic* worker matrix; one writer per frame; separate `synthetic-frame-state-<frame>` branches; restore before test; encrypted commit after a completed test. It is deliberately NOT scheduled and not an actual strategy research worker.
- WARNING: Workflow has not yet been dispatched or validated in an actual remote-restore cycle. The CI unit tests do not prove Git branch race handling, remote credentials, restore after termination, or long-lived retention. The synthetic branch may carry only encrypted training state, NEVER production data.
- Still missing: official V3 candidate adapter and authorization, persistent ten-minute remote checkpoints during running jobs, long-running chained 5h30 jobs, automatic restart/watchdog, and large-scale research data lifecycle.

## Eighth increment — commit boundary and local Git recovery
- Added `frame_git_sync.py` to snapshot a frame SQLite ledger consistently, encrypt the checkpoint, stage encrypted immutable objects, and make a Git commit. No remote push from this helper.
- Added `tests/test_frame_git_sync.py`: local isolated Git roundtrip verifies encrypted object commit and checkpoint restoration; missing frame ledger fails closed.
- The manual-only six-frame remote persistence smoke was previously added but has **not been dispatched**. No actual GitHub remote state continuation, 10-minute remote checkpoint, unattended restart, official V3 parallel runner, or permanent storage is confirmed.
- Do not deploy real strategy material to synthetic-state branches. Existing original research `main` workflows and R4 are unchanged.

## Ninth increment — safe chain-resume gating
- Confirmed eighth-increment GitHub CI success: run 38548125891.
- Added `frame_run_manifest.py` and tests to validate independent frame run identities, immutable head/checkpoint hashes, terminal status, timestamps and stale/revision-mismatched resume refusal.
- This does **not** automatically dispatch a new workflow or make remote continuity proven. The encrypted per-frame manual smoke still needs actual dispatch and two successive runs with per-frame state comparison before being trusted.
- Do not enable self-restarting GitHub Actions until encrypted remote restore, concurrency controls, budget limits, failure recovery and official V3 adapter have passed end-to-end validation.

## Tenth increment — bounded supervisor persistence callback
- Confirmed ninth-increment CI success: run 38548294501.
- `frame_supervisor.supervise()` now accepts an optional `checkpoint_callback(frame, verified_local_snapshot_directory)`. It is invoked after every timed snapshot and at final cleanup; exceptions are not swallowed, so a failed remote persistence callback cannot be silently claimed successful.
- `tests/test_frame_supervisor.py` checks that callbacks receive manifest-verified, consistent SQLite snapshots.
- This is an integration seam, not a completed remote upload or a verified 10-minute persisted checkpoint. An authenticated Git push callback and durable store consistency/restore tests are required before production scheduling.

## Eleventh increment — pre-publication checkpoint guard
- Added `checkpoint_publish_guard.py`: verifies source snapshot SHA256 and checks decrypted staged ciphertext against each source file's exact bytes in an external temporary directory. Does not write decrypted plaintext under a Git worktree.
- Added `tests/test_checkpoint_publish_guard.py` for roundtrip and source corruption rejection.
- **Not yet verified:** actual GitHub push, remote refetch, two consecutive workflows, live 10-minute remote checkpoints or self-dispatch. Do not claim remote durability from local unit tests. Existing `main` continuous workflow and R4 are unchanged.

## Twelfth increment — Git remote roundtrip harness
- Eleventh-increment CI passed (run 38548638915).
- Added `frame_remote_git.py` to create a synthetic per-frame remote branch only with explicit initial-seed authorization, push encrypted frame checkpoint and independently refetch it before claiming durability.
- Added `tests/test_frame_remote_git.py` to check a local bare-Git remote through two consecutive runs, an initial reset guard, failure/success trial retention and restoration. Tests are synthetic and do not run real trading strategies.
- This is NOT yet an authenticated GitHub-hosted remote experiment, nor a 10-minute remote checkpoint, 5h30 automatic chain or integration into unchanged official V3. The manual workflow on feature branch has not been dispatched; the original production research schedule stays unchanged.

## Thirteenth increment — byte-exact remote checkpoint verification
- Confirmed twelfth-increment CI passed: run 38548795619.
- After an encrypted Git push, `frame_remote_git.py` now refetches the state from the remote branch, decrypts it, and compares SHA-256 and byte lengths of every persisted file against the source SQLite-consistent snapshot; valid but stale ciphertext is no longer treated as evidence of successful persistence.
- The remote Git regression test now covers a third unchanged-state publish/restore and validates both failed and successful experiment records remain intact. These tests use a local bare Git remote, not live GitHub.
- Next mandatory gate: manually dispatch and re-run the GitHub-hosted synthetic encrypted persistence workflow from an eligible registered workflow branch, without promoting to production. Existing V3 scheduled workflow and R4 remain unchanged.

## Fourteenth increment — real GitHub smoke evidence
- Actual first hosted encrypted 6h frame-state run 38549073036: SUCCESS; state persisted to independent synthetic frame branch.
- Actual second GitHub run 38549138070: SUCCESS for 1h and 6h concurrently. 6h log explicitly emitted RESTORED and training batch reported 31 previously recorded candidates, 0 new candidates and 0 reevaluated candidates. These are synthetic training candidates only, not official V3 trials or approved strategies.
- Enhanced `git_frame_checkpoint.stage_frame` to decrypt and verify the old object before reusing it for byte-identical snapshots, reducing unnecessary content-addressed encrypted objects. Added reuse test.
- Expanded an opt-in feature-branch-only synthetic persistence workflow to six independent timeframes for live GitHub Actions smoke testing; this changes no original continuous research schedule or R4 code.
- Still pending: six-frame workflow result, remote ten-minute mid-job checkpoint, worker self-chaining, original V3 official research integration, independent immutable ledger over long-term storage rollover, production release signing and AWS pull.

## Fifteenth increment — checkpoint callback to authenticated Git remote
- Fixed checkpoint-reuse test and verified all three GitHub test workflows succeeded on SHA b5b20474 (Research CI run 38549413616).
- Added `hosted_frame_runner.py` to supervise an explicit child job and, at each local timed checkpoint or final cleanup, authenticate the staged encrypted snapshot, commit/push to the isolated synthetic frame branch, refetch it and compare decrypted byte hashes. Errors fail closed. The worktree/credentials must already be initialized by a trusted workflow.
- Added `tests/test_hosted_frame_runner.py`, using a local bare Git remote with seeded failed trial and verifying that new synthetic training and previous failed evidence both survive encrypted publication.
- IMPORTANT: ten-minute checkpoint execution on GitHub hosted long-running jobs remains unverified; the current synthetic job is short and ends before ten minutes. No actual V3 strategy engine is connected. Current original main research workflow and EC2 R4 remain unchanged.

## Sixteenth increment — checkpoint evolution regression
- Fifteenth-increment GitHub CI failed in `test_hosted_frame_runner`: encrypted checkpoint reuse assumed an earlier snapshot contained `training_progress.json` when the new snapshot had added that file, raising FileNotFoundError. This was a real integration regression, not a strategy rejection.
- `git_frame_checkpoint.py` now treats missing old snapshot members as changed content and creates a new authenticated encrypted checkpoint rather than crashing or pretending the old state matched.
- Added explicit regression to `test_git_frame_checkpoint.py` covering first-save without progress, repeated identical checkpoint, and new progress-file addition.
- Recheck full GitHub CI before marking the fix as passed; periodic hosted 10-minute persistence and 24h automatic chaining are not yet verified. Production V3/R4 remain unchanged.

## Seventeenth increment — bounded repeated batches (synthetic only)
- Sixteenth-increment CI passed on SHA c900ef0d (Research CI run 38549798843).
- Added `bounded_research_continuation.py` to run a finite, capped number of synthetic research batches per frame, stopping immediately on failure; never dispatches additional GitHub workflows, submits live trades or modifies the official V3 backtester.
- The feature-branch GitHub persistence smoke now executes two consecutive synthetic batches per frame before encrypted remote state commit. This verifies in-job continuation and fingerprint dedup if the hosted workflow succeeds.
- **Not implemented**: self-restarting across GitHub Actions jobs, 5h30 real research, ten-minute remote mid-job checkpoints, real market data and official V3 adapter. These gates are intentionally not represented as complete.

## Eighteenth increment — fail-closed inter-job continuation gate
- Seventeenth-increment six-frame hosted synthetic 2-batch workflow passed: run 38549998076.
- Added `restart_gate.py` and `tests/test_restart_gate.py`: a future inter-job chaining controller may only continue if explicitly enabled, the previous GitHub job succeeded, the remote checkpoint was independently verified, the checkpoint timestamp is fresh, and a strict hop cap has not been exceeded.
- Does NOT currently dispatch another GitHub Actions run. No scheduled or recursive workflow was enabled, so the original V3 research and R4 remain unaffected. Actual 24-hour autonomous research remains unimplemented.

## Nineteenth increment — opt-in authenticated GitHub dispatch handoff
- Verified eighteenth-increment Research CI passed: run 38550161489.
- Added `dispatch_next_research.py` to call GitHub's workflow_dispatch API for the explicitly approved feature branch only, **only after** the previously implemented restart gate checks successful job, checkpoint verification, recency, enabled flag and bounded hop count. This does not contain or log secrets.
- Added bounded `frame` / `hop` workflow_dispatch inputs to the synthetic persistence workflow and synthetic API mock tests.
- **Not enabled**: the workflow does not invoke this dispatcher itself. GitHub requires a workflow registered on the default branch for workflow_dispatch; this feature-branch-only workflow is not yet registered there. Thus no claim of automatic chaining or 24/7 execution. Push-trigger remains limited to workflow file changes on the feature branch for synthetic smoke.
- The original 15-min main research runner and EC2 R4 are unchanged.

## Twentieth increment — hosted mid-job remote checkpoint evidence
- Nineteenth-increment Research CI run 38550350309 passed.
- Hosted synthetic workflow run 38550517165 passed all six frame jobs. Its 6h frame used `hosted_frame_runner` to write/read back remote encrypted checkpoints while a child job was still alive, with 2-second test interval and `REMOTE_CHECKPOINT_VERIFIED=6h` logged three times. The run first emitted `RESTORED` and completed two bounded batches.
- This demonstrates intermediate GitHub persistence under a SHORT synthetic test. It does not establish actual 600-second cadence over a long hosted job, workflow-to-workflow self-dispatch, unlimited 24/7 availability, actual V3 official engine use or AWS deployment. Do not enable scheduled chaining before end-to-end guard tests and GitHub default-branch workflow registration.

## Twenty-first increment — guarded job-to-job handoff controller
- Twentieth-increment hosted six-frame smoke succeeded (run 38550517165), and associated Research CI passed (run 38550492203).
- Added `continue_hosted_chain.py`: fail-closed opt-in controller performs fresh Git remote checkout, authenticates frame checkpoint restoration and uses the bounded GitHub workflow-dispatch API bridge. It explicitly prints CHAIN_DISABLED without accessing credentials or network unless `BBOT_SYNTHETIC_CHAIN_ENABLED=true`.
- Added `tests/test_continue_hosted_chain.py` for default-off behavior.
- **Not wired into a workflow step**: no GitHub job-to-job auto-dispatch is enabled; GitHub workflow_dispatch must be registered on default branch. No scheduled 24/7 action or official V3 backtesting was started.

## Twenty-second increment — strengthened default-off continuation checks
- Added remote ciphertext-index existence checks to `continue_hosted_chain.py` after decrypting remote frame state, before optional dispatch.
- Added `tests/test_continue_chain_safety.py`: a real local bare Git remote with encrypted synthetic ledger is present, but the continuation controller remains disabled without any GitHub token.
- No workflow invocation of the dispatcher, no GitHub auto-restart activation, no official V3 strategy research activation and no R4 changes.

## Twenty-third increment — genuine remote checkpoint age required
- Twenty-second-increment Research CI passed: run 38550888953.
- Fixed continuation authorization so the checkpoint freshness condition uses the remotely fetched Git commit's actual commit timestamp, rather than generating the current time after any successful restore. Previously, an arbitrarily stale but decryptable checkpoint could appear fresh.
- Added stale-remote-commit regression test (`tests/test_real_checkpoint_age.py`), with no network dispatch expected when it is expired. The check must pass GitHub CI before considering automatic chaining.
- IMPORTANT: no job-to-job dispatch wired into hosted jobs; 24/7 and original official V3 are still unimplemented; main workflow and live R4 unchanged.
