import json
import tempfile
import unittest
from pathlib import Path
from research_addon.checkpoint_store import load, record_trial, save, signature

class CheckpointTests(unittest.TestCase):
    def test_restart_dedup(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"state"/"checkpoint.json"
            state=load(path)
            self.assertTrue(record_trial(state, {"x":0.3}, "TRAIN_EVALUATED", 1.2))
            self.assertFalse(record_trial(state, {"x":0.3}, "TRAIN_EVALUATED", 1.2))
            save(path,state)
            restarted=load(path)
            self.assertEqual(restarted["completed_trials"],1)
            self.assertEqual(len(restarted["records"]),1)
    def test_bad_checkpoint_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"state.json"
            path.write_text(json.dumps({"schema":"WRONG","records":{},"completed_trials":0}))
            with self.assertRaises(ValueError): load(path)
    def test_live_approval_forbidden(self):
        s=load(Path("/nonexistent-checkpoint-for-unit-test-only"))
        with self.assertRaises(ValueError): record_trial(s, {"x":1}, "AUTO_APPROVED")
    def test_signature_order_independent(self):
        self.assertEqual(signature({"a":1,"b":2}),signature({"b":2,"a":1}))

if __name__ == "__main__":
    unittest.main()
