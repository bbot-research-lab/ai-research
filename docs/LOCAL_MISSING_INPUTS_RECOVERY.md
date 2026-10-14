# Required local backtester components — safe recovery

The uploaded BBOT_RESEARCH_UPLOAD.zip was rechecked on 2026-10-14. It has `strategy_lab/run_strategy.py`, `strategy_lab/lab_config.json`, `requirements.txt`, but **not**:
- `gate_lab_fast.py` (formal engine)
- `gate_lab_exact_long_cache.parquet` (cache referenced by lab_config)

Before any further migration or Actions scheduling, run the **read-only** local PowerShell inventory below. Do NOT upload the cache or the entire `C:\\my\\bottest` directory publicly. The cache might be large or contain proprietary derived signals. Only report the file path and byte size initially.

```powershell
$root='C:\my\bottest'
Get-ChildItem -LiteralPath $root -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -in @('gate_lab_fast.py','gate_lab_exact_long_cache.parquet') } |
  Select-Object FullName,Length,LastWriteTime |
  Format-Table -AutoSize
```

If `gate_lab_fast.py` exists, inspect it locally for secrets and server calls before sharing in ChatGPT (not directly GitHub). Cache transfer strategy depends on file size and actual content. Neither missing file is synthesized, and real research remains disabled until official backtest results are reproducible.

Important: No changes to the live R4 service or game repositories.
