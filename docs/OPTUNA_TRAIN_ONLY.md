# Optuna isolated-training smoke tests

New tests call existing `research_addon.candidate_search.optuna_candidates` using the existing `TrainOnlyObjective` wrapper.

Checks:
- Fix the optimizer seed and training rows, replace sealed-future prices with extremely different values, and demand identical Optuna trial sequences and training scores.
- Invalid (non-finite) train scores fail rather than silently approving candidates.
- Research proposals have **no promotion status**.

This checks the isolated Python objective only. It **does not** establish that the original B-BOT official runner, derived indicator cache, portfolio simulation, WF/OOS evaluations or signal generation cannot see future observations. It is not a real strategy backtest.

Next: supply the separately audited official source/cache to a quarantined Linux validation worker; compare formal runner outputs to the Windows reference and audit the cache's signal timestamp construction.

As of this change, scheduled research and AWS deployment are still disabled.
