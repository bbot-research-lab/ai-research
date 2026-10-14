"""Smoke-test ORIGINAL formal B-BOT runner without Parquet, exchange, or trading.

Use audited local source path. The runner is imported to exercise its pure
accounting functions, not main() or the production system.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

def smoke(runner_path):
    import pandas as pd
    path=Path(runner_path).resolve()
    spec=importlib.util.spec_from_file_location("_bbot_official_runner_smoke",path)
    runner=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    fee=0.0005
    assert math.isclose(runner.trade_net_return(1,100,110,fee),0.099,abs_tol=1e-12)
    assert math.isclose(runner.trade_net_return(-1,100,110,fee),-0.101,abs_tol=1e-12)
    frame=pd.DataFrame({"ts":[1,2,3,4,5],"close":[100.,102.,105.,104.,100.]})
    expected=[
      ([0,1,1,0,0],"LONG",-0.020607843137254944),
      ([0,-1,-1,0,0],"SHORT",0.018607843137254942),
    ]
    for sig,side,net in expected:
        trades=runner.simulate(frame,sig,fee)
        assert len(trades)==1
        t=trades[0]
        assert t["side"]==side and t["exit_reason"]=="END_OF_TEST"
        assert math.isclose(t["net_return"],net,abs_tol=1e-12)
    return {"passed":True,"original_runner_imported":True,
            "accounting_cases":4,"official_full_backtest":False,
            "production_deployment":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("official_runner_py",type=Path)
    result=smoke(p.parse_args().official_runner_py)
    print(json.dumps(result,sort_keys=True,indent=2))
