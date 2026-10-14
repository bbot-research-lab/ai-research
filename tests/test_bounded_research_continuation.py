import unittest
from types import SimpleNamespace
from research_addon.bounded_research_continuation import run_iterations

class BoundedContinuationTests(unittest.TestCase):
    def test_restarts_finite_training_batches(self):
        commands = []
        def fake(cmd, **kwargs):
            commands.append(cmd)
            return SimpleNamespace(returncode=0)
        self.assertEqual(run_iterations("6h", "/tmp/example", batches=3, runner=fake), 3)
        self.assertEqual(len(commands), 3)
        self.assertTrue(all("--dry-synthetic" in c for c in commands))

    def test_failure_stops_chain(self):
        counter = []
        def failing(cmd, **kwargs):
            counter.append(cmd)
            return SimpleNamespace(returncode=1)
        with self.assertRaises(RuntimeError):
            run_iterations("1d", "/tmp/example", batches=3, runner=failing)
        self.assertEqual(len(counter), 1)

    def test_unbounded_rejected(self):
        with self.assertRaises(ValueError):
            run_iterations("1h", "/tmp/example", batches=999)

if __name__ == "__main__":
    unittest.main()
