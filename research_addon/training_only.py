"""Train-only optimizer adapter. No exchange, deployment or OOS access."""
from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping
from research_addon.sealed_windows import WindowPlan, training_rows

class TrainOnlyObjective:
    """An optimizer can see training rows only. OOS evaluation is a separate caller."""
    def __init__(self, rows: Iterable[Mapping], plan: WindowPlan,
                 evaluator: Callable[[list, dict], float], *, timestamp_field="open_time"):
        # Snapshot the allowed data once, excluding all other timestamps.
        self._train = tuple(dict(row) for row in training_rows(rows, plan, timestamp_field))
        self._evaluator = evaluator
        self.window_signature = plan.signature()

    @property
    def train_count(self):
        return len(self._train)

    def __call__(self, params: dict) -> float:
        if not isinstance(params, dict) or not params:
            raise ValueError("nonempty parameter dictionary required")
        # Defensive copies stop an evaluator from mutating future trials.
        result = float(self._evaluator([dict(r) for r in self._train], dict(params)))
        if not -float("inf") < result < float("inf"):
            raise ValueError("nonfinite training result")
        return result
