import tempfile
import unittest
from pathlib import Path

from research_addon.structure_proposals import Structure, propose_structures
from research_addon.experiment_ledger import ExperimentLedger, fingerprint
from research_addon.frame_progress import save_progress, load_progress


class MultiFrameFoundationTests(unittest.TestCase):
    def test_proposals_deterministic_and_unique(self):
        first = propose_structures("6h", seed=9, count=60)
        second = propose_structures("6h", seed=9, count=60)
        self.assertEqual([x.identity() for x in first],
                         [x.identity() for x in second])
        self.assertEqual(len(set(x.identity() for x in first)), 60)
        self.assertTrue(all(x.frame == "6h" for x in first))

    def test_forbidden_and_invalid_structure(self):
        first = propose_structures("1h", count=1)[0]
        second = propose_structures("1h", count=1,
                                    forbidden=frozenset({first.identity()}))
        self.assertNotEqual(first.identity(), second[0].identity())
        with self.assertRaises(ValueError):
            Structure("1h", "trend", ("unknown",), "atr_trailing")
        with self.assertRaises(ValueError):
            propose_structures("wrong", count=1)

    def test_terminal_history_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "6h" / "ledger.sqlite3"
            key = fingerprint(structure={"family": "trend"}, params={"a": 1},
                              frame="6h", symbols=["BTCUSDT"],
                              data_version="data1", rules_version="rules1",
                              code_version="code1")
            different = fingerprint(structure={"family": "trend"}, params={"a": 1},
                                    frame="6h", symbols=["BTCUSDT"],
                                    data_version="data2", rules_version="rules1",
                                    code_version="code1")
            self.assertNotEqual(key, different)
            with ExperimentLedger(path) as ledger:
                self.assertTrue(ledger.record(identity=key, frame="6h",
                    status="FAILED", spec={"a": 1}, outcome={"reason": "failed gate"}))
                self.assertFalse(ledger.record(identity=key, frame="6h",
                    status="COMPLETED", spec={"a": 2}, outcome={"reason": "overwrite"}))
                self.assertEqual(ledger.count(), 1)
            with ExperimentLedger(path) as restored:
                self.assertEqual(restored.get(key)["status"], "FAILED")
                self.assertEqual(restored.get(key)["outcome"]["reason"], "failed gate")

    def test_independent_frames_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            for frame in ("30m", "6h"):
                checkpoint = Path(tmp) / frame / "progress.json"
                save_progress(checkpoint, frame=frame, cursor="trial-42",
                              completed=42, generation=3)
                self.assertEqual(load_progress(checkpoint, frame=frame)["completed"], 42)
                with self.assertRaises(ValueError):
                    load_progress(checkpoint, frame="wrong")
            self.assertIsNone(load_progress(Path(tmp) / "1w/progress.json", frame="1w"))


if __name__ == "__main__":
    unittest.main()
