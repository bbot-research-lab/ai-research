import base64
from pathlib import Path
import subprocess
import tempfile
import unittest

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_git_sync import stage_and_commit
from research_addon.git_frame_checkpoint import restore_frame

KEY = base64.b64encode(b"s" * 32).decode()

class FrameGitSyncTests(unittest.TestCase):
    def test_commit_and_roundtrip_against_local_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            worktree = base / "git"
            worktree.mkdir()
            def git(*args):
                subprocess.run(["git", "-C", str(worktree), *args],
                               check=True, capture_output=True)
            git("init")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            (worktree / "README.md").write_text("test")
            git("add", "README.md")
            git("commit", "-m", "init")
            root = base / "research"
            with ExperimentLedger(root / "6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="trial1", frame="6h", status="FAILED",
                              spec={"a": 1}, outcome={"reason": "synthetic"})
            index = stage_and_commit("6h", root, worktree, KEY)
            self.assertEqual(index["frame"], "6h")
            self.assertTrue((worktree / "objects" / (index["object"] + ".enc")).is_file())
            self.assertTrue(restore_frame("6h", KEY, worktree, base / "restored"))
            with ExperimentLedger(base / "restored/training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.count(), 1)
            with self.assertRaises(ValueError):
                stage_and_commit("1h", root, worktree, KEY)

if __name__ == "__main__":
    unittest.main()
