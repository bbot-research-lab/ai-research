"""Synthetic-only verification of periodic checkpoint remote roundtrip."""
import base64
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame, commit_and_push
from research_addon.git_frame_checkpoint import restore_frame

class HostedFrameRunnerTests(unittest.TestCase):
    def test_git_remote_checkpoint_after_supervised_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote = base / "remote.git"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            frame_root = base / "state"
            frame_dir = frame_root / "6h"
            with ExperimentLedger(frame_dir / "training_ledger.sqlite3") as db:
                db.record(identity="prior", frame="6h", status="FAILED",
                          spec={"from": "seed"}, outcome={"reason": "synthetic"})
            worktree = base / "frame-repo"
            self.assertFalse(checkout_frame(remote, "6h", worktree))
            key = base64.b64encode(b"z" * 32).decode()
            commit_and_push("6h", frame_root, worktree, key, allow_initial_seed=True)
            env = dict(os.environ, BBOT_RESEARCH_STATE_KEY=key)
            run = subprocess.run(
                [sys.executable, "-m", "research_addon.hosted_frame_runner",
                 "--frame", "6h", "--root", str(frame_root),
                 "--worktree", str(worktree), "--max-seconds", "30",
                 "--checkpoint-seconds", "1", "--grace-seconds", "5",
                 "--", sys.executable, "-m", "research_addon.training_orchestrator",
                 "--frame", "6h", "--root", str(frame_root),
                 "--dry-synthetic"],
                env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr[-3000:])
            mirror = base / "new-checkout"
            self.assertTrue(checkout_frame(remote, "6h", mirror))
            restored = base / "restore"
            self.assertTrue(restore_frame("6h", key, mirror, restored))
            with ExperimentLedger(restored / "training_ledger.sqlite3") as db:
                self.assertIsNotNone(db.get("prior"))
                self.assertGreater(db.count(), 1)

if __name__ == "__main__":
    unittest.main()
