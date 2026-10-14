"""Minimal public-repository safety gate. Not a comprehensive secret scan."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
blocked = {".env", "id_rsa", "id_ed25519"}
extensions = {".pem", ".p12", ".pfx", ".key", ".sqlite", ".db"}
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.name.lower() in blocked or path.suffix.lower() in extensions:
        raise SystemExit(f"BLOCKED filename: {path.relative_to(root)}")
print("PREFLIGHT PASS: known sensitive filename patterns absent.")
print("NOTICE: full contents audit still required before research code upload.")
