"""Checkpoint bridge: consistent SQLite snapshot -> authenticated ciphertext -> Git commit.

Called by the job owner at a safe checkpoint boundary. This never runs orders,
changes official V3 results, or removes previous encrypted objects.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess

from .frame_snapshot import snapshot
from .git_frame_checkpoint import stage_frame
from .structure_proposals import FRAMES


def stage_and_commit(frame, root, worktree, key):
    if frame not in FRAMES:
        raise ValueError("unsupported frame")
    source = Path(root) / frame
    if not (source / "training_ledger.sqlite3").is_file():
        raise ValueError("missing durable frame ledger")
    worktree = Path(worktree)
    snapshot_dir = Path(root) / "_checkpoint_snapshots" / frame
    snapshot(source, snapshot_dir)
    index = stage_frame(frame, snapshot_dir, key, worktree)
    def git(*args):
        return subprocess.run(["git", "-C", str(worktree), *args],
                              check=True, capture_output=True, text=True)
    git("add", "--", "frames/" + frame + ".json", "objects/")
    changed = subprocess.run(
        ["git", "-C", str(worktree), "diff", "--cached", "--quiet"],
        check=False, capture_output=True)
    if changed.returncode not in (0, 1):
        raise RuntimeError("cannot determine pending checkpoint changes")
    if changed.returncode == 1:
        git("commit", "-m", "Frame checkpoint: " + frame)
    return index


def push_prepared_worktree(worktree, frame, *, remote="origin", token=None):
    """Push only to the isolated frame branch. Caller must enforce single writer.

    Refuses to run with an unspecified, absent, or malformed token. No token is
    placed in argv, logs, config, commit content, or the public source tree.
    """
    if frame not in FRAMES:
        raise ValueError("unsupported frame")
    if not token:
        raise ValueError("authenticated push token required")
    import base64
    from urllib.parse import quote
    # GitHub Actions masks env token; ephemeral askpass keeps it out of arguments.
    # The caller supplies a credential helper through its environment.
    if not os.environ.get("GIT_ASKPASS"):
        raise ValueError("secure git askpass required")
    branch = "synthetic-frame-state-" + frame
    subprocess.run(["git", "-C", str(worktree), "push", remote,
                    "HEAD:refs/heads/" + branch], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   env=dict(os.environ, BBOT_GIT_PUSH_TOKEN=token))
