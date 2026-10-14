import unittest
from research_addon.candidate_search import Range, genetic_candidates

class SearchTests(unittest.TestCase):
    def test_reproducible_bounded(self):
        bounds = {"a": Range(0, 1), "b": Range(-2, 2)}
        objective = lambda p: -(p["a"] - .4)**2 - (p["b"] - .7)**2
        a = genetic_candidates(bounds, objective, seed=9, generations=4)
        b = genetic_candidates(bounds, objective, seed=9, generations=4)
        self.assertEqual(a, b)
        self.assertTrue(all(0 <= x["params"]["a"] <= 1 for x in a))
        self.assertTrue(all(-2 <= x["params"]["b"] <= 2 for x in a))
    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            genetic_candidates({}, lambda _: 0)

if __name__ == "__main__": unittest.main()
