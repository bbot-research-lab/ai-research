"""Stage and run ORIGINAL B-BOT formal runner privately using three user ZIPs.

No automatic deployment, network, data uploads or strategy modifications.
Run only on an isolated local machine with pandas/numpy/pyarrow installed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ENGINE_SHA="78d38775b8d741de0a57027962b1820eb37d94087771e1358fe24d93ba5a6c9d"
CACHE_SHA="b47837c09b8672c9b420cf80fe37fcaba80fd61f2b6aeee8e03a6ceaa74833e3"
MODULES={"div.py","ema_cross.py","macd.py","obv.py","sar.py","shape.py","stoch.py"}
SOURCE_FILES={
 "strategy_lab/run_strategy.py",
 "strategy_lab/lab_config.json",
 "strategy_lab/strategies/CURRENT_PRODUCTION.py",
}
EXTRA_FILES={"gate_lab_fast.py","gate_lab_exact_long_cache.parquet"}

def read_selected(archive, expected):
    found={}
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name=info.filename.replace("\\","/")
            if name in expected:
                if name in found: raise ValueError("duplicate ZIP member: "+name)
                found[name]=z.read(info)
    missing=expected-set(found)
    if missing: raise ValueError("missing from ZIP: "+",".join(sorted(missing)))
    return found

def stage(upload_zip, missing_zip, modules_zip, root):
    root=Path(root).resolve()
    for archive, required, prefix in [
        (upload_zip,SOURCE_FILES,""),
        (missing_zip,EXTRA_FILES,""),
        (modules_zip,MODULES,"assist/strategies/"),
    ]:
        for name,blob in read_selected(archive, required).items():
            rel=prefix+name
            if name=="gate_lab_fast.py" and hashlib.sha256(blob).hexdigest()!=ENGINE_SHA:
                raise ValueError("official gate engine hash mismatch")
            if name=="gate_lab_exact_long_cache.parquet" and hashlib.sha256(blob).hexdigest()!=CACHE_SHA:
                raise ValueError("official cache hash mismatch")
            target=root/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(blob)
    settings=json.loads((root/"strategy_lab/lab_config.json").read_text(encoding="utf-8-sig"))
    if not isinstance(settings,dict) or settings.get("auto_deploy") is not False:
        raise ValueError("refusing replay: original config must explicitly disable auto_deploy")
    if settings.get("mode") != "EXACT_SIGNAL_CACHE":
        raise ValueError("refusing replay: unexpected original research mode")
    return root

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_research_zip",type=Path)
    p.add_argument("engine_cache_zip",type=Path)
    p.add_argument("material_modules_zip",type=Path)
    p.add_argument("--timeout",type=int,default=900)
    p.add_argument("--execute",action="store_true",help="Opt in to full original research backtest")
    p.add_argument("--output-dir",type=Path,help="Private directory for retained official result JSON")
    p.add_argument("--auto-download-candles",action="store_true",help="Fetch missing original candles from public Binance USD-M archive")
    p.add_argument("--candle-store",type=Path,help="Persist downloaded candles privately across reruns")
    args=p.parse_args()
    if args.timeout<1 or args.timeout>21600: p.error("timeout must be 1..21600")
    if args.execute and args.output_dir is None: p.error("--execute requires --output-dir; otherwise reports are deleted")
    if args.auto_download_candles and (not args.execute or not args.candle_store):
        p.error("--auto-download-candles requires --execute and --candle-store")
    with tempfile.TemporaryDirectory(prefix="bbot_original_isolated_") as temp:
        root=stage(args.original_research_zip,args.engine_cache_zip,args.material_modules_zip,temp)
        print("Original input hashes verified; all official material modules staged.")
        if not args.execute:
            print("DRY RUN PASS: source files staged and pinned hashes match; no backtest executed.")
            return 0
        import importlib.util
        if importlib.util.find_spec("pyarrow") is None and importlib.util.find_spec("fastparquet") is None:
            print("BLOCKED: install pyarrow or fastparquet in the selected Python environment.")
            return 2
        env=dict(os.environ)
        env["BBOT_LOCAL_ROOT"]=str(root)
        # Avoid accidental reuse of live R4/production environment settings.
        for key in list(env):
            if key.startswith(("BINANCE_","AWS_","TELEGRAM_")) or key in {"API_KEY","API_SECRET"}:
                env.pop(key,None)
        runner=root/"strategy_lab/run_strategy.py"
        strategy=root/"strategy_lab/strategies/CURRENT_PRODUCTION.py"
        print("Executing official runner in temp directory; no original source patches.")
        downloaded=set()
        if args.auto_download_candles:
            import shutil
            store=args.candle_store.expanduser().resolve()
            store.mkdir(parents=True,exist_ok=True)
            for previous in store.glob("*/*.parquet"):
                target=root/"data"/"candles"/previous.parent.name/previous.name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(previous,target)
        for attempt in range(300 if args.auto_download_candles else 1):
            result=subprocess.run([sys.executable,str(runner),str(strategy)],cwd=root,
                                  env=env,timeout=args.timeout,check=False,capture_output=True,text=True,errors="replace")
            print(result.stdout[-15000:])
            if result.returncode==0:
                break
            if not args.auto_download_candles:
                print(result.stderr[-10000:]);break
            pattern=r"(1h|6h|12h|1d|1w|monthly) parquet missing for ([A-Z0-9]+)"
            match=re.search(pattern,result.stderr)
            if not match:
                print(result.stderr[-10000:]);break
            tf,symbol=match.groups()
            tf="1M" if tf=="monthly" else tf
            if (symbol,tf) in downloaded:
                raise RuntimeError("historical downloader did not resolve "+symbol+" "+tf)
            downloaded.add((symbol,tf))
            from download_historical_candles import download
            from datetime import datetime,timezone
            import pandas as pd
            from datetime import timedelta
            cache_timestamps=pd.read_parquet(root/'gate_lab_exact_long_cache.parquet',columns=['symbol','ts'])
            symbol_ts=cache_timestamps.loc[cache_timestamps['symbol']==symbol,'ts']
            if symbol_ts.empty: raise ValueError('symbol absent from pinned official cache: '+symbol)
            start=datetime.fromtimestamp(int(symbol_ts.min()),tz=timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
            end=datetime.fromtimestamp(int(symbol_ts.max()),tz=timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)
            print("DOWNLOADING AUTHENTIC HISTORICAL CANDLES:",symbol,tf,flush=True)
            report=download(symbol,tf,start,end,args.candle_store)
            source=Path(report["path"])
            target=root/"data"/"candles"/symbol/source.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            print("HISTORICAL CANDLES READY:",report,flush=True)
        else:
            raise RuntimeError("more than 300 missing candles; refusing unbounded retries")
        reports=list((root/"strategy_lab/results").glob("*.json"))
        if result.returncode==0 and not reports:
            print("ERROR: original runner returned 0 but created no result JSON")
            return 3
        if reports:
            destination=args.output_dir.expanduser().resolve()
            if destination == root or root in destination.parents:
                raise ValueError("report destination must be outside temporary staging")
            destination.mkdir(parents=True,exist_ok=True)
            for report in reports:
                target=destination/report.name
                if target.exists():
                    raise FileExistsError("refusing to overwrite an existing result: "+str(target))
                shutil.copy2(report,target)
                print("RETAINED_OFFICIAL_RESULT =",target)
        return result.returncode

if __name__=="__main__":
    sys.exit(main())
