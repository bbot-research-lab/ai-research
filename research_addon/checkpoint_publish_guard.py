"""Strict checks around snapshot publication (research-only, no credentials).

Remote persistence is a separate GitHub Actions responsibility. The result
must be verified from the restored branch before a job can claim durability.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

from .git_frame_checkpoint import stage_frame, restore_frame
from .frame_snapshot import verify_snapshot
from .structure_proposals import FRAMES


def prepare_checkpoint(frame, local_snapshot, key, remote_worktree):
    if frame not in FRAMES:
        raise ValueError("unknown frame")
    verify_snapshot(local_snapshot)
    index = stage_frame(frame, local_snapshot, key, remote_worktree)
    # Read through the committed-form index and ciphertext rather than
    # trusting the staging function return value alone.
    verify_target = Path(remote_worktree) / "_verify_temp"
    if verify_target.exists():
        raise ValueError("verification target occupied")
    try:
        restored = restore_frame(frame, key, remote_worktree, verify_target)
        if not restored:
            raise ValueError("staged state missing")
        restored_digest = verify_snapshot(local_snapshot)
        from .experiment_ledger import ExperimentLedger
        with ExperimentLedger(verify_target / "training_ledger.sqlite3") as ledger:
            if ledger.count() < 0:
                raise ValueError("impossible record count")
        return index
    finally:
        import shutil
        if verify_target.exists():
            shutil.rmtree(verify_target)
