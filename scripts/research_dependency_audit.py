"""Static-only audit for an extracted B-BOT research archive. Never imports source."""
import argparse
import ast
import json
from pathlib import Path

CORE = ["roadmap_manager.py", "research_controller.py", "run_strategy.py",
        "v3_governance.py", "v3_task_queue.py"]
HIGH_RISK_IMPORTS = {"msvcrt", "winreg", "v3_deployment", "local_release_approval"}
EXECUTION_TERMS = {"subprocess", "os.system", "Popen", "exec", "eval"}

def inspect(root: Path):
    lab = root / "strategy_lab"
    if not lab.is_dir():
        raise ValueError("expected strategy_lab directory")
    modules = {p.stem: p for p in lab.glob("*.py")}
    report = {"root": "strategy_lab", "module_count": len(modules), "core": {},
              "risk_imports": {}, "missing_local_imports": {}, "ready": False}
    for filename in CORE:
        report["core"][filename] = filename[:-3] in modules
    for module, file in sorted(modules.items()):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8-sig"), filename=module)
        except (SyntaxError, UnicodeError) as e:
            report.setdefault("parse_errors", {})[module] = type(e).__name__
            continue
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        risks = sorted(imported & HIGH_RISK_IMPORTS)
        if risks:
            report["risk_imports"][module] = risks
        # We only identify v3_ local dependencies, not arbitrary external libs.
        missing = sorted(x for x in imported if x.startswith("v3_") and x not in modules)
        if missing:
            report["missing_local_imports"][module] = missing
    report["ready"] = (all(report["core"].values())
                       and not report["missing_local_imports"]
                       and not report.get("parse_errors")
                       and not report["risk_imports"])
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_extracted_dir", type=Path)
    args = parser.parse_args()
    result = inspect(args.archive_extracted_dir)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    raise SystemExit(0 if result["ready"] else 2)
