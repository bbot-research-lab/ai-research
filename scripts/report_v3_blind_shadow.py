"""Fail-closed evidence report for original V3 blind-to-shadow readiness.

Does not authorize shadow, alter deployment state or reveal strategy parameters.
Only the original validator's explicit evidence can support promotion.
"""
from __future__ import annotations
import json
from pathlib import Path

STAGES=("WF_OOS","SEALED_FUTURE","SHADOW")

def inspect_evidence(root):
    root=Path(root)
    outcomes={}
    for name in STAGES:
        path=root/"strategy_lab"/"results"/"v3"/"validation"/(name.lower()+".json")
        if not path.is_file():
            outcomes[name]={"state":"NOT_VERIFIED"}
            continue
        try:
            row=json.loads(path.read_text(encoding="utf-8-sig"))
            if (row.get("stage")==name and row.get("verdict")=="PASS"
                and isinstance(row.get("evidence_sha256"),str)
                and len(row["evidence_sha256"])==64):
                outcomes[name]={"state":"EVIDENCE_PRESENT_UNATTESTED"}
            else:
                outcomes[name]={"state":"NOT_VERIFIED"}
        except (OSError,ValueError,TypeError):
            outcomes[name]={"state":"NOT_VERIFIED"}
    # A standalone report must never replace original official approval gates.
    return {"schema":"BBOT_V3_STAGE_OBSERVATION_V1","stages":outcomes,
            "shadow_approved":False,"live_trading_enabled":False}

def main():
    import os
    result=inspect_evidence(os.environ["BBOT_LOCAL_ROOT"])
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as out:
        out.write("## V3 sealed-blind / SHADOW evidence (read-only)\\n")
        for stage,state in result["stages"].items():
            out.write(f"- {stage}: {state['state']}\\n")
        out.write("No independent SHADOW admission or live trading authorization issued.\\n")
    print("V3_STAGE_OBSERVATION="+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
