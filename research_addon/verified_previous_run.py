"""Verify the real predecessor GitHub Actions run before allowing a handoff.

The caller-supplied result string is not authoritative. A completed successful
run on the approved feature ref is required; token is never logged.
"""
from __future__ import annotations
import json
from urllib.request import Request, urlopen

REPO="bbot-research-lab/ai-research"
REF="feature/research-multiframe-foundation-20261014"

def verify_predecessor(run_id, token, *, opener=urlopen):
    if isinstance(run_id,bool) or not isinstance(run_id,int) or run_id<=0:
        raise ValueError("invalid previous run ID")
    if not isinstance(token,str) or not token:
        raise ValueError("GitHub credential required")
    req=Request(f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}",
                headers={"Authorization":"Bearer "+token,
                         "Accept":"application/vnd.github+json",
                         "User-Agent":"bbot-research-run-verifier"})
    with opener(req,timeout=15) as res:
        data=json.load(res)
    if data.get("status")!="completed" or data.get("conclusion")!="success":
        raise RuntimeError("previous GitHub workflow has not succeeded")
    if data.get("head_branch")!=REF or data.get("repository",{}).get("full_name")!=REPO:
        raise RuntimeError("wrong GitHub run identity")
    if data.get("path","").split("@",1)[0] != ".github/workflows/multiframe-persistence-smoke.yml":
        raise RuntimeError("previous run used an unapproved workflow")
    if data.get("event") not in ("push","workflow_dispatch"):
        raise RuntimeError("unapproved GitHub run event")
    return True
