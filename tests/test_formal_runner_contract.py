import json
import tempfile
import unittest
from pathlib import Path
from research_addon.formal_runner_contract import inspect_official_runner

class FormalRunnerContractTests(unittest.TestCase):
    def test_missing_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            x = inspect_official_runner(tmp)
            self.assertFalse(x["ready"])
            self.assertFalse(x["execution_enabled"])
            self.assertIn("gate_lab_fast.py", x["missing_files"])

    def test_static_contract_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"strategy_lab").mkdir()
            (root/"strategy_lab/run_strategy.py").write_text(
                'import os\nROOT=os.getenv("BBOT_LOCAL_ROOT")\n'
                'def main():\n    raise SystemExit("strategy file required")\n'
            )
            (root/"strategy_lab/lab_config.json").write_text(json.dumps({"data_file":"fixture.pkl"}))
            (root/"gate_lab_fast.py").write_text("# fixture\n")
            x=inspect_official_runner(tmp)
            self.assertTrue(x["ready"])
            self.assertFalse(x["execution_enabled"])

if __name__ == "__main__":
    unittest.main()
