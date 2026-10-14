import tempfile
import unittest
from research_addon.input_readiness import inspect
from scripts.research_input_preflight import preflight

class PreflightTests(unittest.TestCase):
    def test_missing_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            result = preflight(root)
            self.assertFalse(result["ready"])
            self.assertFalse(result["official_backtest_executed"])
            self.assertFalse(result["production_deploy_allowed"])
            self.assertEqual(result["checks"]["engine_cache_integrity"]["reason"],"REQUIRED_INPUT_MISSING")
    def test_inspector_never_permits_deployment(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertFalse(preflight(root)["production_deploy_allowed"])

if __name__ == "__main__":
    unittest.main()
