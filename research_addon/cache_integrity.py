"""Check pinned backtest inputs before research; no data row reads or trading imports."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

PINNED_ENGINE = "78d38775b8d741de0a57027962b1820eb37d94087771e1358fe24d93ba5a6c9d"
PINNED_CACHE = "b47837c09b8672c9b420cf80fe37fcaba80fd61f2b6aeee8e03a6ceaa74833e3"

def sha256_stream(path):
    h = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def verify(root, *, expected_engine=PINNED_ENGINE, expected_cache=PINNED_CACHE):
    root=Path(root)
    engine=root/"gate_lab_fast.py"
    cache=root/"gate_lab_exact_long_cache.parquet"
    if not engine.is_file() or not cache.is_file():
        return {"ok": False, "reason": "REQUIRED_INPUT_MISSING"}
    if sha256_stream(engine)!=expected_engine or sha256_stream(cache)!=expected_cache:
        return {"ok": False, "reason": "PINNED_SHA256_MISMATCH"}
    with cache.open("rb") as file:
        first=file.read(4)
        file.seek(-4,2)
        last=file.read(4)
    if first != b"PAR1" or last != b"PAR1":
        return {"ok": False, "reason": "PARQUET_MAGIC_INVALID"}
    if cache.stat().st_size < 12:
        return {"ok": False, "reason": "PARQUET_FOOTER_INVALID"}
    with cache.open("rb") as file:
        file.seek(-8, 2)
        footer_size = struct.unpack("<I", file.read(4))[0]
    if footer_size == 0 or footer_size > cache.stat().st_size - 12:
        return {"ok": False, "reason": "PARQUET_FOOTER_INVALID"}
    return {"ok": True, "reason": "INTEGRITY_ONLY_NOT_DATA_VALIDATION", "cache_bytes": cache.stat().st_size}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("research_root",type=Path)
    args=p.parse_args()
    result=verify(args.research_root)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["ok"] else 2)
