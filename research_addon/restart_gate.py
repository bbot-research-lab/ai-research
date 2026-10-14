"""Fail-closed budget and eligibility for future GitHub research job chaining.

Pure policy only: does not dispatch workflows or enable schedules.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

FRAMES = ("30m", "1h", "6h", "12h", "1d", "1w")
MAX_HOPS = 48
MAX_AGE_SECONDS = 6 * 3600

def can_continue(*, frame, job_result, checkpoint_verified,
                 enabled, completed_hops, last_checkpoint_at, now=None):
    if frame not in FRAMES:
        raise ValueError("unsupported frame")
    if not isinstance(completed_hops, int) or isinstance(completed_hops, bool):
        raise ValueError("invalid hop counter")
    if completed_hops < 0 or completed_hops >= MAX_HOPS:
        return False
    if enabled is not True or checkpoint_verified is not True:
        return False
    if job_result != "success":
        return False
    if not isinstance(last_checkpoint_at, str):
        return False
    try:
        stamp = datetime.fromisoformat(last_checkpoint_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if stamp.tzinfo is None:
        return False
    current = now or datetime.now(timezone.utc)
    seconds = (current - stamp).total_seconds()
    return 0 <= seconds <= MAX_AGE_SECONDS

def next_hop(*, frame, job_result, checkpoint_verified,
             enabled, completed_hops, last_checkpoint_at, now=None):
    if not can_continue(frame=frame, job_result=job_result,
                        checkpoint_verified=checkpoint_verified,
                        enabled=enabled, completed_hops=completed_hops,
                        last_checkpoint_at=last_checkpoint_at, now=now):
        return None
    return {"frame": frame, "hop": completed_hops + 1}
