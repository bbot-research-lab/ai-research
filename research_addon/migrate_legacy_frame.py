"""Explicit one-time migration of legacy *synthetic* frame state.

Must be invoked by an operator while frame writers are stopped. Never edits
existing encrypted object history or assumes a missing receipt is hop zero
during unattended continuation.
"""
from __future__ import annotations
from pathlib import Path

from .continuation_receipt import NAME, read_hop, write_hop
from .experiment_ledger import ExperimentLedger
from .structure_proposals import FRAMES

def migrate_legacy_frame(frame, restored_dir, *, operator_approved=False):
    if frame not in FRAMES:
        raise ValueError("invalid frame")
    if operator_approved is not True:
        raise PermissionError("explicit synthetic migration approval required")
    root=Path(restored_dir)
    if (root/NAME).exists():
        hop=read_hop(root,frame,require_existing=True)
        return {"migrated":False,"hop":hop}
    ledger=root/"training_ledger.sqlite3"
    if not ledger.is_file():
        raise ValueError("existing ledger required; refusing empty reset")
    with ExperimentLedger(ledger) as db:
        before=db.count()
    # A human-approved legacy frame starts a NEW bounded synthetic chain,
    # not a continuation of an untrusted previous hop count.
    write_hop(root,frame,0)
    with ExperimentLedger(ledger) as db:
        after=db.count()
    if after!=before:
        raise RuntimeError("legacy experiment count changed during migration")
    return {"migrated":True,"hop":0,"retained_records":after}
