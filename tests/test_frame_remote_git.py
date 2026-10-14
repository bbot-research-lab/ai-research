import base64
import subprocess
import tempfile
import unittest
from pathlib import Path

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame, commit_and_push
from research_addon.git_frame_checkpoint import restore_frame

KEY = base64.b64encode(b"t" * 32).decode()


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


class FrameRemoteGitTests(unittest.TestCase):
    def test_two_consecutive_push_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            git("init", "--bare", str(remote))
            frame_root = root / "data"
            with ExperimentLedger(frame_root / "6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="one", frame="6h", status="FAILED",
                              spec={"trial": 1}, outcome={"reason": "synthetic"})
            first = root / "checkout-1"
            self.assertFalse(checkout_frame(remote, "6h", first))
            with self.assertRaises(ValueError):
                commit_and_push("6h", frame_root, first, KEY)
            commit_and_push("6h", frame_root, first, KEY, allow_initial_seed=True)
            second = root / "checkout-2"
            self.assertTrue(checkout_frame(remote, "6h", second))
            restored = root / "restored"
            self.assertTrue(restore_frame("6h", KEY, second, restored))
            with ExperimentLedger(restored / "training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.count(), 1)
            with ExperimentLedger(frame_root / "6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="two", frame="6h", status="COMPLETED",
                              spec={"trial": 2}, outcome={"score": 1})
            commit_and_push("6h", frame_root, second, KEY)
            third = root / "checkout-3"
            self.assertTrue(checkout_frame(remote, "6h", third))
            self.assertTrue(restore_frame("6h", KEY, third, root / "restored-2"))
            with ExperimentLedger(root / "restored-2/training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.count(), 2)
                self.assertEqual(ledger.get("one")["status"], "FAILED")
                self.assertEqual(ledger.get("two")["status"], "COMPLETED")
            # Repeat same state: no terminal trial is deleted or overwritten.
            commit_and_push("6h", frame_root, third, KEY)
            fourth = root / "checkout-4"
            self.assertTrue(checkout_frame(remote, "6h", fourth))
            self.assertTrue(restore_frame("6h", KEY, fourth, root / "restored-3"))
            with ExperimentLedger(root / "restored-3/training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.count(), 2)

if __name__ == "__main__":
    unittest.main()
