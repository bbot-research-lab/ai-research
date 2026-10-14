# Official B-BOT research execution blockers — inspected 2026-10-14

Observed directly in the user-uploaded `BBOT_RESEARCH_UPLOAD.zip`:
- The archive includes `strategy_lab/run_strategy.py` and `strategy_lab/lab_config.json`.
- Configuration uses `mode: EXACT_SIGNAL_CACHE` and `data_file: C:\\my\\bottest\\gate_lab_exact_long_cache.parquet`.
- The official runner explicitly requires `gate_lab_fast.py` and reads that signal cache.
- **Neither `gate_lab_fast.py` nor `gate_lab_exact_long_cache.parquet` is in the uploaded ZIP.**
- No `.parquet` file was present in the archive at all.

The uploaded source alone therefore **cannot run the original formal research backtest** on a GitHub Actions Linux runner. The added `input_readiness.py` checks mandatory input files and fails closed. It is only a static presence check, not functional validation.

## Remediation before enabling periodic research
1. Obtain an audited copy of the formal `gate_lab_fast.py` engine from the user's **local** project.
2. Resolve how the exact long signal cache is built and kept current. Large cache files should not be pushed into a public Git branch by default.
3. Reproduce the formal runner on Linux using non-sensitive research data. Inspect all dependencies and side effects.
4. Compare results against an existing local baseline for the same dataset/configuration.
5. Preserve original governance/WF/OOS/sealed checks. Only after validated end-to-end operation connect GA/Optuna.
6. Scheduled research, AWS pull and live deployment remain **disabled**.

All archived data requires redaction review before public distribution.
