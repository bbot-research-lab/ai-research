# Official B-BOT backtester integration: verified initial contract

Inspected directly from user-provided `BBOT_RESEARCH_UPLOAD.zip` (not published):

- `strategy_lab/run_strategy.py` defines a CLI `main()` that requires a **strategy file argument**.
- The runner reads `strategy_lab/lab_config.json` and uses its `data_file` property.
- Runtime root defaults to the Windows directory `C:\\my\\bottest`; it may be overridden with `BBOT_LOCAL_ROOT`.
- The runner loads the standalone `gate_lab_fast.py` engine and dynamically imports the supplied strategy.
- It also reads cached candle data and material modules, and produces JSON results.

**Important:** This is *not* a callable pure-Python numeric objective. Calling it repeatedly from Optuna or GA requires an audited, sandboxed adapter, data isolation and a strict training-window contract.

What was added now:
- `research_addon/formal_runner_contract.py`: static contract inspection without executing source.
- `tests/test_formal_runner_contract.py`: fail-closed tests.
- The previous toy-objective candidate search remains **unconnected** to this official runner.
- Scheduled research and AWS deployment remain disabled.

Next: audit `lab_config.json`, imported material modules, gate engine, strategy templates, and data shape; implement a non-deploying **TRAIN-only** candidate evaluator that rejects sealed-period access.
