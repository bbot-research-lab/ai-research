"""Default-off completed-run listener entrypoint.

Runs only when installed in a separate trusted workflow on the default branch.
Does not automatically restart research when imported or invoked without an
explicit opt-in variable. Never executes a trading command.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

from .completed_run_handoff import eligible_completion
from .verified_previous_run import verify_predecessor
from .verified_frame_job import verify_frame_job
from .dispatch_next_research import dispatch_next
from .restart_gate import FRAMES

def handle_event(payload, *, enabled, token, state_checker, dispatcher=dispatch_next):
    run_id=eligible_completion(payload,enabled=enabled)
    if run_id is None:
        return []
    verify_predecessor(run_id,token)
    outcomes=[]
    for frame in FRAMES:
        try:
            verify_frame_job(run_id,frame,token)
        except RuntimeError:
            continue  # A frame not present in this run must not restart.
        state=state_checker(frame)
        if not isinstance(state,dict) or not state.get("verified"):
            continue
        result=dispatcher(frame=frame,job_result="success",
                          checkpoint_verified=True,enabled=True,
                          completed_hops=state["hop"],last_checkpoint_at=state["timestamp"],
                          token=token)
        if result is not None:
            outcomes.append(result)
    return outcomes

def main():
    if os.environ.get("BBOT_SYNTHETIC_CHAIN_ENABLED")!="true":
        print("CHAIN_DISABLED")
        return
    raise RuntimeError("Listener is not deployed: a trusted remote checkpoint state_checker is required")

if __name__=="__main__":
    main()
