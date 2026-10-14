"""Research-only checkpoint store; no imports from production bot."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

SCHEMA = "BBOT_RESEARCH_CHECKPOINT_V1"
ALLOWED = {"CANDIDATE", "TRAIN_EVALUATED", "AWAITING_SEALED", "REJECTED"}
MAX_RECORDS = 10000

def signature(params):
    raw = json.dumps(params, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()

def load(path):
    path = Path(path)
    if not path.exists():
        return {"schema": SCHEMA, "records": {}, "completed_trials": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unknown checkpoint schema")
    records = data.get("records")
    if not isinstance(records, dict) or len(records) > MAX_RECORDS:
        raise ValueError("invalid checkpoint records")
    for key, record in records.items():
        if not isinstance(record, dict) or record.get("state") not in ALLOWED:
            raise ValueError("invalid checkpoint state")
        if signature(record.get("params")) != key:
            raise ValueError("checkpoint fingerprint mismatch")
    completed = data.get("completed_trials")
    if type(completed) is not int or completed < 0:
        raise ValueError("invalid completed_trials")
    return data

def record_trial(checkpoint, params, state, train_score=None):
    if state not in ALLOWED:
        raise ValueError("unsupported state; no live approval state accepted")
    if not isinstance(params, dict) or not params:
        raise ValueError("parameters required")
    key = signature(params)
    records = checkpoint["records"]
    if key in records:
        return False
    if len(records) >= MAX_RECORDS:
        raise ValueError("checkpoint capacity reached")
    if train_score is not None:
        score = float(train_score)
        if not (-float("inf") < score < float("inf")):
            raise ValueError("score must be finite")
    else:
        score = None
    records[key] = {"params": params, "state": state, "train_score": score}
    checkpoint["completed_trials"] += 1
    return True

def save(path, checkpoint):
    path = Path(path)
    # Always validate before writing; never emit partial checkpoint.
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != SCHEMA:
        raise ValueError("invalid checkpoint")
    records = checkpoint.get("records")
    if not isinstance(records, dict) or len(records) > MAX_RECORDS:
        raise ValueError("invalid checkpoint records")
    for k, v in records.items():
        if signature(v.get("params")) != k or v.get("state") not in ALLOWED:
            raise ValueError("invalid record")
    blob = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"), allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temp_name = stream.name
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
