import json
import tempfile
import unittest
from pathlib import Path
from research_addon.input_readiness import inspect, NEEDED

class ReadinessTests(unittest.TestCase):
    def test_missing_required_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            result=inspect(td)
            self.assertFalse(result["ready"])
            self.assertIn("gate_lab_fast.py", result["missing"])
            self.assertTrue(result["no_live_deployment"])
    def test_all_required_inputs_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in NEEDED:
                target=root/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text("{}" if name.endswith(".json") else "# mock")
            (root/"strategy_lab/lab_config.json").write_text(
                json.dumps({"data_file":r"C:\my\bottest\gate_lab_exact_long_cache.parquet"}))
            (root/"gate_lab_exact_long_cache.parquet").write_bytes(b"fixture")
            self.assertTrue(inspect(root)["ready"])
    def test_missing_cache_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name in NEEDED:
                target=root/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text("{}" if name.endswith(".json") else "# mock")
            (root/"strategy_lab/lab_config.json").write_text(
                json.dumps({"data_file":"gate_lab_exact_long_cache.parquet"}))
            self.assertIn("research candle cache data_file",inspect(root)["missing"])
    def test_outside_root_data_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"strategy_lab").mkdir()
            (root/"strategy_lab/lab_config.json").write_text(json.dumps({"data_file":"/etc/passwd"}))
            self.assertFalse(inspect(root)["ready"])
            self.assertIn("outside research root", inspect(root)["config_error"])

if __name__ == "__main__":
    unittest.main()
