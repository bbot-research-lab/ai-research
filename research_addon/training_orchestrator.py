"""Training-only multi-frame proposal orchestration.

An injected objective may evaluate *training data only*. Results are NOT official
V3 trials, deployment approvals, or verified strategy performance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidate_search import Range, genetic_candidates, optuna_candidates
from .experiment_ledger import ExperimentLedger, fingerprint
from .frame_progress import load_progress, save_progress
from .structure_proposals import FRAMES, propose_structures

DEFAULT_BOUNDS = {
    "lookback": Range(5.0, 120.0),
    "threshold": Range(0.05, 3.0),
}


def training_batch(*, frame, root, objective, data_version, rules_version,
                   code_version, symbols, seed=42, structures=4,
                   ga_population=8, ga_generations=2, optuna_trials=8,
                   checkpoint_every=10):
    """Bounded/restartable; objective(structure_dict, params) -> training score.

    Each proposal/method is a deterministic batch. Terminal results are committed
    before advancing progress; every identity includes immutable source versions.
    """
    if frame not in FRAMES or not callable(objective):
        raise ValueError("invalid frame or training objective")
    if not 1 <= structures <= 1000 or not 1 <= checkpoint_every <= 10000:
        raise ValueError("invalid batch limits")
    if not symbols or not all((data_version, rules_version, code_version)):
        raise ValueError("missing provenance")
    base = Path(root) / frame
    base.mkdir(parents=True, exist_ok=True)
    progress_path = base / "training_progress.json"
    marker = load_progress(progress_path, frame=frame)
    # Fail closed when resuming under a different experiment configuration.
    import hashlib
    run_config = json.dumps({
        "frame": frame, "data": data_version, "rules": rules_version,
        "code": code_version, "symbols": sorted(set(symbols)), "seed": seed,
        "structures": structures, "ga_population": ga_population,
        "ga_generations": ga_generations, "optuna_trials": optuna_trials,
    }, sort_keys=True)
    run_key = hashlib.sha256(run_config.encode()).hexdigest()
    if marker and not marker["cursor"].startswith(run_key + ":"):
        raise ValueError("stored progress belongs to another configuration")
    batch = propose_structures(frame, seed=seed, count=structures)
    inserted = 0
    checked = 0
    with ExperimentLedger(base / "training_ledger.sqlite3") as ledger:
        for index, structure in enumerate(batch):
            for method in ("ga", "optuna"):
                job_key = f"{run_key}:{index}:{method}"
                def evaluate(params):
                    return float(objective(structure.as_dict(), params))
                try:
                    if method == "ga":
                        proposals = genetic_candidates(
                            DEFAULT_BOUNDS, evaluate, seed=seed + index,
                            population=ga_population, generations=ga_generations)
                    else:
                        proposals = optuna_candidates(
                            DEFAULT_BOUNDS, evaluate, seed=seed + index,
                            trials=optuna_trials)
                    for row in proposals:
                        params = row["params"]
                        identity = fingerprint(
                            structure=structure.as_dict(), params=params,
                            frame=frame, symbols=symbols, data_version=data_version,
                            rules_version=rules_version, code_version=code_version)
                        if ledger.record(identity=identity, frame=frame,
                                         status="COMPLETED",
                                         spec={"structure": structure.as_dict(),
                                               "params": params, "method": method,
                                               "stage": "TRAINING_ONLY"},
                                         outcome={"train_score": row["train_score"],
                                                  "official_pass": False}):
                            inserted += 1
                        checked += 1
                except Exception as exc:
                    # Infrastructure failure must not be called a failed strategy.
                    # Preserve existing terminal results, stop and retry later.
                    save_progress(progress_path, frame=frame, cursor=job_key,
                                  completed=ledger.count())
                    raise RuntimeError("training search interrupted; safe retry") from exc
                save_progress(progress_path, frame=frame, cursor=job_key,
                              completed=ledger.count())
    return {"frame": frame, "new_records": inserted, "evaluated": checked,
            "ledger_records": ledger_count(base / "training_ledger.sqlite3"),
            "stage": "TRAINING_ONLY", "official_pass": False}


def ledger_count(path):
    with ExperimentLedger(path) as ledger:
        return ledger.count()


def main():
    parser = argparse.ArgumentParser(description="Inert training harness self-test")
    parser.add_argument("--frame", choices=FRAMES, required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--dry-synthetic", action="store_true", required=True)
    args = parser.parse_args()
    # Explicit synthetic-only CLI avoids accidentally executing original V3
    # strategy or using a sealed dataset in this prototype.
    def synthetic(_structure, params):
        return -(params["threshold"] - 1.0) ** 2 - (params["lookback"] - 40.0) ** 2 / 10000
    print(json.dumps(training_batch(
        frame=args.frame, root=args.root, objective=synthetic,
        data_version="SYNTHETIC_V1", rules_version="NO_OFFICIAL_RULES",
        code_version="MULTIFRAME_TRAINING_V1", symbols=["SYNTHETIC"],
        structures=2, optuna_trials=3)))


if __name__ == "__main__":
    main()
