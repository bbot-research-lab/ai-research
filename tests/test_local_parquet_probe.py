import unittest
from scripts.local_parquet_probe import PINNED_SHA256,REQUIRED

class ProbeContractTests(unittest.TestCase):
    def test_original_cache_hash_is_pinned(self):
        self.assertEqual(len(PINNED_SHA256),64)
    def test_official_columns(self):
        self.assertEqual(set(REQUIRED),{"ts","symbol","close"})

if __name__=="__main__":unittest.main()
