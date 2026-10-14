"""Compare B-BOT formal research configuration with a reviewed local baseline.
No imports from trading systems, no optimization, no order/deployment calls.
"""
import argparse
import json
from pathlib import Path

# Baseline from user-provided STRATEGY_LAB_CONFIG_V4 lab_config.json (2026-10-14).
REQUIRED = {
    "schema": "STRATEGY_LAB_CONFIG_V4",
    "mode": "EXACT_SIGNAL_CACHE",
    "auto_deploy": False,
    "auto_test": True,
    "fee_rate": 0.0005,
    "leverage_min": 1,
    "leverage_max": 50,
    "leverage_test_enabled": False,
    "research_candidate_fill_target": 8,
    "timeframes": ["30M", "1H", "6H", "12H", "1D", "1W", "1M"],
    "research_candidate_fill_timeframes": ["30M", "1H", "6H", "12H", "1D", "1W"],
    "reference_only_timeframes": ["1M"],
}

def inspect(config_path):
    obj = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("Research config must be a JSON object")
    differences = {}
    for key, expected in REQUIRED.items():
        if key not in obj or type(obj[key]) is not type(expected) or obj[key] != expected:
            differences[key] = {"expected": expected, "actual": obj.get(key, "MISSING")}
    data_file = obj.get("data_file")
    if not isinstance(data_file, str) or not data_file.endswith("gate_lab_exact_long_cache.parquet"):
        differences["data_file"] = {"expected": "*gate_lab_exact_long_cache.parquet", "actual": data_file}
    return {"matches_local_baseline": not differences, "differences": differences,
            "checks_only_configuration": True}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("config", type=Path)
    result=inspect(p.parse_args().config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["matches_local_baseline"] else 2)
