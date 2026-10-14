# Train-only search boundary (not a trading backtest)

`research_addon/training_only.py` is an in-memory adapter between a training-window evaluator and candidate search. It snapshots rows limited to the `WindowPlan` training range, never passes sealed-period rows to the objective, and rejects non-finite scores. Unit tests alter the withheld future prices by large amounts and verify **identical genetic-search results** with unchanged training input.

Limitations:
- This is a pure-Python **boundary unit test**, not a validated replay of the B-BOT official formal backtester.
- The real runner may read underlying cache outside this adapter; do not assert end-to-end no-lookahead yet.
- Training/evidence may still be contaminated upstream by precomputed signals; check signal construction timestamps and provenance.
- Optuna/GA are suggestion generators, not an approval pipeline.
- Scheduled 24-hour work and EC2 synchronization remain OFF pending full engine and data certification.
