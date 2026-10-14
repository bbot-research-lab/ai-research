"""Fail-closed idempotency receipt for a synthetic completed-run handoff.

The receipt is only a local claim, not proof of an actual GitHub dispatch.
A failed dispatch must not be retried automatically; operator reconciliation
against GitHub runs is required. Callers must serialize access via a trusted
single-writer GitHub environment or concurrency group.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from .structure_proposals import FRAMES

SCHEMA="BBOT_SYNTHETIC_HANDOFF_CLAIM_V1"

def claim_handoff(directory,*,frame,run_id,hop):
    if frame not in FRAMES or type(run_id) is not int or run_id<=0 or type(hop) is not int or not 0<=hop<48:
        raise ValueError("invalid frame/run/hop")
    root=Path(directory)
    root.mkdir(parents=True,exist_ok=True)
    filename=root/(f"{run_id}-{frame}-{hop}.json")
    claim={"schema":SCHEMA,"run_id":run_id,"frame":frame,"hop":hop,
           "status":"CLAIMED_NEEDS_RECONCILIATION"}
    try:
        fd=os.open(filename,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        existing=json.loads(filename.read_text())
        if existing!=claim:
            raise RuntimeError("handoff claim collision or corruption")
        return False
    with os.fdopen(fd,"w",encoding="utf-8") as out:
        json.dump(claim,out,sort_keys=True)
        out.flush()
        os.fsync(out.fileno())
    return True
