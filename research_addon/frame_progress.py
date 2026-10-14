"""Atomic per-frame resume markers for bounded hosted research.

Checkpoint only names already committed work; never marks an incomplete trial as done.
State is portable JSON, not a substitute for the original authenticated V3 checkpoint.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile

def save_progress(path, *, frame, cursor, completed, generation=0):
    if not frame or not isinstance(cursor, str) or not isinstance(completed, int) or completed < 0 or generation < 0:
        raise ValueError("invalid resume state")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "BBOT_FRAME_PROGRESS_V1", "frame": frame,
               "cursor": cursor, "completed": completed, "generation": generation}
    fd, temp = tempfile.mkstemp(prefix=".progress-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(payload, out, sort_keys=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def load_progress(path, *, frame):
    target = Path(path)
    if not target.exists():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("schema") != "BBOT_FRAME_PROGRESS_V1" or payload.get("frame") != frame:
        raise ValueError("frame checkpoint mismatch")
    if not isinstance(payload.get("cursor"), str) or type(payload.get("completed")) is not int or payload["completed"] < 0:
        raise ValueError("corrupt checkpoint")
    if type(payload.get("generation")) is not int or payload["generation"] < 0:
        raise ValueError("corrupt generation")
    return payload
