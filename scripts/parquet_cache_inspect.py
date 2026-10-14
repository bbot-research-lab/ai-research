"""Read-only Parquet metadata inspection; prints only summary (not raw data rows)."""
import argparse
import hashlib
import json
from pathlib import Path

def inspect(path: Path):
    import pyarrow.parquet as pq
    meta = pq.ParquetFile(path)
    if meta.metadata.num_rows <= 0:
        raise ValueError("empty cache")
    return {
        "file_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "num_rows": meta.metadata.num_rows,
        "row_groups": meta.metadata.num_row_groups,
        "column_names": [str(name) for name in meta.schema.names],
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("parquet_path", type=Path)
    a = p.parse_args()
    print(json.dumps(inspect(a.parquet_path), indent=2, ensure_ascii=False))
