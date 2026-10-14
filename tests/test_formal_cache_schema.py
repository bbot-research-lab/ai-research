import tempfile
import unittest
from pathlib import Path

class FormalCacheSchemaTests(unittest.TestCase):
    def test_original_required_columns(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from research_addon.formal_cache_schema import inspect
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"fixture.parquet"
            pq.write_table(pa.table({"ts":[1,2],"symbol":["X","X"],"close":[2.,3.]}),f)
            self.assertTrue(inspect(f)["compatible_columns"])
            self.assertEqual(inspect(f)["missing_columns"],[])
    def test_open_time_is_not_official_ts(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from research_addon.formal_cache_schema import inspect
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/"incorrect.parquet"
            pq.write_table(pa.table({"open_time":[1],"symbol":["X"],"close":[2.]}),f)
            result=inspect(f)
            self.assertFalse(result["compatible_columns"])
            self.assertEqual(result["missing_columns"],["ts"])

if __name__=="__main__":
    unittest.main()
