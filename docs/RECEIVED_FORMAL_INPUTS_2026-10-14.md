# Received official engine and signal cache (2026-10-14)

Source: user-provided `BBOT_MISSING_FILES.zip`. **The archive itself is not committed.**

| Input | Uncompressed bytes | SHA-256 |
|---|---:|---|
| `gate_lab_fast.py` | 90,743 | `78d38775b8d741de0a57027962b1820eb37d94087771e1358fe24d93ba5a6c9d` |
| `gate_lab_exact_long_cache.parquet` | 13,616,772 | `b47837c09b8672c9b420cf80fe37fcaba80fd61f2b6aeee8e03a6ceaa74833e3` |

Static check of `gate_lab_fast.py`: Python AST syntax PASS, imported libraries include numpy and pandas, and no obvious hard-coded key or Windows absolute drive paths found by preliminary scanning. This is **not** a comprehensive supply-chain/security certification.

Engine describes comparative single/paired strategy signal experiments (MACD, STOCH, SHAPE, DIV, EMA_CROSS, OBV, SAR) with portfolio-type summaries. The cache is a Parquet data file and likely includes derived signal inputs.

**Not verified:** Parquet schema/rows, full test execution, research controller entrypoint end-to-end, sealed future validation, or reference performance equality. The auditing environment did not have `pyarrow`; dependency installation was unavailable. GitHub can install it separately.

## Next steps
1. Validate Parquet schema and data consistency in an isolated CI diagnostic or local environment. Do not expose the cache publicly by default.
2. Verify the official engine, strategy modules, and formal runner in a complete isolated Linux working tree.
3. Compare outputs against the user's prior local baseline with identical configuration.
4. Only after successful validation integrate GA and Optuna and enable periodic research.

All production trading and AWS deployment remain disabled.
