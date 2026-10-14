"""Validate the exact completed timeframe job of a predecessor workflow.

A green matrix workflow is insufficient when the requested frame did not run.
No dispatch or network side-effects beyond reading the supplied Actions jobs.
"""
from __future__ import annotations
import json
from urllib.request import Request, urlopen
from .restart_gate import FRAMES

REPOSITORY="bbot-research-lab/ai-research"

def verify_frame_job(run_id, frame, token, *, opener=urlopen):
    if frame not in FRAMES or type(run_id) is not int or run_id <= 0 or not token:
        raise ValueError("invalid run/frame/credential")
    url=f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}/jobs?per_page=100"
    req=Request(url,headers={"Authorization":"Bearer "+token,
                             "Accept":"application/vnd.github+json",
                             "User-Agent":"bbot-synthetic-frame-job-verifier"})
    with opener(req,timeout=15) as res:
        payload=json.load(res)
    if payload.get("total_count",0)>100:
        raise RuntimeError("unexpected job count; refuse incomplete verification")
    matches=[j for j in payload.get("jobs",[])
             if j.get("name")==f"synthetic-frame ({frame})"]
    if len(matches)!=1 or matches[0].get("status")!="completed" or matches[0].get("conclusion")!="success":
        raise RuntimeError("approved frame job did not complete successfully")
    steps=matches[0].get("steps",[])
    needed=("Restore authenticated frame before training",
            "Commit encrypted state to isolated branch")
    for name in needed:
        if not any(s.get("name")==name and s.get("conclusion")=="success" for s in steps):
            raise RuntimeError("required checkpoint step not successful")
    return True
