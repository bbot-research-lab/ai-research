# Candidate search addon (research only)
- `research_addon/candidate_search.py` provides reproducible genetic parameter search and Optuna TPE search.
- Both accept only a caller-provided **training objective** and return suggestions/observed training scores.
- **No market data, trading code, exchange API, research-controller integration, approval logic, sealed OOS evaluation or live deployment** exists in this module yet.
- Tests exercise toy functions only. A real B-BOT official backtester adapter and data-contract validation are required next.
- GitHub Actions tests are manual/on-push only; 24h scheduled research is not enabled.
