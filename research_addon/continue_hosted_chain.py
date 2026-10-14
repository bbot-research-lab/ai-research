"""Opt-in controller for a bounded synthetic GitHub continuation.

No implicit workflow recursion: requires an explicit enabling environment
variable and remote state verified by an independent Git refetch.
"""
import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from .dispatch_next_research import dispatch_next
from .frame_remote_git import checkout_frame
from .git_frame_checkpoint import restore_frame
from .frame_snapshot import verify_snapshot
from .remote_frame_objects import recover_bundle
from .structure_proposals import FRAMES

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--frame",choices=FRAMES,required=True)
    parser.add_argument("--hop",type=int,required=True)
    parser.add_argument("--remote",required=True)
    parser.add_argument("--result",choices=("success","failure"),required=True)
    args=parser.parse_args()
    allowed=os.environ.get("BBOT_SYNTHETIC_CHAIN_ENABLED")=="true"
    if not allowed:
        print("CHAIN_DISABLED")
        return 0
    key=os.environ["BBOT_RESEARCH_STATE_KEY"]
    token=os.environ["GH_TOKEN"]
    with TemporaryDirectory() as temp:
        worktree=Path(temp)/"remote"
        if not checkout_frame(args.remote,args.frame,worktree):
            raise RuntimeError("cannot chain without a remote checkpoint")
        state=Path(temp)/"restored"
        if not restore_frame(args.frame,key,worktree,state):
            raise RuntimeError("cannot chain without verified state")
        # Independently read the full snapshot; malformed remote state aborts.
        from .experiment_ledger import ExperimentLedger
        with ExperimentLedger(state/"training_ledger.sqlite3") as ledger:
            if ledger.count()<0:
                raise RuntimeError("invalid research ledger")
        # Compare ciphertext content to its remote index and authenticate the
        # restored ledger; do not treat missing or corrupt metadata as success.
        index_path=worktree/"frames"/(args.frame+".json")
        import json, hashlib
        index=json.loads(index_path.read_text(encoding="utf-8"))
        if index["frame"] != args.frame or not (worktree/"objects"/(index["object"]+".enc")).is_file():
            raise RuntimeError("invalid remote frame checkpoint index")
    # A freshly verified remote checkpoint is the checkpoint authorization.
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    hop=dispatch_next(frame=args.frame,job_result=args.result,
                      checkpoint_verified=True,enabled=True,
                      completed_hops=args.hop,last_checkpoint_at=now,
                      token=token)
    print("DISPATCHED="+str(hop) if hop else "CHAIN_STOPPED")
    return 0

if __name__=="__main__":
    sys.exit(main())
