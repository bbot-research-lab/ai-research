"""Opt-in supervised frame job with durable Git checkpoint callback.

This module is not an official V3 candidate validator. The remote must be
checked out and authenticated by the caller; no live trading operations.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys

from .frame_supervisor import supervise
from .checkpoint_publish_guard import prepare_checkpoint
from .structure_proposals import FRAMES

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frame",required=True,choices=FRAMES)
    p.add_argument("--root",required=True)
    p.add_argument("--worktree",required=True)
    p.add_argument("--max-seconds",type=int,default=19800)
    p.add_argument("--checkpoint-seconds",type=int,default=600)
    p.add_argument("--grace-seconds",type=int,default=1200)
    p.add_argument("command",nargs=argparse.REMAINDER)
    a=p.parse_args()
    if a.max_seconds > 19800 or a.max_seconds <= a.grace_seconds:
        p.error("invalid hosted execution budget")
    key=os.environ["BBOT_RESEARCH_STATE_KEY"]
    worktree=Path(a.worktree)
    branch="synthetic-frame-state-"+a.frame
    def publish(frame, snapshot_dir):
        index=prepare_checkpoint(frame,snapshot_dir,key,worktree)
        def git(*args):
            return subprocess.run(["git","-C",str(worktree),*args],check=True,
                                  capture_output=True,text=True)
        git("add","--","frames/"+frame+".json","objects/")
        changed=subprocess.run(["git","-C",str(worktree),"diff","--cached","--quiet"],
                               check=False,capture_output=True)
        if changed.returncode not in (0,1):
            raise RuntimeError("cannot inspect staged checkpoint")
        if changed.returncode==1:
            git("commit","-m","Periodic encrypted frame checkpoint "+frame)
        # Credentials are supplied to git by the invoking workflow environment.
        git("push","origin","HEAD:refs/heads/"+branch)
        # Independent remote read-back verifies the committed index.
        import tempfile,hashlib
        from .frame_remote_git import checkout_frame
        from .git_frame_checkpoint import restore_frame
        from .frame_snapshot import verify_snapshot
        with tempfile.TemporaryDirectory() as temp:
            mirror=Path(temp)/"remote"
            if not checkout_frame(git("remote","get-url","origin").stdout.strip(),frame,mirror):
                raise RuntimeError("checkpoint not found at remote")
            restored=Path(temp)/"restored"
            if not restore_frame(frame,key,mirror,restored):
                raise RuntimeError("remote checkpoint restore failed")
            original=verify_snapshot(snapshot_dir)
            for name,meta in original["files"].items():
                data=(restored/name).read_bytes()
                if len(data)!=meta["size"] or hashlib.sha256(data).hexdigest()!=meta["sha256"]:
                    raise RuntimeError("remote checkpoint differs from source")
    command=a.command[1:] if a.command[:1]==["--"] else a.command
    if not command:
        p.error("research command is required")
    sys.exit(supervise(command,frame=a.frame,root=a.root,
                       snapshots=str(Path(a.root)/"_snapshots"),
                       max_seconds=a.max_seconds,
                       checkpoint_seconds=a.checkpoint_seconds,
                       grace_seconds=a.grace_seconds,
                       checkpoint_callback=publish))
if __name__=="__main__":
    main()
