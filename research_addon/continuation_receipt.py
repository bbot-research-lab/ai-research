"""Durable bounded continuation hop receipt stored inside encrypted checkpoints.

The receipt is untrusted until the containing AES-GCM checkpoint is authenticated.
Never infer the hop from a local default when a remote checkpoint exists.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from .restart_gate import FRAMES, MAX_HOPS

NAME="continuation_hop.json"
SCHEMA="BBOT_SYNTHETIC_CONTINUATION_V1"

def read_hop(directory,frame,*,require_existing=False):
    if frame not in FRAMES: raise ValueError("invalid frame")
    path=Path(directory)/NAME
    if not path.exists():
        if require_existing: raise ValueError("missing persisted hop")
        return 0
    record=json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema")!=SCHEMA or record.get("frame")!=frame:
        raise ValueError("wrong continuation receipt")
    hop=record.get("hop")
    if type(hop) is not int or not 0<=hop<=MAX_HOPS:
        raise ValueError("invalid continuation count")
    return hop

def write_hop(directory,frame,hop,*,expected_previous=None):
    if frame not in FRAMES or type(hop) is not int or not 0<=hop<=MAX_HOPS:
        raise ValueError("invalid frame or continuation count")
    directory=Path(directory)
    if expected_previous is not None:
        current=read_hop(directory,frame,require_existing=True)
        if current!=expected_previous or hop!=current+1:
            raise ValueError("nonmonotonic continuation count")
    directory.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=".hop-",dir=directory)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump({"schema":SCHEMA,"frame":frame,"hop":hop},f,sort_keys=True)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,directory/NAME)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
