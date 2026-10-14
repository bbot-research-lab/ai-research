# Formal runner dependency blocker: six strategy materials

Inspected the original official `run_strategy.py`: `main()` calls `load_material_modules()` unconditionally after loading the cache and strategy. That function imports six files from `BBOT_LOCAL_ROOT/assist/strategies/`:

- macd.py, stoch.py, shape.py, div.py, obv.py, sar.py

The two uploaded ZIP archives contain the official runner, current strategy, gate engine and Parquet cache, but **none of these six material modules**. Installing `pyarrow` alone is therefore insufficient for complete execution. The original full backtest cannot be certified until these modules are available and their behavior is validated.

This check is read-only; no original data or source is published, no research thresholds are tightened, and the AWS R4 service remains untouched.
