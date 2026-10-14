"""Read-only static inspection of source files in a B-BOT export ZIP.
Does not import, exec, extract, or publish archive members.
Embedded Python source is recursively AST-parsed; executable embedded code
is flagged for manual review, never auto-approved.
"""
import argparse
import ast
import json
import zipfile
from pathlib import PurePosixPath

DANGEROUS_CALLS = {"exec", "eval", "__import__", "compile"}
DANGEROUS_MODULES = {"subprocess", "socket", "requests", "httpx", "ccxt", "boto3", "ftplib"}
MAX_EMBEDDED_DEPTH = 3
MAX_SOURCE_BYTES = 1024 * 1024

def inspect_ast(tree, depth=0):
    flags=set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call=node.func
            name=call.id if isinstance(call,ast.Name) else (call.attr if isinstance(call,ast.Attribute) else "")
            if name in DANGEROUS_CALLS:
                flags.add("DYNAMIC_EXECUTION:"+name)
            if name in {"system", "Popen", "run", "check_call", "check_output"}:
                flags.add("PROCESS_CALL_REVIEW:"+name)
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name.split(".")[0] in DANGEROUS_MODULES: flags.add("NETWORK_OR_PROCESS_IMPORT:"+item.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in DANGEROUS_MODULES: flags.add("NETWORK_OR_PROCESS_IMPORT:"+node.module)
        if isinstance(node, ast.Constant) and isinstance(node.value,str):
            if node.value.startswith("-----BEGIN ") and "PRIVATE KEY" in node.value:
                flags.add("POTENTIAL_EMBEDDED_PRIVATE_KEY")
            if depth < MAX_EMBEDDED_DEPTH and len(node.value)>40:
                try: child=ast.parse(node.value)
                except (SyntaxError,ValueError): continue
                flags.update("EMBEDDED_"+flag for flag in inspect_ast(child,depth+1))
    return flags

def audit(archive_path):
    reports=[]
    with zipfile.ZipFile(archive_path) as z:
        for member in z.infolist():
            path=member.filename.replace("\\","/")
            parts=PurePosixPath(path).parts
            if not parts or ".." in parts or member.is_dir(): continue
            if not path.endswith(".py") or not path.startswith("strategy_lab/"): continue
            if "/strategies/" not in path and "/redeveloped_strategies/" not in path: continue
            if member.file_size>MAX_SOURCE_BYTES:
                reports.append({"path":path,"status":"OVERSIZED_REVIEW_REQUIRED"});continue
            try:
                source=z.read(member).decode("utf-8-sig")
                tree=ast.parse(source)
                flags=sorted(inspect_ast(tree))
                reports.append({"path":path,"status":"REVIEW_REQUIRED" if flags else "STATIC_LOW_RISK",
                                "flags":flags,"bytes":member.file_size})
            except (SyntaxError,UnicodeDecodeError,ValueError):
                reports.append({"path":path,"status":"UNREADABLE_REVIEW_REQUIRED"})
    counts={}
    for report in reports: counts[report["status"]]=counts.get(report["status"],0)+1
    return {"files":len(reports),"statuses":counts,"strategies":reports,
            "notice":"Static scan cannot prove safety. No source has been approved for publication."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("zip_path")
    print(json.dumps(audit(p.parse_args().zip_path),ensure_ascii=False,indent=2))
