"""Safe remote checkpoint operations using a caller-managed Git worktree.

A remote branch must have a SINGLE writer per timeframe. Git never receives plaintext.
All remote Git I/O is deliberately handled by the workflow, not this module.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import tempfile

from .remote_frame_objects import publish_bundle, recover_bundle
from .structure_proposals import FRAMES

def stage_frame(frame, snapshot_dir, key, worktree):
    if frame not in FRAMES:
        raise ValueError("unrecognized frame")
    worktree = Path(worktree)
    objects = worktree / "objects"
    index = publish_bundle(frame, snapshot_dir, key, objects)
    # The index contains no strategy data, only encrypted blob reference.
    index_dir = worktree / "frames"
    index_dir.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix=".index-", dir=index_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(index, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(path, index_dir / (frame + ".json"))
    finally:
        if os.path.exists(path):
            os.unlink(path)
    return index

def restore_frame(frame, key, worktree, destination):
    if frame not in FRAMES:
        raise ValueError("unrecognized frame")
    worktree = Path(worktree)
    index_path = worktree / "frames" / (frame + ".json")
    if not index_path.is_file():
        return False  # first run only; caller MUST verify authorized seed policy
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("frame") != frame:
        raise ValueError("wrong frame index")
    recover_bundle(index, worktree / "objects", key, destination)
    return True
