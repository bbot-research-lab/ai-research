# Private formal replay after successful PyArrow CI

Confirmed in GitHub Actions run #6 (38519740284): Python 3.11 Linux successfully installed PyArrow 21.0.0, Pandas 2.3.3, NumPy 2.4.6, Optuna 4.9.0; Parquet tests and 47 unit tests passed. These tests used **synthetic data** and are not an original strategy benchmark.

Original `run_strategy.py` writes its JSON under `BBOT_LOCAL_ROOT/strategy_lab/results`. Previous staging code deleted that directory when its temporary folder exited. The replay tool now requires `--output-dir` when `--execute` is used and copies original JSON results out; it refuses overwrites. Do not upload this private JSON to the public repository until reviewed.

## Windows private playback

From a local clone of `bbot-research-lab/ai-research`, pass paths to the three ZIPs already supplied in the conversation:

```powershell
./scripts/setup_private_replay.ps1 -ResearchZip 'C:\path\BBOT_RESEARCH_UPLOAD.zip' -EngineCacheZip 'C:\path\BBOT_MISSING_FILES.zip' -ModulesZip 'C:\path\BBOT_STRATEGY_MODULES.zip' -Execute -OutputDir 'C:\path\bbot-private-formal-results'
```

The script creates its own `.private-replay-venv`, installs the GitHub-tested versions according to the requirements file, verifies original engine/cache hashes and the no-deployment flag, runs the original formal backtester, and retains its output. This does not change the existing B-BOT production installation; it is not a strict OS sandbox against malicious source.

The equivalent Linux command after requirements installation is:

```bash
python scripts/staged_official_replay.py BBOT_RESEARCH_UPLOAD.zip BBOT_MISSING_FILES.zip BBOT_STRATEGY_MODULES.zip --execute --output-dir /private/bbot-formal-results
```

The three original ZIPs remain available in this conversation, **not in GitHub Actions**. Do not place their raw contents in the public repo, public Action artifacts or repository commits. Running CI alone will not reproduce actual results. Baseline comparison, data validity and original promotion governance are still pending.
