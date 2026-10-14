"""SQLite research ledger, independent of the official V3 trial ledger.

No production approval and no deletion of completed/failed experiments.
Use separate database files per frame to avoid concurrent-writer contention.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
 identity TEXT PRIMARY KEY,
 frame TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('COMPLETED', 'FAILED')),
 spec_json TEXT NOT NULL,
 outcome_json TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def fingerprint(*, structure, params, frame, symbols, data_version, rules_version, code_version):
    if not all([frame, data_version, rules_version, code_version]):
        raise ValueError("all version identities are required")
    canonical = json.dumps({
        "structure": structure, "params": params, "frame": frame,
        "symbols": sorted(set(symbols)), "data_version": data_version,
        "rules_version": rules_version, "code_version": code_version,
    }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

class ExperimentLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path), timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(SCHEMA)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    def record(self, *, identity, frame, status, spec, outcome):
        if status not in {"COMPLETED", "FAILED"}:
            raise ValueError("only terminal experiments can be recorded")
        # Atomic and idempotent. Existing results must never be overwritten.
        with self.db:
            cursor = self.db.execute(
                "INSERT OR IGNORE INTO experiments(identity,frame,status,spec_json,outcome_json)"
                " VALUES(?,?,?,?,?)",
                (identity, frame, status,
                 json.dumps(spec, sort_keys=True, allow_nan=False),
                 json.dumps(outcome, sort_keys=True, allow_nan=False)))
        return cursor.rowcount == 1

    def get(self, identity):
        row = self.db.execute(
            "SELECT frame,status,spec_json,outcome_json FROM experiments WHERE identity=?",
            (identity,)).fetchone()
        if row is None:
            return None
        return {"frame": row[0], "status": row[1],
                "spec": json.loads(row[2]), "outcome": json.loads(row[3])}

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]
