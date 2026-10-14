import unittest
from research_addon.sealed_windows import WindowPlan,training_rows,sealed_rows
class BoundaryTests(unittest.TestCase):
    def plan(self):
        return WindowPlan("2020-01-01T00:00:00Z","2022-01-01T00:00:00Z",
            "2022-02-01T00:00:00Z","2023-01-01T00:00:00Z",embargo_seconds=86400)
    def rows(self):
        return [{"open_time":s,"value":i} for i,s in enumerate([
            "2019-01-01T00:00:00Z","2020-01-01T00:00:00Z",
            "2021-12-31T23:00:00Z","2022-01-01T00:00:00Z",
            "2022-02-01T00:00:00Z","2022-12-31T23:00:00Z",
            "2023-01-01T00:00:00Z"])]
    def test_sealed_not_reachable_from_training(self):
        self.assertEqual([r["value"] for r in training_rows(self.rows(),self.plan())],[1,2])
        self.assertEqual([r["value"] for r in sealed_rows(self.rows(),self.plan())],[4,5])
    def test_embargo_and_overlap_rejected(self):
        with self.assertRaises(ValueError):
            WindowPlan("2020-01-01T00:00:00Z","2022-01-01T00:00:00Z",
                "2022-01-01T12:00:00Z","2023-01-01T00:00:00Z",86400)
    def test_non_utc_and_duplicate_rejected(self):
        with self.assertRaises(ValueError): training_rows([{"open_time":"2020-01-01"}],self.plan())
        with self.assertRaises(ValueError): training_rows(self.rows()[:2]+self.rows()[1:2],self.plan())
    def test_signature_reproducible(self): self.assertEqual(self.plan().signature(),self.plan().signature())
if __name__ == "__main__":unittest.main()
