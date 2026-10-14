# Local cache inspection (Windows PowerShell, no transfer of rows)

Run from a local PC that has `pyarrow` installed in the B-BOT virtual environment:

```powershell
cd C:\my\bottest
.\.venv\Scripts\python.exe -m pip show pyarrow
.\.venv\Scripts\python.exe -c "import pyarrow.parquet as pq; p=pq.ParquetFile('gate_lab_exact_long_cache.parquet'); print('rows=',p.metadata.num_rows,'row_groups=',p.num_row_groups,'columns=',p.schema.names)"
```

This prints only Parquet metadata. Do not upload account data or the whole cache publicly without reviewing its columns and contents first.
