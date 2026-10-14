"""Audit original B-BOT archived WF checkpoints; no source execution."""
import argparse
import collections
import hashlib
import json
import zipfile

def audit(path):
    groups=collections.defaultdict(list)
    errors=[]
    with zipfile.ZipFile(path) as z:
        for m in z.infolist():
            name=m.filename.replace("\\","/")
            if "/walk_forward_v1/" not in name or not name.endswith(".json"):
                continue
            try:
                item=json.loads(z.read(m))
                if item.get("schema")!="RESEARCH_PIPELINE_V2_CHECKPOINT":
                    continue
                f=item["candidate_config"]["fold"]
                if not (f["train_start_ts"]<f["train_end_ts"]<=f["test_start_ts"]<f["test_end_ts"]):
                    raise ValueError("invalid chronological fold")
                stable={"status":item.get("status"),"stage":item.get("stage"),
                        "fold":f,"metrics":item["metrics"],
                        "fingerprint":item.get("data_fingerprint"),
                        "role":item["candidate_config"].get("role"),
                        "parent":item["candidate_config"].get("parent"),
                        "universe_size":item["candidate_config"].get("universe_size")}
                groups[(item["candidate"],f["fold"])].append(stable)
            except (ValueError,KeyError,TypeError) as e:
                errors.append({"member":name,"error":str(e)})
    conflicts=[]
    for key,vals in groups.items():
        digests={hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for v in vals}
        if len(digests)>1:
            conflicts.append({"candidate":key[0],"fold":key[1]})
    return {"raw_records":sum(map(len,groups.values())),
            "unique_candidate_folds":len(groups),
            "duplicate_records":sum(len(v)-1 for v in groups.values()),
            "duplicate_conflicts":conflicts,"errors":errors,
            "new_backtests_executed":0,"promotion_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("research_zip")
    r=audit(p.parse_args().research_zip)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    raise SystemExit(2 if r["duplicate_conflicts"] or r["errors"] else 0)
