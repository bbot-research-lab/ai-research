# Formal backtester input integrity gate

User archive `BBOT_MISSING_FILES.zip` examined locally (2026-10-14):

- `gate_lab_fast.py`: 90,743 bytes; SHA256 `78d38775b8d741de0a57027962b1820eb37d94087771e1358fe24d93ba5a6c9d`; valid Python AST.
- `gate_lab_exact_long_cache.parquet`: 13,616,772 bytes; SHA256 `b47837c09b8672c9b420cf80fe37fcaba80fd61f2b6aeee8e03a6ceaa74833e3`; begins/ends `PAR1`.
- This indicates a Parquet container but **does not verify its schema, data values, trading validity, or row count**.
- No raw content uploaded to this public repository.
- `research_addon/cache_integrity.py` provides fail-closed file presence, SHA256 and Parquet magic checks before any future authorized local research execution.
- This pins **one specific snapshot**. Future cache updates must be versioned and reviewed; treating any changed cache as valid without revalidation is prohibited.
- GitHub source unit tests use synthetic fixtures, not actual market history.

Blockers to live automated research: review confidentiality of exact-signal cache; supply isolated runner input through a controlled storage channel; verify schema, strategy/data dependencies, official full backtest reproduction and sealed OOS checks. No Actions schedule or EC2 trading deployment.
