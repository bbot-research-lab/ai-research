"""Static contract for importing the *existing* formal B-BOT backtester.
This module NEVER imports or executes an uploaded strategy or live order code.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path

REQUIRED = (
    "strategy_lab/run_strategy.py",
    "strategy_lab/lab_config.json",
    "gate_lab_fast.py",
)
DEFAULT_LOCAL_ROOT = r"C:\my\bottest"

def inspect_official_runner(root: str | Path) -> dict:
    root = Path(root)
    missing = [x for x in REQUIRED if not (root / x).is_file()]
    result = {
        "ready": False,
        "missing_files": missing,
        "linux_path_ready": False,
        "has_formal_main": False,
        "requires_strategy_argument": False,
        "config_has_data_file": False,
        "execution_enabled": False,
    }
    runner_path = root / REQUIRED[0]
    if runner_path.is_file():
        tree = ast.parse(runner_path.read_text(encoding="utf-8-sig"))
        result["has_formal_main"] = any(
            isinstance(node, ast.FunctionDef) and node.name == "main"
            for node in tree.body
        )
        # Static evidence of CLI contract. Deliberately conservative.
        result["requires_strategy_argument"] = any(
            isinstance(node, ast.Constant) and node.value == "strategy file required"
            for node in ast.walk(tree)
        )
        code = runner_path.read_text(encoding="utf-8-sig")
        # Runner defaults to a Windows local directory if BBOT_LOCAL_ROOT is unset.
        result["linux_path_ready"] = "BBOT_LOCAL_ROOT" in code
    cfg = root / REQUIRED[1]
    if cfg.is_file():
        data = json.loads(cfg.read_text(encoding="utf-8-sig"))
        result["config_has_data_file"] = isinstance(data.get("data_file"), str)
    result["ready"] = (
        not missing
        and result["has_formal_main"]
        and result["requires_strategy_argument"]
        and result["config_has_data_file"]
        and result["linux_path_ready"]
    )
    return result
