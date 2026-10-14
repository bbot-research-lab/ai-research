"""Fail-closed static readiness check for the official B-BOT research runner.

No imports of trading software. No network, orders, or secrets.
"""
import argparse
import json
from pathlib import Path

NEEDED = (
    "strategy_lab/run_strategy.py",
    "strategy_lab/research_controller.py",
    "strategy_lab/roadmap_manager.py",
    "strategy_lab/v3_governance.py",
    "strategy_lab/v3_task_queue.py",
    "strategy_lab/lab_config.json",
    "gate_lab_fast.py",
)

def inspect(root):
    root = Path(root).resolve()
    missing = [name for name in NEEDED if not (root / name).is_file()]
    settings_path = root / "strategy_lab/lab_config.json"
    config_error = None
    data_path = None
    if settings_path.is_file():
        try:
            config = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            configured = config.get("data_file")
            if not isinstance(configured, str) or not configured.strip():
                raise ValueError("data_file missing")
            # The actual run_strategy.py rewrites this Windows default if BBOT_LOCAL_ROOT is set.
            if configured.lower().endswith("gate_lab_exact_long_cache.parquet"):
                data_path = root / "gate_lab_exact_long_cache.parquet"
            else:
                proposed = Path(configured)
                if proposed.is_absolute() and root not in proposed.parents:
                    raise ValueError("data_file points outside research root")
                data_path = (root / proposed).resolve() if not proposed.is_absolute() else proposed
                if root not in data_path.parents:
                    raise ValueError("data_file resolves outside research root")
            if not data_path.is_file():
                missing.append("research candle cache data_file")
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            config_error = str(exc)
    result = {
        "ready": not missing and config_error is None,
        "missing": missing,
        "config_error": config_error,
        "no_live_deployment": True,
    }
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("source_root", type=Path)
    args = p.parse_args()
    r = inspect(args.source_root)
    print(json.dumps(r, ensure_ascii=False, sort_keys=True, indent=2))
    raise SystemExit(0 if r["ready"] else 2)
