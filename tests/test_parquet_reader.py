"""Public-safe parquet fixture test; no user trading or cache data."""
import tempfile
import unittest
from pathlib import Path

class ParquetReaderTests(unittest.TestCase):
    def test_metadata_and_monotonic_timestamps(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from scripts.parquet_cache_inspect import inspect
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"synthetic.parquet"
            table=pa.table({
                "symbol":["EXAMPLE"]*3,
                "ts": pa.array([1609459200000,1609459260000,1609459320000],type=pa.int64()),
                "close":[1.0,1.1,1.2],
            })
            pq.write_table(table, f)
            data=inspect(f)
            self.assertEqual(data["num_rows"],3)
            self.assertIn("ts",data["column_names"])
            self.assertIn("symbol",data["column_names"])
            self.assertIn("close",data["column_names"])
            self.assertTrue(data["sha256"])
            self.assertEqual(data["file_bytes"],f.stat().st_size)

if __name__ == "__main__":
    unittest.main()
