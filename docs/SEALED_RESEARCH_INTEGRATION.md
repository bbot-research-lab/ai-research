# Historical future-window split — research-only protection

The existing B-BOT `strategy_lab/run_strategy.py` is **not** a standalone optimization objective. In the user ZIP it reads `strategy_lab/lab_config.json`; `data_file` points to a Windows-local `gate_lab_exact_long_cache.parquet`. The runner depends on `gate_lab_fast.py`, which is **not part of the uploaded ZIP**. Its header explicitly says portfolio compound/MDD, WF/OOS and regime evaluation are handled by later portfolio simulation rather than the runner itself.

This repository adds `research_addon/sealed_windows.py`:
- Deterministic, immutable UTC training and sealed-period plan with stable signature.
- Non-overlapping chronological training/sealed windows with embargo.
- Reject non-UTC timestamps, duplicate/out-of-order timestamps, and empty window.
- Only `training_rows()` may feed genetic/Optuna objective.
- `sealed_rows()` exists **only** for an independent evaluator of already-frozen candidates.

**Not yet implemented:** validated official backtester adapter, look-ahead-safe bar execution/next-bar fills, portfolio ledger/MDD, a formal sealed-evidence one-time evaluation registry, checkpoints across GitHub runners, publishing approved artifacts, or AWS ingestion.

Do not treat this module or its toy-unit tests as proof of reliable financial research or enable any production trading.
