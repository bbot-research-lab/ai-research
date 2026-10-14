import struct
import tempfile
import unittest
from pathlib import Path
from research_addon.cache_integrity import sha256_stream,verify

class CacheIntegrityTests(unittest.TestCase):
    def test_missing_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(verify(root)["reason"],"REQUIRED_INPUT_MISSING")
    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            (p/"gate_lab_fast.py").write_text("# toy")
            (p/"gate_lab_exact_long_cache.parquet").write_bytes(b"PAR1helloPAR1")
            self.assertEqual(verify(root)["reason"],"PINNED_SHA256_MISMATCH")
    def test_invalid_footer_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            (p/"gate_lab_fast.py").write_bytes(b"engine")
            (p/"gate_lab_exact_long_cache.parquet").write_bytes(b"PAR1badPAR1")
            x=verify(root,expected_engine=sha256_stream(p/"gate_lab_fast.py"),expected_cache=sha256_stream(p/"gate_lab_exact_long_cache.parquet"))
            self.assertEqual(x["reason"],"PARQUET_FOOTER_INVALID")
    def test_pinned_fixture(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            (p/"gate_lab_fast.py").write_bytes(b"engine")
            (p/"gate_lab_exact_long_cache.parquet").write_bytes(b"PAR1" + b"DATA" + b"M" + struct.pack("<I", 1) + b"PAR1")
            engine=sha256_stream(p/"gate_lab_fast.py")
            cache=sha256_stream(p/"gate_lab_exact_long_cache.parquet")
            self.assertTrue(verify(root,expected_engine=engine,expected_cache=cache)["ok"])
            (p/"gate_lab_exact_long_cache.parquet").write_bytes(b"PAR1badPAR1")
            self.assertFalse(verify(root,expected_engine=engine,expected_cache=cache)["ok"])

if __name__=="__main__":
    unittest.main()
