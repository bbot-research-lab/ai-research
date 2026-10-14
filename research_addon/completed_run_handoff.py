"""Validate a *completed* workflow_run event before requesting a next frame job.

GitHub does not consider a workflow completed while its own final step runs.
A distinct workflow_run listener on the default branch must make any handoff.
This file is deliberately pure and performs no dispatch.
"""
from __future__ import annotations
from .restart_gate import FRAMES, MAX_HOPS

EXPECTED="multiframe-persistence-smoke.yml"
FEATURE="feature/research-multiframe-foundation-20261014"

def eligible_completion(event, *, enabled=False):
    if enabled is not True or event.get("action")!="completed":
        return None
    run=event.get("workflow_run") or {}
    if run.get("status")!="completed" or run.get("conclusion")!="success":
        return None
    if run.get("head_branch")!=FEATURE:
        return None
    path=(run.get("path") or "").split("@",1)[0]
    if path!=".github/workflows/"+EXPECTED:
        return None
    repo=run.get("repository") or {}
    if repo.get("full_name")!="bbot-research-lab/ai-research":
        return None
    # A workflow_run event does not authenticate individual frame results.
    # Only an actual Actions jobs API query can authorize each frame.
    rid=run.get("id")
    if type(rid) is not int or rid<=0:
        return None
    return rid

def next_frame_hop(frame, hop):
    if frame not in FRAMES or type(hop) is not int or not (0<=hop<MAX_HOPS):
        return None
    return {"frame":frame,"hop":hop+1}
