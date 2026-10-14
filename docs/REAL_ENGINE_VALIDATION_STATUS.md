# Reproduction gates for original B-BOT formal backtester

## Confirmed from user-provided archives
- `strategy_lab/lab_config.json` has `schema: STRATEGY_LAB_CONFIG_V4`, `mode: EXACT_SIGNAL_CACHE`, `auto_deploy: false`, and `data_file: C:\\my\\bottest\\gate_lab_exact_long_cache.parquet`.
- `run_strategy.py` supports `BBOT_LOCAL_ROOT` and loads `gate_lab_fast.py` dynamically.
- Official engine+cache supplied in the second ZIP, but neither is in this public repository.
- This CI uses **synthetic** test Parquet generated at runtime with pyarrow; it validates plumbing, not official signals or profitability.

## Reasons actual strategy research is still blocked
1. The original research import tree (including official material modules and strategies) has not been published as an audited full dependency closure.
2. The exact signal cache has not been provided to an isolated runner. Its contents and disclosure rights must be audited before any public upload.
3. No Windows versus Linux exact engine baseline comparison was performed.
4. Original V3 governance and promotion stages are not wired to the additive GA/Optuna module.
5. Persistent state workflow is only a manual diagnostic and has not been confirmed in real Actions.

## Next verifiable result
Run `Research CI (synthetic data only)`; inspect every test result, then fix any regressions.
Do NOT enable scheduled research or live strategy application from these tests alone.
