"""Read-only metadata-level check against original run_strategy.py cache contract.

The official loader requires columns ts, symbol, close. This check does not
read signal rows or validate trading outcomes.
"""
from pathlib import Path

REQUIRED_COLUMNS = frozenset({"ts", "symbol", "close"})

def inspect(path):
    import pyarrow.parquet as pq
    cache = Path(path)
    handle = pq.ParquetFile(cache)
    names = set(handle.schema.names)
    missing = sorted(REQUIRED_COLUMNS - names)
    rows = handle.metadata.num_rows
    return {
        "compatible_columns": not missing and rows > 0,
        "missing_columns": missing,
        "rows": rows,
        "row_groups": handle.metadata.num_row_groups,
        "metadata_only": True,
        "full_backtest_validated": False,
    }
