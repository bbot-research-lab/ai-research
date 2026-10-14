# Local-vs-GitHub research config parity gate

This gate is based on the user's uploaded `strategy_lab/lab_config.json` dated 2026-10-14. It compares original values *without changing research pass/fail thresholds*.

Original:
- `schema = STRATEGY_LAB_CONFIG_V4`
- `mode = EXACT_SIGNAL_CACHE`
- `auto_deploy = false`, `auto_test = true`
- `fee_rate = 0.0005`, leverage range `1..50`, leverage testing disabled
- research candidate target `8`
- timeframes `30M/1H/6H/12H/1D/1W/1M`
- `1M` reference-only; research fill timeframes exclude `1M`
- `data_file` path may change to Linux but must refer to `gate_lab_exact_long_cache.parquet`

To run after staging (not publishing) the source:

```bash
python -m research_addon.local_config_parity /path/to/research/strategy_lab/lab_config.json
```

**Not an end-to-end parity proof:** Same config does not mean same signals, data, evidence, WF/OOS, portfolio simulation, exit management or approvals. A real official backtest comparison remains required. Public scheduling and R4 live deployment remain disabled.
