"""Run-manifest validation for independent, bounded research chains.

This module does not trigger workflows. Its decisions can be tested before
enabling any unattended GitHub scheduler.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path

from .structure_proposals import FRAMES

SCHEMA = "BBOT_FRAME_RUN_MANIFEST_V1"

def make_manifest(frame, *, head_sha, checkpoint_sha, run_id, started_at,
                  ended_at, status, completed):
    if frame not in FRAMES or status not in ("SUCCESS", "INTERRUPTED", "FAILED"):
        raise ValueError("invalid frame or terminal status")
    if not (isinstance(run_id, int) and run_id > 0 and isinstance(completed, int) and completed >= 0):
        raise ValueError("invalid run counters")
    import re
    if not re.fullmatch(r"[a-f0-9]{40}", head_sha) or not re.fullmatch(r"[a-f0-9]{64}", checkpoint_sha):
        raise ValueError("invalid immutable hash")
    a = dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    b = dt.datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
    if a.tzinfo is None or b.tzinfo is None or b < a:
        raise ValueError("invalid UTC run times")
    return {"schema": SCHEMA, "frame": frame, "head_sha": head_sha,
            "checkpoint_sha": checkpoint_sha, "run_id": run_id,
            "started_at": started_at, "ended_at": ended_at,
            "status": status, "completed": completed}

def eligible_for_resume(manifest, *, current_head_sha, max_age_hours=48):
    if manifest.get("schema") != SCHEMA or manifest.get("frame") not in FRAMES:
        raise ValueError("unknown run manifest")
    if manifest.get("head_sha") != current_head_sha:
        return False
    stamp = dt.datetime.fromisoformat(manifest["ended_at"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    if stamp.tzinfo is None or stamp > now + dt.timedelta(minutes=5):
        raise ValueError("invalid remote timestamp")
    if now - stamp > dt.timedelta(hours=max_age_hours):
        return False
    return manifest["status"] in ("SUCCESS", "INTERRUPTED")
