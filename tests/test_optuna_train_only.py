"""Synthetic Optuna train-only regression; never runs exchange or official bot."""
import unittest

from research_addon.candidate_search import Range, optuna_candidates
from research_addon.sealed_windows import WindowPlan
from research_addon.training_only import TrainOnlyObjective

PLAN = WindowPlan(
    "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z",
    "2021-02-01T00:00:00Z", "2022-01-01T00:00:00Z"
)

def make_rows(future):
    return [
        {"open_time": "2020-03-01T00:00:00Z", "price": 2.0},
        {"open_time": "2020-06-01T00:00:00Z", "price": 4.0},
        {"open_time": "2021-04-01T00:00:00Z", "price": future},
    ]

def scoring(train, params):
    return -(params["x"] - sum(row["price"] for row in train) / 6.0) ** 2

class OptunaTrainingBoundaryTests(unittest.TestCase):
    def test_future_prices_cannot_change_trials(self):
        left = TrainOnlyObjective(make_rows(-999999), PLAN, scoring)
        right = TrainOnlyObjective(make_rows(+999999), PLAN, scoring)
        self.assertEqual(left.train_count, 2)
        self.assertEqual(right.train_count, 2)
        a = optuna_candidates({"x": Range(0.0, 2.0)}, left, seed=17, trials=12)
        b = optuna_candidates({"x": Range(0.0, 2.0)}, right, seed=17, trials=12)
        self.assertEqual(a, b)

    def test_training_objective_rejects_invalid_score(self):
        obj = TrainOnlyObjective(make_rows(5), PLAN, lambda *_: float("inf"))
        with self.assertRaises(ValueError):
            optuna_candidates({"x": Range(0.0, 2.0)}, obj, seed=17, trials=1)

if __name__ == "__main__":
    unittest.main()
