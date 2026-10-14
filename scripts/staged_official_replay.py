"""Stage and run ORIGINAL B-BOT formal runner privately using three user ZIPs.

No automatic deployment, network, data uploads or strategy modifications.
Run only on an isolated local machine with pandas/numpy/pyarrow installed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
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
    args=p.parse_args()
    if args.timeout<1 or args.timeout>21600: p.error("timeout must be 1..21600")
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
        result=subprocess.run([sys.executable,str(runner),str(strategy)],cwd=root,
                              env=env,timeout=args.timeout,check=False)
        return result.returncode

if __name__=="__main__":
    sys.exit(main())
