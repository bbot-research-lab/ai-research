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

if __name__ == "__main__":
    unittest.main()
