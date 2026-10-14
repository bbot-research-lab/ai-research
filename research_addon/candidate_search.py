"""Research-only candidate search. Never imports live trading code.
Caller passes a TRAINING objective; sealed/OOS approval must be separate.
"""
import math
import random
from dataclasses import dataclass

@dataclass(frozen=True)
class Range:
    low: float
    high: float
    def __post_init__(self):
        if self.low >= self.high: raise ValueError("invalid bounds")

def genetic_candidates(bounds, objective, *, seed=42, population=16, generations=8, mutation_rate=0.2):
    if not bounds or population < 4 or generations < 1 or not 0 <= mutation_rate <= 1:
        raise ValueError("invalid genetic search setup")
    rng = random.Random(seed)
    keys = sorted(bounds)
    def sample(): return {k: rng.uniform(bounds[k].low, bounds[k].high) for k in keys}
    def mutate(parent):
        child = dict(parent)
        for k in keys:
            if rng.random() < mutation_rate:
                span = bounds[k].high - bounds[k].low
                child[k] = min(bounds[k].high, max(bounds[k].low, child[k] + rng.gauss(0, span * .15)))
        return child
    members = [sample() for _ in range(population)]
    seen = {}
    for _ in range(generations):
        scored = []
        for m in members:
            sig = tuple((k, round(m[k], 12)) for k in keys)
            if sig not in seen:
                score = float(objective(dict(m)))
                if not math.isfinite(score):
                    raise ValueError("nonfinite training score")
                seen[sig] = {"params": dict(m), "train_score": score}
            scored.append(seen[sig])
        scored.sort(key=lambda x: x["train_score"], reverse=True)
        elite = [x["params"] for x in scored[:max(2, population // 4)]]
        members = [dict(m) for m in elite]
        while len(members) < population:
            a, b = rng.sample(elite, 2)
            members.append(mutate({k: a[k] if rng.random() < .5 else b[k] for k in keys}))
    return sorted(seen.values(), key=lambda x: x["train_score"], reverse=True)

def optuna_candidates(bounds, objective, *, seed=42, trials=40):
    if not bounds or trials < 1: raise ValueError("invalid optuna setup")
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    def evaluate(trial):
        score = float(objective({k: trial.suggest_float(k, b.low, b.high) for k, b in sorted(bounds.items())}))
        if not math.isfinite(score):
            raise ValueError("nonfinite training score")
        return score
    study.optimize(evaluate, n_trials=trials, n_jobs=1)
    return [{"params": dict(t.params), "train_score": t.value}
            for t in sorted(study.trials, key=lambda t: t.value if t.value is not None else float("-inf"), reverse=True)
            if t.value is not None and t.state == optuna.trial.TrialState.COMPLETE]
