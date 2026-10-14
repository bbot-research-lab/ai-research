"""Research-only, deterministic strategy-structure proposal.

This module NEVER evaluates official backtests, approves deployments, or places orders.
A proposal is an inert JSON-compatible definition; no eval/exec or future-data reads.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import random

FRAMES = ("30m", "1h", "6h", "12h", "1d", "1w")
FAMILIES = ("trend", "pullback", "breakout", "volatility_expansion", "momentum")
SIGNALS = ("ema_cross", "rsi_level", "channel_break", "atr_expansion", "volume_pressure")
EXIT_TYPES = ("opposite_signal", "atr_trailing", "time_limit")

@dataclass(frozen=True)
class Structure:
    frame: str
    family: str
    entry: tuple[str, ...]
    exit_type: str

    def __post_init__(self):
        if self.frame not in FRAMES or self.family not in FAMILIES:
            raise ValueError("unknown frame or family")
        if not 1 <= len(self.entry) <= 3 or len(set(self.entry)) != len(self.entry):
            raise ValueError("entry length or duplicate")
        if any(item not in SIGNALS for item in self.entry) or self.exit_type not in EXIT_TYPES:
            raise ValueError("unsupported research component")

    def as_dict(self):
        return {"frame": self.frame, "family": self.family,
                "entry": list(self.entry), "exit_type": self.exit_type}

    def identity(self):
        canonical = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()


def propose_structures(frame: str, *, seed: int = 42, count: int = 20,
                       forbidden: frozenset[str] = frozenset()):
    """Produce unique bounded candidates for TRAINING; no performance claims."""
    if frame not in FRAMES or count < 0 or count > 10000:
        raise ValueError("unsupported frame or candidate count")
    rng = random.Random(seed)
    seen = set(forbidden)
    result = []
    # Finite grammar: don't claim infinite possibilities.
    attempts = 0
    while len(result) < count and attempts < max(100, count * 50):
        attempts += 1
        entry = tuple(sorted(rng.sample(SIGNALS, rng.randint(1, 3))))
        s = Structure(frame, rng.choice(FAMILIES), entry, rng.choice(EXIT_TYPES))
        key = s.identity()
        if key in seen:
            continue
        seen.add(key)
        result.append(s)
    return result
