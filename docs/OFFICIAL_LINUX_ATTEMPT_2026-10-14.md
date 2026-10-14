# Actual Linux official-runner execution attempt — 2026-10-14

The user-provided ZIPs were accessed **locally**, not published. The exact original files were staged in a temporary directory with `BBOT_LOCAL_ROOT` set; no AWS access, trading calls or code changes were made.

## Experiment 1: no strategy argument
`python strategy_lab/run_strategy.py`
- Exit code: 1
- Expected message: `strategy file required`
- This confirms the official CLI reaches its argument check on Linux with installed NumPy/Pandas, but **does not** prove that a strategy can be evaluated.

## Experiment 2: original CURRENT_PRODUCTION.py argument
`python strategy_lab/run_strategy.py strategy_lab/strategies/CURRENT_PRODUCTION.py`
- Exit code: 1
- Trace reached `main -> load_cache -> pandas.read_parquet` (source line 313).
- Precise blocker: `ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'`.
- The environment has NumPy and Pandas, but no Parquet engine. Package installation was blocked by the environment's offline dependency source.
- The official backtest **did not begin**; no performance, signals, WF/OOS or historical fills were evaluated.

## Other locally confirmed details
- Original cache size: 13,616,772 bytes.
- Parquet footer metadata byte length: **44,958** (little-endian integer at bytes -8..-5).
- Footer length is not a row count, schema analysis, or data quality validation.

## Required next
1. Install `pyarrow` in a network-enabled isolated Linux test environment (not the production R4 host).
2. Inspect input schema/rows and verify no private or account information before sharing any data.
3. Stage the official material modules and remaining dependencies in that isolated environment.
4. Re-run official current strategy and compare frozen run outputs against the unchanged Windows baseline.
5. Preserve preexisting research pass/fail and promotion criteria. Do not enable auto-deployment until proven equivalent.

**No GitHub Actions PASS or official Linux full-backtest PASS is claimed.**
