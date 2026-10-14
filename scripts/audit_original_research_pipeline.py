"""Report only verifiable original V3 research pipeline execution evidence.

Does not create an approval, invoke a simulator, or alter controller criteria.
Only records observed source files and their hashes; never prints private data.
"""
import hashlib
import json
import os
from pathlib import Path

def audit(root):
    root=Path(root)
    sources={
        "controller":"strategy_lab/results/roadmap_status_latest.json",
        "trial_ledger":"strategy_lab/results/v3/trial_ledger.json",
        "deployment":"strategy_lab/results/v3/deployment_state.json",
    }
    report={"schema":"BBOT_ORIGINAL_RESEARCH_PIPELINE_AUDIT_V1","steps":{}}
    parsed={}
    for kind,name in sources.items():
        path=root/name
        if not path.is_file():
            report["steps"][kind]={"state":"MISSING"}
            continue
        raw=path.read_bytes()
        try:
            parsed[kind]=json.loads(raw.decode("utf-8-sig"))
            report["steps"][kind]={"state":"READABLE",
                                   "sha256":hashlib.sha256(raw).hexdigest()}
        except (ValueError,UnicodeError):
            report["steps"][kind]={"state":"INVALID_JSON",
                                   "sha256":hashlib.sha256(raw).hexdigest()}
    ledger=parsed.get("trial_ledger")
    if isinstance(ledger,dict) and isinstance(ledger.get("entries"),list):
        entries=ledger["entries"]
        report["steps"]["trial_persistence"]={"state":"OBSERVED","record_count":len(entries)}
    else:
        report["steps"]["trial_persistence"]={"state":"UNVERIFIED"}
    # Per-frame counts are observations, never proof of a passed evaluation.
    frame_counts={frame:{"records":0,"completed":0,"failed":0} for frame in ("30m","1h","6h","12h","1d","1w")}
    if isinstance(ledger,dict) and isinstance(ledger.get("entries"),list):
        for row in ledger["entries"]:
            if not isinstance(row,dict):
                continue
            frame=str(row.get("timeframe") or "").strip().lower()
            if frame not in frame_counts:
                continue
            frame_counts[frame]["records"]+=1
            if row.get("event")=="COMPLETED":
                frame_counts[frame]["completed"]+=1
                if row.get("status")=="FAIL":
                    frame_counts[frame]["failed"]+=1
    report["frames"]={frame:{**counts,"state":"RECORDED_NOT_ATTESTED" if counts["records"] else "NOT_OBSERVED"} for frame,counts in frame_counts.items()}
    controller=parsed.get("controller")
    if isinstance(controller,dict):
        state=("REPORTED_OK" if controller.get("ok") is True else "NOT_CONFIRMED")
        report["steps"]["controller_execution"]={"state":state}
    else:
        report["steps"]["controller_execution"]={"state":"UNVERIFIED"}
    # No phase is attested by the presence of a generic trial ledger.
    for stage in ("ga_optuna","official_backtest","wf_oos",
                  "blind_future","shadow_execution"):
        report["steps"][stage]={"state":"NOT_ATTESTED"}
    return report

def main():
    root=Path(os.environ["BBOT_LOCAL_ROOT"])
    report=audit(root)
    out=root/"strategy_lab/results/v3/hosted_pipeline_audit.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,sort_keys=True,indent=2),encoding="utf-8")
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as summary:
        summary.write("## Original pipeline functional evidence audit\n")
        for name,item in report["steps"].items():
            summary.write(f"- {name}: {item['state']}\n")
        summary.write("### Original frame records (not execution proof)\n")
        for frame,item in report["frames"].items():
            summary.write(f"- {frame}: {item['records']} records, {item['completed']} completed, {item['failed']} failed\n")
    print("ORIGINAL_PIPELINE_AUDIT="+json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
