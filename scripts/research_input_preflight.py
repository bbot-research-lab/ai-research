"""Read-only research input preflight for the OFFICIAL engine snapshot.

Use it only after supplying engine+cache by a separately audited mechanism.
Does not execute the engine, read row data or contact exchanges.
"""
import argparse
import json
import sys
from pathlib import Path

from research_addon.cache_integrity import verify as verify_hash
from research_addon.input_readiness import inspect as inspect_files
from research_addon.formal_runner_contract import inspect_official_runner


def preflight(root):
    root = Path(root).resolve()
    checks = {
        "file_contract": inspect_files(root),
        "runner_contract": inspect_official_runner(root),
        "engine_cache_integrity": verify_hash(root),
    }
    return {
        "ready": all(x.get("ready", x.get("ok", False)) for x in checks.values()),
        "checks": checks,
        "official_backtest_executed": False,
        "sealed_oos_validated": False,
        "production_deploy_allowed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("research_root", type=Path)
    args = parser.parse_args()
    result = preflight(args.research_root)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    sys.exit(0 if result["ready"] else 2)
