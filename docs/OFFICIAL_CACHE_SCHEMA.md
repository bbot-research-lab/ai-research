# Original formal-cache column contract

Source: official user-provided `strategy_lab/run_strategy.py` lines 306–331, inspected in `BBOT_RESEARCH_UPLOAD.zip`.

The official `load_cache(path)` uses `pandas.read_parquet(path)` and explicitly requires **`ts`, `symbol`, `close`** columns. It then coerces timestamps and closing prices to numeric, uppercases symbols, drops invalid rows, and casts timestamps to integer.

An earlier GitHub synthetic Parquet fixture used `open_time` instead of `ts`. The fixture was corrected and a negative schema test was added; passing generic Parquet roundtrips alone is not evidence of original-runner compatibility.

`research_addon/formal_cache_schema.py` checks the actual column names and row count using PyArrow metadata, without reading trading rows. Run it in a private isolated Linux worker after input validation. This is *not* sufficient for real backtest parity or no-lookahead guarantees.

No original strategy or cache uploaded to this public repository; no live bot changes and no altered local scoring thresholds.
