import json
import tempfile
import unittest
from pathlib import Path
from research_addon.local_config_parity import REQUIRED, inspect

class ConfigParityTests(unittest.TestCase):
    def cfg(self, obj):
        temp=tempfile.TemporaryDirectory()
        path=Path(temp.name)/"lab_config.json"
        path.write_text(json.dumps(obj),encoding="utf-8")
        self.addCleanup(temp.cleanup)
        return path
    def baseline(self):
        return {**REQUIRED, "data_file":r"C:\my\bottest\gate_lab_exact_long_cache.parquet"}
    def test_local_configuration_matches(self):
        self.assertTrue(inspect(self.cfg(self.baseline()))["matches_local_baseline"])
    def test_no_silent_criteria_change(self):
        for key, value in [
            ("fee_rate", 0.0001), ("research_candidate_fill_target", 12),
            ("timeframes", ["1H"]), ("auto_deploy", True), ("mode", "SYNTHETIC")
        ]:
            with self.subTest(key=key):
                changed=self.baseline()
                changed[key]=value
                self.assertFalse(inspect(self.cfg(changed))["matches_local_baseline"])
                self.assertIn(key,inspect(self.cfg(changed))["differences"])
    def test_path_can_change_to_linux_but_cache_identity_preserved(self):
        changed=self.baseline()
        changed["data_file"]="/opt/research/gate_lab_exact_long_cache.parquet"
        self.assertTrue(inspect(self.cfg(changed))["matches_local_baseline"])
    def test_missing_field_fails(self):
        changed=self.baseline()
        del changed["leverage_min"]
        self.assertFalse(inspect(self.cfg(changed))["matches_local_baseline"])

if __name__=="__main__": unittest.main()
