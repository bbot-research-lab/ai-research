"""Synthetic end-to-end GA/Optuna training against the official-simulator adapter.

No real cache, no strategy approval. Both optimizers receive TRAIN rows only.
"""
import unittest
from research_addon.candidate_search import Range, genetic_candidates, optuna_candidates
from research_addon.formal_simulation_objective import make_trade_objective
from research_addon.sealed_windows import WindowPlan
from research_addon.training_only import TrainOnlyObjective

PLAN=WindowPlan("2020-01-01T00:00:00Z","2021-01-01T00:00:00Z",
                "2021-02-01T00:00:00Z","2022-01-01T00:00:00Z")
def sample(future_close):
    return [
      {"open_time":"2020-01-01T00:00:01Z","ts":1,"close":100.},
      {"open_time":"2020-02-01T00:00:01Z","ts":2,"close":102.},
      {"open_time":"2020-03-01T00:00:01Z","ts":3,"close":105.},
      {"open_time":"2020-04-01T00:00:01Z","ts":4,"close":104.},
      {"open_time":"2020-05-01T00:00:01Z","ts":5,"close":100.},
      {"open_time":"2021-03-01T00:00:01Z","ts":6,"close":future_close},
    ]
def signal(frame, params):
    return [0, 1 if params["x"]>=0.5 else -1, 1 if params["x"]>=0.5 else -1,0,0]

class ExplorationAdapterTests(unittest.TestCase):
    def test_both_optimizers_ignore_future_prices(self):
        def official_sim(frame, signals, fee):
            assert len(frame)==len(signals)==5
            # The adapter calls this as the ORIGINAL simulator function would be called.
            return [{"net_return":float(frame.iloc[-1]["close"]-frame.iloc[1]["close"])/100.0
                    * (1 if signals[1]>0 else -1)-2*fee}]
        evaluator=make_trade_objective(official_sim,signal,fee_rate=.0005)
        left=TrainOnlyObjective(sample(-10000.),PLAN,evaluator)
        right=TrainOnlyObjective(sample(10000.),PLAN,evaluator)
        bounds={"x":Range(0.,1.)}
        self.assertEqual(genetic_candidates(bounds,left,seed=7,population=8,generations=3),
                         genetic_candidates(bounds,right,seed=7,population=8,generations=3))
        self.assertEqual(optuna_candidates(bounds,left,seed=7,trials=8),
                         optuna_candidates(bounds,right,seed=7,trials=8))
        self.assertEqual(left.train_count,5)
if __name__=="__main__":unittest.main()
