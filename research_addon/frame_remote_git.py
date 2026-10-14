"""Git remote frame checkpoint lifecycle; local/bare Git remotes supported.

Synthetic frame state only. Auth is caller-provided via Git's credential
environment. No network credentials, live strategy code, or production orders.
"""
from __future__ import annotations
import subprocess
from pathlib import Path

from .structure_proposals import FRAMES
from .git_frame_checkpoint import restore_frame
from .frame_git_sync import stage_and_commit


def _git(*args, cwd=None, allowed=(0,)):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode not in allowed:
        raise RuntimeError("Git checkpoint operation failed")
    return result


def branch_name(frame):
    if frame not in FRAMES:
        raise ValueError("unsupported frame")
    return "synthetic-frame-state-" + frame


def checkout_frame(remote, frame, worktree):
    branch = branch_name(frame)
    worktree = Path(worktree)
    if worktree.exists():
        raise ValueError("worktree already exists")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    # The independent frame worktree is a regular clone, never a shared index.
    result = _git("ls-remote", "--exit-code", "--heads", str(remote),
                  "refs/heads/" + branch, allowed=(0, 2))
    if result.returncode == 0:
        _git("clone", "--quiet", "--single-branch", "--branch", branch,
             str(remote), str(worktree))
        return True
    # First run: no remote branch is NOT a reset if this branch was expected.
    # Caller must explicitly authorize initial seed creation.
    _git("init", "--quiet", str(worktree))
    _git("remote", "add", "origin", str(remote), cwd=worktree)
    _git("checkout", "--orphan", branch, cwd=worktree)
    return False


def commit_and_push(frame, root, worktree, key, *, allow_initial_seed=False):
    branch = branch_name(frame)
    worktree = Path(worktree)
    state_exists = (worktree / "frames" / (frame + ".json")).is_file()
    if not state_exists and not allow_initial_seed:
        raise ValueError("missing remote state: refusing implicit reset")
    _git("config", "user.name", "github-actions[bot]", cwd=worktree)
    _git("config", "user.email",
         "41898282+github-actions[bot]@users.noreply.github.com", cwd=worktree)
    index = stage_and_commit(frame, root, worktree, key)
    _git("push", "origin", "HEAD:refs/heads/" + branch, cwd=worktree)
    # Refetch and verify saved remote state in a separate worktree.
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        other = Path(tmp) / "remote-checkout"
        if not checkout_frame("origin" if False else _remote_url(worktree), frame, other):
            raise RuntimeError("remote frame checkpoint missing after push")
        if not restore_frame(frame, key, other, Path(tmp) / "restored"):
            raise RuntimeError("remote state could not be restored")
    return index


def _remote_url(worktree):
    return _git("remote", "get-url", "origin", cwd=worktree).stdout.strip()
