"""Operator-gated migration of a synthetic encrypted remote frame state.

Preserves the original immutable encrypted blob in Git history, verifies its
experiment records, then publishes a new authenticated checkpoint. This tool
must never be run against official V3 state or without stopped frame writers.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from .frame_remote_git import checkout_frame,commit_and_push
from .git_frame_checkpoint import restore_frame
from .migrate_legacy_frame import migrate_legacy_frame
from .experiment_ledger import ExperimentLedger
from .structure_proposals import FRAMES

def migrate_remote(frame,remote,key,*,operator_approved=False,expected_remote_sha=None):
    if operator_approved is not True:
        raise PermissionError("migration requires explicit operator approval")
    if not isinstance(expected_remote_sha,str) or len(expected_remote_sha)!=40 or any(ch not in "0123456789abcdef" for ch in expected_remote_sha):
        raise ValueError("exact audited remote SHA is required")
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        branch=root/"remote"
        if not checkout_frame(remote,frame,branch):
            raise ValueError("remote legacy state missing; refusing reset")
        current=subprocess.run(["git","-C",str(branch),"rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
        if current != expected_remote_sha:
            raise RuntimeError("remote checkpoint changed since approved audit")
        live=root/"state"/frame
        if not restore_frame(frame,key,branch,live):
            raise ValueError("remote legacy checkpoint missing")
        ledger_path=live/"training_ledger.sqlite3"
        before_digest=hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        with ExperimentLedger(ledger_path) as ledger:
            before=ledger.count()
        result=migrate_legacy_frame(frame,live,operator_approved=True)
        if not result["migrated"]:
            return result
        # Existing commit remains in Git history and the old encrypted blob
        # remains content-addressed, so migration never destroys the original.
        after_digest=hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        if before_digest!=after_digest:
            raise RuntimeError("migration modified existing experiment ledger bytes")
        commit_and_push(frame,root/"state",branch,key)
        verify=root/"second"
        if not checkout_frame(remote,frame,verify):
            raise RuntimeError("migration publication missing")
        recovered=root/"confirmed"
        if not restore_frame(frame,key,verify,recovered):
            raise RuntimeError("migration restore failed")
        from .continuation_receipt import read_hop
        if read_hop(recovered,frame,require_existing=True)!=0:
            raise RuntimeError("incorrect migrated continuation count")
        if hashlib.sha256((recovered/"training_ledger.sqlite3").read_bytes()).hexdigest()!=before_digest:
            raise RuntimeError("remote migration changed experiment ledger bytes")
        with ExperimentLedger(recovered/"training_ledger.sqlite3") as ledger:
            if ledger.count()!=before:
                raise RuntimeError("migration lost experiment records")
        return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frame",required=True,choices=FRAMES)
    p.add_argument("--remote",required=True)
    p.add_argument("--approve-synthetic-migration",action="store_true")
    p.add_argument("--expected-remote-sha",required=True)
    args=p.parse_args()
    key=os.environ["BBOT_RESEARCH_STATE_KEY"]
    print(migrate_remote(args.frame,args.remote,key,
                         operator_approved=args.approve_synthetic_migration,
                         expected_remote_sha=args.expected_remote_sha))
if __name__=="__main__":
    main()
