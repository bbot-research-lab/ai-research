"""Checkpoint bridge: consistent SQLite snapshot -> authenticated ciphertext -> Git commit.

Called by the job owner at a safe checkpoint boundary. This never runs orders,
changes official V3 results, or removes previous encrypted objects.
"""
from __future__ import annotations
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


