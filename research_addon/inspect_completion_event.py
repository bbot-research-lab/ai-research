"""Read-only completion handoff inspection. Never dispatches a workflow."""
import argparse
import json
import os
from pathlib import Path
from .completed_run_handoff import eligible_completion
from .verified_previous_run import verify_predecessor
from .verified_frame_job import verify_frame_job
from .remote_state_checker import check_remote_state
from .structure_proposals import FRAMES

def inspect(payload, token, remote, key):
    run_id=eligible_completion(payload,enabled=True)
    if run_id is None:
        return {"eligible":False,"frames":[]}
    verify_predecessor(run_id,token)
    result=[]
    for frame in FRAMES:
        try:
            verify_frame_job(run_id,frame,token)
        except RuntimeError:
            continue
        state=check_remote_state(frame,remote,key)
        if state.get("verified"):
            result.append({"frame":frame,"hop":state["hop"],"records":state["records"]})
    return {"eligible":True,"frames":result}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--event-file",required=True)
    parser.add_argument("--remote",required=True)
    args=parser.parse_args()
    if os.environ.get("BBOT_SYNTHETIC_CHAIN_ENABLED")=="true":
        raise RuntimeError("inspection-only entrypoint refuses automatic dispatch")
    payload=json.loads(Path(args.event_file).read_text())
    print(json.dumps(inspect(payload,os.environ["GH_TOKEN"],args.remote,
                             os.environ["BBOT_RESEARCH_STATE_KEY"]),sort_keys=True))

if __name__=="__main__":
    main()
