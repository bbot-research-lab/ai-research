"""Content-addressed, encrypted per-frame checkpoint index.

Transport-independent: callers upload immutable ciphertext and index atomically
through an authenticated remote store. No GitHub credentials or network in here.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from .encrypted_frame_transport import file_identity, seal, unseal
from .structure_proposals import FRAMES

def publish_bundle(frame, snapshot_dir, key, object_dir):
    if frame not in FRAMES:
        raise ValueError("invalid frame")
    data = seal(frame, snapshot_dir, key)
    meta = file_identity(data)
    dest = Path(object_dir)
    dest.mkdir(parents=True, exist_ok=True)
    object_path = dest / (meta["sha256"] + ".enc")
    if object_path.exists():
        if object_path.read_bytes() != data:
            raise ValueError("hash collision or corrupt object")
    else:
        import os
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=dest, prefix=".blob-")
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, object_path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    return {"schema": "BBOT_FRAME_OBJECT_INDEX_V1", "frame": frame,
            "object": meta["sha256"], "size": meta["size"]}

def recover_bundle(index, object_dir, key, target):
    if index.get("schema") != "BBOT_FRAME_OBJECT_INDEX_V1" or index.get("frame") not in FRAMES:
        raise ValueError("invalid frame object index")
    digest = index.get("object")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid object digest")
    blob = (Path(object_dir) / (digest + ".enc")).read_bytes()
    if hashlib.sha256(blob).hexdigest() != digest or len(blob) != index.get("size"):
        raise ValueError("object integrity failure")
    unseal(index["frame"], blob, key, target)
