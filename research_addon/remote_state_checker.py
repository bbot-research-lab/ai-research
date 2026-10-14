"""Independently verify encrypted frame state fetched from a remote Git branch.

No strategy evaluation, dispatch, live trading or mutation occurs here.
"""
from __future__ import annotations
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from .frame_remote_git import checkout_frame
from .git_frame_checkpoint import restore_frame
from .experiment_ledger import ExperimentLedger
from .structure_proposals import FRAMES
from .continuation_receipt import read_hop

def check_remote_state(frame,remote,key):
    if frame not in FRAMES or not key:
        raise ValueError("invalid frame or missing decryption key")
    with TemporaryDirectory() as tmp:
        worktree=Path(tmp)/"git"
        if not checkout_frame(remote,frame,worktree):
            return {"verified":False}
        destination=Path(tmp)/"restored"
        if not restore_frame(frame,key,worktree,destination):
            raise RuntimeError("remote checkpoint missing")
        index=json.loads((worktree/"frames"/(frame+".json")).read_text())
        if index.get("frame")!=frame:
            raise RuntimeError("remote checkpoint points at wrong frame")
        with ExperimentLedger(destination/"training_ledger.sqlite3") as ledger:
            records=ledger.count()
        completed=subprocess.run(["git","-C",str(worktree),"show","-s",
                                  "--format=%cI","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
        timestamp=datetime.fromisoformat(completed)
        if timestamp.tzinfo is None or timestamp>datetime.now(timezone.utc):
            raise RuntimeError("invalid remote checkpoint time")
        hop=read_hop(destination,frame,require_existing=True)
        return {"verified":True,"timestamp":completed,"records":records,"hop":hop}
