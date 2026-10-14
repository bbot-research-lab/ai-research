# Original formal accounting replay on Linux — actual local execution

The unmodified `strategy_lab/run_strategy.py` was loaded from the user-provided ZIP and its *pure accounting functions* were called directly with synthetic prices/signals. No `pyarrow`, private cache, exchange calls, orders, or AWS access.

Environment: Linux Python with installed NumPy/Pandas.

Executed cases:
- `trade_net_return(LONG, entry=100, exit=110, fee=0.0005)` => `0.09900000000000009`
- `trade_net_return(SHORT, entry=100, exit=110, fee=0.0005)` => `-0.10100000000000009`
- `simulate` on close prices `[100,102,105,104,100]` and signal `[0,1,1,0,0]` => one LONG `END_OF_TEST` exit; net `-0.020607843137254944`
- Same prices and signal `[0,-1,-1,0,0]` => one SHORT `END_OF_TEST` exit; net `0.018607843137254942`

The reusable tool `scripts/official_runner_smoke.py` runs these cases against any path to the **actual** runner. It intentionally does not carry or publish original source.

**Verified:** pure official trade simulation functions run on Linux with this synthetic input.
**Not verified:** the complete official strategy, cache, signals, final fills and WF/OOS results; pyarrow and a confidential input staging route are still missing. No stricter scoring thresholds or live R4 modifications.
