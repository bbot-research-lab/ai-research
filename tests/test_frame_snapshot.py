import tempfile
import unittest
from pathlib import Path

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_progress import save_progress
from research_addon.frame_snapshot import snapshot, verify_snapshot, restore_snapshot


class FrameSnapshotTests(unittest.TestCase):
    def test_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "original"
            with ExperimentLedger(frame / "training_ledger.sqlite3") as ledger:
                ledger.record(identity="identity-1", frame="6h", status="FAILED",
                              spec={"structure": "trend"}, outcome={"reason": "synthetic"})
            save_progress(frame / "training_progress.json",
                          frame="6h", cursor="done", completed=1)
            snapshot(frame, root / "snapshot")
            self.assertEqual(verify_snapshot(root / "snapshot")["schema"],
                             "BBOT_FRAME_SNAPSHOT_V1")
            restore_snapshot(root / "snapshot", root / "restored")
            with ExperimentLedger(root / "restored/training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.get("identity-1")["status"], "FAILED")
                self.assertEqual(ledger.count(), 1)
            with self.assertRaises(ValueError):
                restore_snapshot(root / "snapshot", root / "restored")
            with open(root / "snapshot/training_progress.json", "ab") as stream:
                stream.write(b"tamper")
            with self.assertRaises(ValueError):
                verify_snapshot(root / "snapshot")


if __name__ == "__main__":
    unittest.main()
