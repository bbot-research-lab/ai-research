"""Continue ORIGINAL V3 pending validation, never invent PASS or grades.

Runs only original v3_strategy_research functions against its persisted queue.
No deployment, orders, simulated evidence fabrication, or state reset.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

def main():
    root=Path(os.environ["BBOT_LOCAL_ROOT"])
    sys.path.insert(0,str(root/"strategy_lab"))
    import v3_governance as governance
    import v3_strategy_research as research
    if not governance.validate_constitution().get("ok"):
        raise SystemExit("ORIGINAL_GOVERNANCE_INVALID")
    if os.environ.get("B_BOT_V3_SERVER_PUSH_HOLD")!="1":
        raise SystemExit("RESEARCH_HOLD_REQUIRED")
    receipts=[]
    for i in range(12):
        research.sync_new_pipeline_entries()
        before=research.pipeline_work_status()
        if before.get("full_validation_pending",0):
            stage="FULL_VALIDATION"
            fn=research.run_full_validation_one
        elif before.get("blind_prepare_pending",0):
            stage="SEALED_BLIND_PREPARE"
            fn=research.prepare_sealed_final_blind_one
        elif before.get("blind_evaluation_pending",0):
            stage="SEALED_BLIND_EVALUATE"
            fn=research.run_sealed_final_blind_one
        else:
            print("ORIGINAL_VALIDATION_QUEUE_EMPTY="+json.dumps(before,sort_keys=True),flush=True)
            break
        result=fn()
        after=research.pipeline_work_status()
        row={"cycle":i+1,"stage":stage,"status":(result.get("status") if isinstance(result,dict) else "UNSPECIFIED"),"before":before,"after":after}
        receipts.append(row)
        print("ORIGINAL_VALIDATION_STEP="+json.dumps(row,sort_keys=True,default=str),flush=True)
        if not isinstance(result,dict):
            raise SystemExit("ORIGINAL_VALIDATION_RESULT_MISSING")
        if str(result.get("status","")).upper() in ("RUNTIME_FAIL","RUN_STRATEGY_FAIL","RESULT_NOT_FOUND","SOURCE_MISSING"):
            raise SystemExit("ORIGINAL_VALIDATION_INFRASTRUCTURE_FAILURE")
    dest=root/"strategy_lab/results/v3/hosted_validation_continuation.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"schema":"BBOT_ORIGINAL_VALIDATION_CONTINUATION_V1","steps":receipts,"official_grade_assigned":False},indent=2,sort_keys=True,default=str),encoding="utf-8")
    print("ORIGINAL_VALIDATION_CONTINUATION_STEPS="+str(len(receipts)),flush=True)

if __name__=="__main__":
    main()
