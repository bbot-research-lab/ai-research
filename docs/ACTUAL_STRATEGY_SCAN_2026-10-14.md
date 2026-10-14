# Actual uploaded-archive strategy scan (2026-10-14)

Source: user-provided `BBOT_RESEARCH_UPLOAD.zip`, inspected locally without importing, extracting, executing, or publishing strategy source.

The scan counted **20 Python sources** below either `strategy_lab/strategies/` or `strategy_lab/results/v3/redeveloped_strategies/`:
- **18** files under `results/v3/redeveloped_strategies/`: AST syntax parse succeeded; each directly calls `exec` and `compile`. Their ordinary AST imports included `numpy`, `sys`, `types`. Inspect embedded code separately; normal AST imports alone are not a complete dependency audit.
- **2** files under `strategy_lab/strategies/`: `CURRENT_PRODUCTION.py` and `_TEMPLATE.py`; AST parse succeeded, no direct `exec`/`compile` calls detected, imports included numpy/pandas.
- Syntax errors: **0**.
- Unreviewed embedded dynamic payloads: **18**.
- No source was automatically approved for public release. No credentials or code were uploaded with this document.

**Correction:** An earlier message said 18 strategy Python files; 18 counts redeveloped strategies only. Total inspected strategy-related files are 20.

This was a targeted AST inventory, not exhaustive recursive source security analysis, proof of reproducibility, or end-to-end strategy execution. Do not alter local research thresholds, official signal behavior or live R4 server based on this scan.

Next: inspect the embedded source strings for dependencies and secrets, stage exact modules privately for Linux replay, and compare outputs against the unchanged Windows baseline.