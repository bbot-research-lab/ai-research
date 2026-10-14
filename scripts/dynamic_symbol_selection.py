"""B-BOT research universe from the production symbol selector's recorded state.

This deliberately does not invent a ranking algorithm. Production symbol.py
owns scoring, filters, membership, and rotation. Research caps its recorded
ordered output to 30 and never modifies production config/state.
"""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_FIXED=[
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
    "ADAUSDT","DOGEUSDT","AVAXUSDT","LTCUSDT","LINKUSDT"
]
TARGET_TOTAL=30

def from_official_state(config, state, total=TARGET_TOTAL):
    if type(total) is not int or total != 30:
        raise ValueError("research contract requires exactly 30 slots")
    if not isinstance(config,dict) or not isinstance(state,dict):
        raise ValueError("official config and symbol state are required")
    fixed=config.get("FIXED_SYMBOLS") or DEFAULT_FIXED
    if not isinstance(fixed,list) or not fixed:
        raise ValueError("invalid official fixed symbols")
    active=config.get("SYMBOLS")
    if not isinstance(active,dict):
        raise ValueError("official config SYMBOLS unavailable")
    meta=state.get("_meta")
    if not isinstance(meta,dict) or not isinstance(meta.get("final_dynamic"),list):
        raise ValueError("production rotation state unavailable; cannot substitute rankings")
    enabled={s for s,value in active.items() if value is True}
    output=[]
    for symbol in list(fixed)+meta["final_dynamic"]:
        if symbol not in enabled or symbol in output:continue
        if not isinstance(symbol,str) or not symbol.endswith("USDT"):continue
        output.append(symbol)
        if len(output)==total:break
    if len(output)<total:
        raise ValueError("fewer than 30 eligible production-selected symbols; no invented fill")
    return output

def write_selection(path, symbols):
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        raise FileExistsError("refusing to overwrite historic selection snapshot")
    target.write_text(json.dumps({
        "origin":"production symbol.py state/config (read-only)",
        "target_total":TARGET_TOTAL,
        "symbols":symbols,
        "historical_point_in_time_proven":False,
        "promotion_allowed":False
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target


# ---------------------- Historical point-in-time snapshots ----------------------
def utc_at(value):
    if not isinstance(value, str):
        raise ValueError("UTC timestamp string required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() != timezone.utc.utcoffset(stamp):
        raise ValueError("UTC timestamp required")
    return stamp.astimezone(timezone.utc)

def capture_production_state(config, state, output):
    """Record only the selection-relevant fields, at actual capture time.

    Private local journal only. Never include API secrets or full live config.
    Capturing now does not create historical evidence for earlier dates.
    """
    symbols=from_official_state(config,state)
    fixed=config.get("FIXED_SYMBOLS") or DEFAULT_FIXED
    dynamic=state["_meta"]["final_dynamic"]
    enabled={key:True for key,value in config["SYMBOLS"].items()
             if value is True and key in set(fixed+dynamic)}
    moment=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    record={
        "source":"production_state_capture",
        "captured_at":moment,
        "effective_at":moment,
        "config":{"FIXED_SYMBOLS":list(fixed),"SYMBOLS":enabled},
        "state":{"_meta":{"final_dynamic":list(dynamic)}},
        "symbols":symbols,
    }
    target=Path(output)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(record,f,ensure_ascii=False,indent=2)
        f.write("\n")
    return target

def replay_historical_rotations(directory, start, end):
    """Recreate 30-member changes only from genuinely dated official captures.

    Any missing capture, unverifiable backdated state or incomplete old history
    must not be filled with current rankings or reused as approved WF/OOS proof.
    """
    a,b=utc_at(start),utc_at(end)
    if a>=b:raise ValueError("invalid historical UTC range")
    snapshots=[]
    for file in sorted(Path(directory).glob("*.json")):
        snapshot=json.loads(file.read_text(encoding="utf-8"))
        if snapshot.get("source")!="production_state_capture":
            raise ValueError("untrusted historical snapshot source: "+file.name)
        captured=utc_at(snapshot.get("captured_at"))
        effective=utc_at(snapshot.get("effective_at"))
        if effective!=captured or captured>datetime.now(timezone.utc):
            raise ValueError("backdated/future snapshot: "+file.name)
        selected=from_official_state(snapshot.get("config"),snapshot.get("state"))
        if snapshot.get("symbols")!=selected:
            raise ValueError("snapshot selection mismatch: "+file.name)
        snapshots.append((effective,file.name,selected))
    snapshots.sort(key=lambda x:x[0])
    if not snapshots or snapshots[0][0]>a:
        raise ValueError("no original selector capture at/before historical start")
    if len({item[0] for item in snapshots})!=len(snapshots):
        raise ValueError("duplicate snapshot capture times")
    active=max((x for x in snapshots if x[0]<=a),key=lambda x:x[0])
    boundaries=[(a,active[1],active[2])]
    for effective,filename,symbols in snapshots:
        if a<effective<b:
            boundaries.append((effective,filename,symbols))
    windows=[]
    for i,(when,filename,symbols) in enumerate(boundaries):
        until=boundaries[i+1][0] if i+1<len(boundaries) else b
        windows.append({"start":when.isoformat().replace("+00:00","Z"),
                        "end":until.isoformat().replace("+00:00","Z"),
                        "symbols":list(symbols),"snapshot":filename})
    return {
        "start":a.isoformat().replace("+00:00","Z"),
        "end":b.isoformat().replace("+00:00","Z"),
        "target_total":TARGET_TOTAL,
        "source":"dated official selector snapshots (not re-ranked)",
        "windows":windows,
        "history_complete_verified":False,
        "historical_point_in_time_proven":False,
        "promotion_allowed":False,
    }

def write_historical_plan(path, plan):
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:
        json.dump(plan,f,ensure_ascii=False,indent=2)
        f.write("\n")
    return target

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--production-config",type=Path)
    p.add_argument("--production-symbol-state",type=Path)
    p.add_argument("--history-dir",type=Path)
    p.add_argument("--start",help="UTC inclusive start, e.g. 2026-01-01T00:00:00Z")
    p.add_argument("--end",help="UTC exclusive end")
    p.add_argument("--capture-now",action="store_true")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.history_dir:
        if a.capture_now or a.production_config or a.production_symbol_state or not (a.start and a.end):
            p.error("history replay requires only --history-dir, --start, --end and --output")
        print(write_historical_plan(a.output,replay_historical_rotations(a.history_dir,a.start,a.end)))
    else:
        if not (a.production_config and a.production_symbol_state) or a.start or a.end:
            p.error("provide both official config and state (or --history-dir)")
        cfg=json.loads(a.production_config.read_text(encoding="utf-8"))
        st=json.loads(a.production_symbol_state.read_text(encoding="utf-8"))
        if a.capture_now:
            print(capture_production_state(cfg,st,a.output))
        else:
            print(write_selection(a.output,from_official_state(cfg,st)))
