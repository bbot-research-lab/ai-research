"""Fail-closed local verification before publishing encrypted frame objects.

Remote Git push and durable round-trip must be checked separately by workflow.
No plaintext trial data is placed under the remote Git worktree.
"""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .git_frame_checkpoint import stage_frame, restore_frame
from .frame_snapshot import verify_snapshot
from .structure_proposals import FRAMES

def prepare_checkpoint(frame, local_snapshot, key, remote_worktree):
    if frame not in FRAMES:
        raise ValueError("unknown frame")
    source_manifest = verify_snapshot(local_snapshot)
    index = stage_frame(frame, local_snapshot, key, remote_worktree)
    with TemporaryDirectory() as directory:
        if not restore_frame(frame, key, remote_worktree, directory):
            raise ValueError("staged state missing")
        # Check the staged ciphertext really roundtrips to the same database
        # and same progress bytes as the source; not merely to valid ciphertext.
        from .experiment_ledger import ExperimentLedger
        with ExperimentLedger(Path(directory) / "training_ledger.sqlite3") as ledger:
            if ledger.count() < 0:
                raise ValueError("invalid restored ledger")
        import hashlib
        for name, record in source_manifest["files"].items():
            restored = (Path(directory) / name).read_bytes()
            if len(restored) != record["size"] or hashlib.sha256(restored).hexdigest() != record["sha256"]:
                raise ValueError("snapshot roundtrip mismatch")
    return index
