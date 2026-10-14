import tempfile
import unittest
from research_addon.training_orchestrator import training_batch

def score(structure, params):
    return -(params["threshold"] - 1.0) ** 2

class TrainingTests(unittest.TestCase):
    def test_repeat_and_independent_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            def go(frame):
                return training_batch(
                    frame=frame, root=temp, objective=score, seed=2,
                    structures=1, ga_population=4, ga_generations=1,
                    optuna_trials=2, data_version="synthetic",
                    rules_version="test-only", code_version="v1",
                    symbols=["SYNTHETIC"])
            a = go("6h")
            self.assertGreater(a["new_records"], 0)
            b = go("6h")
            self.assertEqual(b["new_records"], 0)
            self.assertEqual(b["evaluated"], 0)
            c = go("1d")
            self.assertGreater(c["new_records"], 0)

    def test_failure_does_not_poison_ledger(self):
        import sqlite3
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            def broken(structure, params):
                raise RuntimeError("synthetic infrastructure error")
            with self.assertRaises(RuntimeError):
                training_batch(
                    frame="6h", root=temp, objective=broken, seed=2,
                    structures=1, ga_population=4, ga_generations=1,
                    optuna_trials=2, data_version="synthetic",
                    rules_version="test-only", code_version="v1",
                    symbols=["SYNTHETIC"])
            path = Path(temp) / "6h/training_ledger.sqlite3"
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM experiments").fetchone()[0], 0)
            self.assertFalse((Path(temp) / "6h/training_progress.json").exists())

if __name__ == "__main__":
    unittest.main()
