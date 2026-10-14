"""Immutable TRAIN/OOS window boundary for research. No trading/exchange access."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

def parse_utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamps must be ISO-8601 UTC strings")
    stamp = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(stamp)
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError("timestamp requires UTC offset")
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class WindowPlan:
    train_start: str
    train_end: str
    sealed_start: str
    sealed_end: str
    embargo_seconds: int = 0

    def __post_init__(self):
        a,b,c,d = map(parse_utc,(self.train_start,self.train_end,self.sealed_start,self.sealed_end))
        if self.embargo_seconds < 0 or not (a < b <= c < d):
            raise ValueError("invalid chronological split")
        if (c-b).total_seconds() < self.embargo_seconds:
            raise ValueError("insufficient embargo between train and sealed")
    def signature(self):
        payload=json.dumps(self.__dict__,sort_keys=True,separators=(",",":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def training_rows(rows, plan: WindowPlan, timestamp_field="open_time"):
    """Only rows in [train_start, train_end). Caller must never pass OOS rows to optimizer."""
    start,end = parse_utc(plan.train_start),parse_utc(plan.train_end)
    result=[]
    prev=None
    for row in rows:
        stamp=parse_utc(row[timestamp_field])
        if prev is not None and stamp <= prev:
            raise ValueError("rows must be strictly ordered and unique")
        prev=stamp
        if start <= stamp < end:
            result.append(row)
    if not result:
        raise ValueError("empty training window")
    return result

def sealed_rows(rows, plan: WindowPlan, timestamp_field="open_time"):
    """Only for a separate frozen-candidate evaluator, never for search objective."""
    start,end=parse_utc(plan.sealed_start),parse_utc(plan.sealed_end)
    result=[]
    prev=None
    for row in rows:
        stamp=parse_utc(row[timestamp_field])
        if prev is not None and stamp <= prev:
            raise ValueError("rows must be strictly ordered and unique")
        prev=stamp
        if start <= stamp < end:
            result.append(row)
    if not result:
        raise ValueError("empty sealed window")
    return result
