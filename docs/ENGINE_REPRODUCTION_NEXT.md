# Formal backtest reproducibility: current boundary

Confirmed from the user's uploaded research archive and official-input ZIP:
- Research configuration `strategy_lab/lab_config.json`: `mode = EXACT_SIGNAL_CACHE`, `data_file = C:\\my\\bottest\\gate_lab_exact_long_cache.parquet`.
- `gate_lab_fast.py`: 3,230 lines, importing Python standard libraries plus `numpy` and `pandas`.
- `gate_lab_exact_long_cache.parquet`: 13,616,772 bytes, with SHA-256 pinned in `research_addon/cache_integrity.py`.
- Those two files have **not** been uploaded to this public repository.
- `scripts/research_input_preflight.py` combines the existing readiness, engine contract and hash validation, and **cannot run the backtest or deploy a strategy**.

## To resume
1. Obtain audited, approved input files in an isolated GitHub worker directory (not the public repository). Never put credentials, account DB or confidential results into Actions artifacts.
2. Confirm Parquet schema, signal time range, monotonic timestamps, unique symbols/timeframe combinations and expected read behavior using pyarrow.
3. Validate Linux path resolution and dependencies of `run_strategy.py`, plus all strategy modules it dynamically imports.
4. Compare one identical official backtest on Windows vs Linux, using the same frozen inputs, fees and parameter settings.
5. Only after reproducibility, connect training-only GA/Optuna and sealed OOS evaluators. Continuous schedule still disabled.

This repository remains a research **scaffold**, not a running strategy factory.
