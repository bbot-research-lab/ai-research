# B-BOT research import boundary

Upload **research-only source** after review. Do not upload the full local archive.

Excluded from public repository:
- Runtime state, results, logs, trade/account records, exchange snapshots and historical live DBs.
- API keys, credentials, bot tokens, ssh config, machine-specific paths and IPs.
- Live order/execution modules, server synchronization scripts, deployment scripts until separately audited.
- Raw candle datasets when licensing, size or confidentiality is uncertain.

Required before enabling scheduled research:
1. Reconstruct original import tree under strategy_lab.
2. Audit Python modules and configuration files for secrets and privileged side effects.
3. Replace Windows paths and scheduled-task/locking dependencies without changing research rules.
4. Validate official research controller -> formal backtester -> evidence gates end-to-end.
5. Persist checkpoints across runner shutdown.
6. Only then enable scheduled Actions. EC2 production deployment remains disabled pending dry-run.

This repository currently has **no production research scheduler**. No test-run inference is permission to trade.
