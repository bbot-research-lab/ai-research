import sys
import tempfile
import unittest
from pathlib import Path
from research_addon.frame_supervisor import supervise
from research_addon.frame_snapshot import verify_snapshot

class SupervisorTests(unittest.TestCase):
    def test_completes_and_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, "-m", "research_addon.training_orchestrator",
                       "--frame", "6h", "--root", str(root / "state"),
                       "--dry-synthetic"]
            result = supervise(command, frame="6h", root=root / "state",
                               snapshots=root / "snapshots", max_seconds=15,
                               grace_seconds=5, checkpoint_seconds=1,
                               poll_seconds=0.1)
            self.assertEqual(result, 0)
            verified = verify_snapshot(root / "snapshots" / "6h")
            self.assertIn("training_ledger.sqlite3", verified["files"])

    def test_remote_callback_follows_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, "-m", "research_addon.training_orchestrator",
                       "--frame", "6h", "--root", str(root / "state"),
                       "--dry-synthetic"]
            delivered = []
            result = supervise(command, frame="6h", root=root / "state",
                               snapshots=root / "snapshots", max_seconds=30,
                               grace_seconds=5, checkpoint_seconds=1,
                               poll_seconds=0.1,
                               checkpoint_callback=lambda frame, directory:
                                   delivered.append(verify_snapshot(directory)))
            self.assertEqual(result, 0)
            self.assertTrue(delivered)
            self.assertTrue(all("training_ledger.sqlite3" in d["files"] for d in delivered))

    def test_invalid_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                supervise(["echo", "x"], frame="6h", root=tmp,
                          snapshots=tmp, max_seconds=5, grace_seconds=5)

if __name__ == "__main__":
    unittest.main()
