# Actual 18-strategy embedded-code dependency inspection — 2026-10-14

Source: uploaded `BBOT_RESEARCH_UPLOAD.zip`, inspected offline through `zipfile` and Python `ast`; original strategy source was not executed, edited or uploaded.

## Actual measured results

- Re-developed strategy files: **18**.
- Python string payloads longer than 100 characters that were successfully parsed as Python AST: **18**, exactly one per file.
- All 18 strategy modules use `numpy`, `sys`, and `types` in their outer or embedded code.
- `pandas` appears in 7 strategy files, counting outer + parseable embedded source.
- `exec` and `compile` calls appear in each of 18 wrappers; `get` appears in all 18.
- No direct calls named `open`, `system`, `run`, `Popen`, `read_csv`, `read_parquet`, `to_csv`, `to_parquet`, `request`, or `post` were detected among the outer and parsed embedded ASTs examined.
- All parseable embedded payloads passed AST syntax parsing.

## Limits and next gate

The counted names are AST-level, not proof of behavior or an exhaustive secret scan. `get` is a common dictionary operation and not by itself evidence of network requests. Recursive/mutated dynamic Python or functions imported later can have effects the scan does not expose.

**Do not remove or refactor the `exec` wrappers** before proving identical execution; they may be how the original research reconstructs candidate strategy functions. Do not tighten legacy scoring thresholds.

Next requirements for formal parity: privately stage exact engine/strategy dependencies; run identical frozen-case baseline on Windows and Linux with verified source+cache hashes; record identical signals, order/fill accounting, fees, and exit semantics; only then connect GA/Optuna.

No strategy source or cached market data is published through this report. No AWS or R4 changes.
