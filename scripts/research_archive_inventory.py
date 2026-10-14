"""Read-only inventory of B-BOT export ZIP. No extraction, source execution, or publishing.

Use ZIP member paths normalized to POSIX separators; flag Python strategy sources
under results/ which must not be discarded by an indiscriminate .gitignore.
"""
from __future__ import annotations
import argparse
import json
import zipfile
from collections import Counter
from pathlib import PurePosixPath

def inventory(zip_path):
    with zipfile.ZipFile(zip_path) as arc:
        members = []
        for info in arc.infolist():
            normalized = info.filename.replace("\\", "/").lstrip("/")
            parts = PurePosixPath(normalized).parts
            if not parts or ".." in parts or ":" in parts[0]:
                raise ValueError("unsafe ZIP member path")
            if info.is_dir():
                continue
            members.append((normalized, info.file_size))
    results = [p for p, _ in members if p.startswith("strategy_lab/results/")]
    py_in_results = [p for p in results if p.endswith(".py")]
    strategies = [p for p in py_in_results if "/strategies/" in p or "/redeveloped_strategies/" in p]
    direct_modules = [p for p, _ in members if p.startswith("strategy_lab/") and p.count("/") == 1 and p.endswith(".py")]
    return {
        "total_files": len(members),
        "results_files": len(results),
        "python_under_results": len(py_in_results),
        "strategy_python_under_results": len(strategies),
        "direct_research_python_modules": len(direct_modules),
        "required_paths": {
            name: any(p == name for p, _ in members)
            for name in ("strategy_lab/run_strategy.py", "strategy_lab/research_controller.py",
                         "strategy_lab/roadmap_manager.py", "strategy_lab/lab_config.json")
        },
        "warning": "Do not blanket-delete results/: may contain strategy code. Inventory is NOT secret scan.",
        "code_published": False,
    }

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("research_zip")
    args=p.parse_args()
    print(json.dumps(inventory(args.research_zip), indent=2, ensure_ascii=False, sort_keys=True))
