"""Read-only local inspection of the ORIGINAL B-BOT Parquet cache.

Run on the user's Windows B-BOT venv, where pandas + pyarrow are installed.
Prints aggregate schema and counts only; never prints rows/positions/credentials.
Does not import the live bot or run strategies.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

PINNED_SHA256="b47837c09b8672c9b420cf80fe37fcaba80fd61f2b6aeee8e03a6ceaa74833e3"
REQUIRED=("ts","symbol","close")

def inspect(path):
    import pandas as pd
    import pyarrow.parquet as pq
    p=Path(path)
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    digest=h.hexdigest()
    if digest!=PINNED_SHA256:
        return {"ok":False,"reason":"SOURCE_CACHE_SHA256_MISMATCH","sha256":digest}
    parquet=pq.ParquetFile(p)
    columns=set(parquet.schema.names)
    missing=sorted(set(REQUIRED)-columns)
    if missing or parquet.metadata.num_rows==0:
        return {"ok":False,"reason":"SCHEMA_OR_ROWS_INVALID","missing":missing,
                "row_count":parquet.metadata.num_rows}
    # Only read columns used by the original official loader, not arbitrary account fields.
    df=pd.read_parquet(p,columns=list(REQUIRED))
    ts=pd.to_numeric(df["ts"],errors="coerce")
    close=pd.to_numeric(df["close"],errors="coerce")
    symbols=df["symbol"].astype("string").str.strip()
    valid=ts.notna()&close.notna()&symbols.notna()&(symbols.str.len()>0)
    values=ts[valid]
    return {
        "ok":bool(valid.any()),
        "reason":"READ_ONLY_CACHE_COLUMN_CHECK",
        "sha256":digest,
        "row_count":int(len(df)),
        "valid_rows":int(valid.sum()),
        "invalid_rows":int((~valid).sum()),
        "row_groups":int(parquet.metadata.num_row_groups),
        "columns":sorted(columns),
        "timestamp_min":int(values.min()) if len(values) else None,
        "timestamp_max":int(values.max()) if len(values) else None,
        "unique_symbols":int(symbols[valid].nunique()),
        "backtest_executed":False,
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("cache_path",type=Path)
    result=inspect(parser.parse_args().cache_path)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
    sys.exit(0 if result["ok"] else 2)
