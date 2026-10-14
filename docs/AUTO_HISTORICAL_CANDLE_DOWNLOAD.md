# Automatic original B-BOT historical candle recovery

Source: Binance Vision **public USD-M futures klines**, not spot, not account data. Archive path `data/futures/um/monthly/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{YYYY-MM}.zip`, with daily fallback and checksum validation. No API key is used. Original `gate_lab_fast.find_tf_file` expects `data/candles/{SYMBOL}/{1h,6h,12h,1d,1w}.parquet` and original `find_monthly_file` expects `1M.parquet`.

`scripts/download_historical_candles.py` downloads source ZIP + companion SHA256 `.CHECKSUM`, reads archived UTC OHLCV, validates numeric fields and regular timestamps, never invents missing bars, and writes compatible private Parquet files without overwriting existing data.

`scripts/staged_official_replay.py` now supports `--auto-download-candles --candle-store PRIVATE_DIRECTORY` when used with `--execute --output-dir PRIVATE_RESULTS_DIRECTORY`. On an original runner error for a missing candle symbol/timeframe, the replay script derives that symbol's historic date window from the pinned exact-signal cache, downloads only its missing candles, stores them in the private persistent candle store, copies them into the isolated replay directory and restarts. The number of retries is capped at 300. Existing private downloaded files are reused on subsequent runs.

It does **not** change any research scoring threshold, manually alter candles, publish confidential inputs or touch the AWS R4 server. Data obtained later from public archives may differ from the exact historical raw input that produced the old cache; **baseline parity is NOT proved** until timestamps and signals are compared.

Example in an isolated machine with the original three ZIPs, dependencies installed and a writable private workspace:

```bash
python scripts/staged_official_replay.py BBOT_RESEARCH_UPLOAD.zip BBOT_MISSING_FILES.zip BBOT_STRATEGY_MODULES.zip --execute --auto-download-candles --candle-store /private/bbot-candles --output-dir /private/bbot-reports
```

Known limitation: any missing required Binance archive period fails closed rather than treating incomplete market history as valid. Network access and time are needed to download many years of bars across 35 symbols; no full historical replay success is claimed. The current ChatGPT container cannot reach the Binance archive over the network; the network-enabled GitHub Actions runner can download public archives but does not hold the private original source ZIPs.


## Selection-aware batch recovery

Given a **private dated** rotation plan, the original downloader now gathers
the union of symbols which actually appeared in any recorded window. Each
symbol is downloaded for its required historic span (including symbols later
rotated out), producing the **same original Parquet paths**. Existing files
are reused only when coverage and integrity checks succeed; otherwise the
run fails instead of silently overwriting or filling holes.

```bash
python scripts/download_historical_candles.py --history-plan /private/rotation-plan.json --root /private/bbot-data --timeframes 1h 6h 12h 1d 1w 1M
```

Data validity now includes the expected first and last UTC candle open,
gaps, repeated timestamps, non-finite OHLCV and inconsistent candle prices.
A checksum-valid but incomplete month no longer counts as complete.
If Binance archives have missing historical bars, the downloader stops.

**This does not yet run the official V3/WF/OOS simulator on newly selected
30-symbol history.** A real point-in-time official signal cache, observed
strategy configuration and baseline comparison are required; only the
original non-deploying, SHA-pinned private formal replay can test the existing
old cache. Public GitHub tests use synthetic fixtures, not historical PnL.
