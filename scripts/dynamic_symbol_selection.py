"""B-BOT research universe from the production symbol selector's recorded state.

This deliberately does not invent a ranking algorithm. Production symbol.py
owns scoring, filters, membership, and rotation. Research caps its recorded
ordered output to 30 and never modifies production config/state.
"""
import argparse
import json
from pathlib import Path

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

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--production-config",type=Path,required=True)
    p.add_argument("--production-symbol-state",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    cfg=json.loads(a.production_config.read_text(encoding="utf-8"))
    st=json.loads(a.production_symbol_state.read_text(encoding="utf-8"))
    print(write_selection(a.output,from_official_state(cfg,st)))
