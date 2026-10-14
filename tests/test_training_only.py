import unittest
from research_addon.training_only import TrainOnlyObjective
from research_addon.sealed_windows import WindowPlan
from research_addon.candidate_search import Range, genetic_candidates

PLAN=WindowPlan("2020-01-01T00:00:00Z","2021-01-01T00:00:00Z",
                "2021-02-01T00:00:00Z","2022-01-01T00:00:00Z")
def rows(future_price):
    return [
        {"open_time":"2020-04-01T00:00:00Z","price":2},
        {"open_time":"2020-07-01T00:00:00Z","price":4},
        {"open_time":"2021-04-01T00:00:00Z","price":future_price},
    ]
def objective(source, params):
    return -(params["x"]-sum(r["price"] for r in source)/6)**2

class TrainOnlyTests(unittest.TestCase):
    def test_sealed_future_change_cannot_affect_search(self):
        a=TrainOnlyObjective(rows(-10000),PLAN,objective)
        b=TrainOnlyObjective(rows(+10000),PLAN,objective)
        self.assertEqual(a.train_count,2)
        self.assertEqual(a.window_signature,b.window_signature)
        assert a({"x":.5})==b({"x":.5})
        x=genetic_candidates({"x":Range(0,2)},a,seed=7,population=8,generations=3)
        y=genetic_candidates({"x":Range(0,2)},b,seed=7,population=8,generations=3)
        self.assertEqual(x,y)
    def test_train_data_cannot_be_modified_across_trials(self):
        def mutation_attempt(source, params):
            source[0]["price"] = 9999
            return source[0]["price"]
        obj=TrainOnlyObjective(rows(5),PLAN,mutation_attempt)
        self.assertEqual(obj({"x":1}),9999)
        self.assertEqual(obj({"x":1}),9999)
        self.assertEqual(obj.train_count,2)
    def test_nonfinite_score_rejected(self):
        obj=TrainOnlyObjective(rows(5),PLAN,lambda *_:float("nan"))
        with self.assertRaises(ValueError): obj({"x":1})

if __name__=="__main__":
    unittest.main()
