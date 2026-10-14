"""Research-only adapter for ORIGINAL run_strategy.simulate.

Not a replacement for V3 formal portfolio or its pass gates.
Only use audited original runner with explicit local paths.
"""
from __future__ import annotations
import importlib.util
import math
from pathlib import Path

def load_official_simulate(runner_path):
    path = Path(runner_path).resolve(strict=True)
    if path.name != "run_strategy.py":
        raise ValueError("expected original run_strategy.py")
    spec = importlib.util.spec_from_file_location("_bbot_official_sim_for_training", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load official runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "simulate", None)):
        raise ValueError("official simulator unavailable")
    return module.simulate

def make_trade_objective(official_simulate, signal_builder, *, fee_rate):
    """Return (training_rows, params)->exploratory TRAIN-ONLY metric.

    Caller must enforce the training/holdout split. Result never approves a
    candidate; it is not the official V3 promotion score.
    """
    if not callable(signal_builder) or not callable(official_simulate):
        raise ValueError("original simulator and signal builder are required")
    fee = float(fee_rate)
    if not math.isfinite(fee) or fee < 0:
        raise ValueError("invalid fee")
    def evaluate(training_rows, params):
        import pandas as pd
        frame = pd.DataFrame(training_rows)
        if not {"ts", "close"}.issubset(frame.columns):
            raise ValueError("original simulator requires ts/close")
        if frame.empty or frame.ts.isna().any() or frame.ts.duplicated().any():
            raise ValueError("invalid training frame")
        if not frame.ts.is_monotonic_increasing:
            raise ValueError("training timestamps not strictly increasing")
        signals = signal_builder(frame.copy(deep=True), dict(params))
        trades = official_simulate(frame.copy(deep=True), signals, fee)
        returns = [float(trade["net_return"]) for trade in trades]
        if not all(map(math.isfinite, returns)):
            raise ValueError("nonfinite original simulator output")
        return sum(returns)  # exploration only, not formal V3 acceptance
    return evaluate
