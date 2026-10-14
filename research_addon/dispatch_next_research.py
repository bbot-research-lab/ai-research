"""Opt-in bounded synthetic workflow handoff through GitHub's dispatch API.

This is never called by an existing production workflow. A caller must pass
the explicit ENABLE flag, verified remote checkpoint and GitHub Actions token.
"""
from __future__ import annotations
import json
import re
from urllib.request import Request, urlopen

from .restart_gate import next_hop

WORKFLOW = "multiframe-persistence-smoke.yml"
REF = "feature/research-multiframe-foundation-20261014"
REPOSITORY = "bbot-research-lab/ai-research"

def dispatch_next(*, frame, job_result, checkpoint_verified, enabled,
                  completed_hops, last_checkpoint_at, token,
                  repository=REPOSITORY, opener=urlopen, now=None):
    hop = next_hop(frame=frame, job_result=job_result,
                   checkpoint_verified=checkpoint_verified, enabled=enabled,
                   completed_hops=completed_hops,
                   last_checkpoint_at=last_checkpoint_at, now=now)
    if hop is None:
        return None
    if repository != REPOSITORY or not isinstance(token, str) or not token:
        raise ValueError("approved repository and token required")
    # GitHub workflow_dispatch accepts a workflow only after GitHub registers
    # it on the default branch; do not silently fall back to repository push.
    endpoint = ("https://api.github.com/repos/" + REPOSITORY +
                "/actions/workflows/" + WORKFLOW + "/dispatches")
    payload = json.dumps({"ref": REF, "inputs": {
        "frame": hop["frame"], "hop": str(hop["hop"])}}).encode()
    request = Request(endpoint, data=payload, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "bbot-research-synthetic-continuation"})
    with opener(request, timeout=15) as response:
        if response.status != 204:
            raise RuntimeError("GitHub did not acknowledge dispatch")
    return hop
