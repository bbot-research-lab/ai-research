import base64
import tempfile
import unittest
from pathlib import Path

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_snapshot import snapshot
from research_addon.git_frame_checkpoint import stage_frame, restore_frame

KEY = base64.b64encode(b"x" * 32).decode()

class GitFrameCheckpointTests(unittest.TestCase):
    def test_stage_restore_and_absent_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self.assertFalse(restore_frame("6h", KEY, p / "git", p / "first"))
            with ExperimentLedger(p / "live/training_ledger.sqlite3") as db:
                db.record(identity="candidate", frame="6h", status="FAILED",
                          spec={"candidate": 1}, outcome={"reason": "synthetic"})
            snapshot(p / "live", p / "snapshot")
            index = stage_frame("6h", p / "snapshot", KEY, p / "git")
            repeated = stage_frame("6h", p / "snapshot", KEY, p / "git")
            self.assertEqual(repeated["object"], index["object"])
            self.assertEqual(len(list((p / "git/objects").glob("*.enc"))), 1)
            self.assertTrue(restore_frame("6h", KEY, p / "git", p / "copy"))
            with ExperimentLedger(p / "copy/training_ledger.sqlite3") as db:
                self.assertEqual(db.get("candidate")["status"], "FAILED")
            # Existing encrypted snapshot lacks progress; new state adds it.
            from research_addon.frame_progress import save_progress
            save_progress(p / "live/training_progress.json",
                          frame="6h", cursor="after-first-run", completed=1)
            snapshot(p / "live", p / "snapshot")
            updated = stage_frame("6h", p / "snapshot", KEY, p / "git")
            self.assertNotEqual(updated["object"], index["object"])
            self.assertEqual(len(list((p / "git/objects").glob("*.enc"))), 2)
            with self.assertRaises(ValueError):
                restore_frame("6h", base64.b64encode(b"z" * 32).decode(),
                              p / "git", p / "wrongkey")

if __name__ == "__main__":
    unittest.main()
