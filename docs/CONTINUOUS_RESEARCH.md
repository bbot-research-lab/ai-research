# Continuous original strategy research
## Implemented
The public workflow `.github/workflows/continuous-research.yml` invokes the supplied canonical `strategy_lab/research_controller.py --mode loop --enable-research`. It uses the original Stage10 manager, candidate selection, existing checkpoints, full validation and sealed blind stages. It does not replace the original simulator or scoring criteria.

An isolated persistent self-hosted runner with labels `self-hosted, bbot-research` is required. PowerShell 7 and an existing research virtualenv must be installed once. Private original sources, signal cache, candle files, constitution and original results stay in the persistent research workspace. No checkout, workspace deletion, result upload, trading keys or AWS access are added.

Repository variables: `BBOT_RESEARCH_ROOT` is the absolute isolated research workspace; `BBOT_RESEARCH_ENABLED=true` enables execution only after original preflight and baseline validation. Keep it unset until then. Every 15 minutes GitHub offers another run, with one writer and no cancellation of the current run. Each invocation runs up to 240 original controller cycles and is limited to 350 minutes. This is repeated scheduling, not a guarantee of uninterrupted 24-hour service. Long work may hit the job limit; the original checkpoint/lock recovery must be validated before enablement.

Original constitution validation and managed dry-run are required before research. Research uses `B_BOT_V3_SERVER_PUSH_HOLD=1` and `BBOT_AUTO_RESEARCH_MANAGER_V1=1`; automatic promotion is not enabled. Workflow output suppresses original private result JSON. Inspect research state locally on the isolated runner.

## Actual verification and remaining blockers
Workflow YAML and embedded Python syntax were verified, along with canonical controller invocation, single-writer scheduling and absence of public artifact uploads. **No actual controller cycle, 24-hour run or blind approval was verified.**

The supplied upload has no top-level `ROADMAP_CONSTITUTION_V3.json`; only historical backup copies were observed. They are not substituted for the authoritative current constitution. Original root kernel/config files and complete current point-in-time research state must also be available in the isolated workspace. The existing public repository does not include the original private dependency/data tree. Runner inventory access is unavailable through the current connection, so an attached suitable runner is not confirmed.

This workflow stays disabled by default. Production R4, live orders, existing thresholds and production symbol count are unchanged. Research's new 30-symbol universe is not retroactively relabeled as the frozen 35-symbol signal cache.
