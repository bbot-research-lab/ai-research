# GitHub-hosted original strategy research
## Actual status — 2026-10-14
GitHub run 38532165730 on main commit 19a3f9011e46ee0ff2c9e178a0a67b63e7fe3121 was actually executed. Input connection checks, dependency installation, authenticated encrypted source download/decryption, and original research state restoration all succeeded. The original governance preflight failed before a research action began. No official strategy result, WF/OOS, blind approval, baseline equality, live application or 24-hour operation is claimed.

Exact blocker: strategy_lab/v3_governance.py line 1013 calls server_runtime.get("role"), while the provided R5 final ROADMAP_CONSTITUTION_V3.json stores continuous_operation_pipeline.server_runtime as a string. The failure is AttributeError: 'str' object has no attribute 'get'. The rules were not downgraded, replaced with an old backup or changed to invented scheduler weights. A matching authoritative current local constitution/source contract is still needed.

## Original identity and accumulated history
1023 uploaded Python files were compared byte-for-byte against BBOT_RESEARCH_UPLOAD.zip: zero changed. The original roadmap_manager.py -> research_controller.py path is preserved. The input pack combines the user's original research ZIP, engine/cache ZIP, strategy module ZIP, provided core archive and provided strategy configuration; it includes the separately supplied ROADMAP_CONSTITUTION_V3_R5_final.json under the canonical name. This assembly is not proof of equality with the user's current complete local filesystem.
The archived trial ledger has 337 entries, including 334 COMPLETED events. Existing results, rejected work and blind consumption records are retained, not initialized from zero.

Original deduplication was tested with fixtures against the unmodified knowledge module: completed rejected candidate/timeframe/kind cannot be reserved again, including after module reload. A distinct timeframe remains separate. Hosted transport tests verified source identity, authenticated original seed, cumulative chunked-state restore, exact mtime restoration and corruption/empty-state rejection. These are targeted tests, not actual strategy research.

## Connected input transport
The user expressly approved publishing ciphertext in the public research repository and placing its decryption key in Actions secrets.
Release: research-inputs-20261014, asset source.enc, AES-256-GCM, authenticated context BBOT_RESEARCH_SOURCE_V1. SHA256: 375d60eb5aff058f4201191d74260916d833051348208048c1a29b39f1befef1.
Configured and visibly verified: secrets BBOT_RESEARCH_SOURCE_URL and BBOT_RESEARCH_STATE_KEY; variable BBOT_RESEARCH_SOURCE_SHA256. No plaintext key, original ZIP or private result JSON is committed or publicly uploaded.

## Hosted execution and persistence
GitHub supplies windows-latest workers; the user's PC and self-hosted runners are not required. Windows retains original C:\\my\\bottest paths and msvcrt locking. Source is restored privately to that path. Original rules and managed preflight are checked before invoking the unchanged original roadmap_manager.py for one bounded action.

The schedule requests work every 15 minutes only when BBOT_RESEARCH_READY=true. That readiness variable is not enabled while the original governance preflight is failing, preventing repeated known-invalid executions. Manual and source-change verification are allowed. GitHub scheduling and 350-minute job limits cannot guarantee continuous uninterrupted execution.

On first run only, absent research-state uses the authenticated original uploaded seed and verifies existing ledger hash/count; failed remote lookup never permits an empty reset. Later runs require a valid authenticated encrypted state manifest and all ciphertext parts. State timestamps are restored only when hash and size match, preserving original signature inputs.
After an actual research action starts, state under original strategy_lab/results is encrypted with BBOT_RESEARCH_STATE_V1 and split into 30 MiB parts on research-state. Non-forced push and workflow serialization prevent conflicting writers. No checkpoint was published from the failed governance preflight. Remote persistence, long-run retention, interruption recovery and real-cycle dedup remain to be verified in real Actions.

## Production boundary
Authoritative production plan: hans1177/binance-bot/docs/BBOT_RESEARCH_BUILD_PLAN_2026-10-14.md.
Goal: GitHub researches -> EC2 pulls approved results at 06:00 KST -> existing signed/versioned validation and SHADOW/CANARY/SMALL/NORMAL release procedure. GitHub receives no SSH/AWS/trading credentials and does not push to EC2. The uploaded local strategy_runtime_sync.ps1 is an SSH push routine, not a GitHub result receiver.
EC2 daily receiver, production feedback import, signed result publication and live promotion remain unimplemented/unverified. R4, existing positions and pass criteria were not changed. The new 30-symbol universe is not a relabeling of the old frozen 35-symbol exact cache.
