"""Read-only inventory of legacy synthetic frame-state branches.

No state writes, migration, trading, or scheduling. Authenticated decrypt
verifies whether existing research can be migrated without losing records.
"""
from __future__ import annotations
import argparse
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from .frame_remote_git import checkout_frame
from .git_frame_checkpoint import restore_frame
from .continuation_receipt import NAME, read_hop
from .experiment_ledger import ExperimentLedger
from .structure_proposals import FRAMES

def audit(frame,remote,key):
    if frame not in FRAMES: raise ValueError("invalid frame")
    with TemporaryDirectory() as tmp:
        path=Path(tmp)
        worktree=path/"remote"
        if not checkout_frame(remote,frame,worktree):
            return {"frame":frame,"status":"MISSING_REMOTE","records":None}
        destination=path/"state"
        if not restore_frame(frame,key,worktree,destination):
            raise RuntimeError("remote state branch lacks checkpoint")
        with ExperimentLedger(destination/"training_ledger.sqlite3") as ledger:
            count=ledger.count()
        if (destination/NAME).is_file():
            hop=read_hop(destination,frame,require_existing=True)
            status="MIGRATED"
        else:
            hop=None
            status="LEGACY_NEEDS_APPROVED_MIGRATION"
        sha=subprocess.run(["git","-C",str(worktree),"rev-parse","HEAD"],
                           check=True,capture_output=True,text=True).stdout.strip()
        return {"frame":frame,"status":status,"records":count,"hop":hop,"remote_commit":sha}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frame",choices=FRAMES,required=True)
    p.add_argument("--remote",required=True)
    a=p.parse_args()
    result=audit(a.frame,a.remote,os.environ["BBOT_RESEARCH_STATE_KEY"])
    import json
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
