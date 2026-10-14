# Research symbol universe: production parity, 30-symbol cap

Verified upstream source: `hans1177/binance-bot/symbol.py` (GitHub default branch as reviewed 2026-10-14).

The live selector uses `config.json FIXED_SYMBOLS` (or default ten BTC/ETH/BNB/SOL/XRP/ADA/DOGE/AVAX/LTC/LINK), official USD-M liquidity/price/spread/listing-age checks, 7-day and recent-three-sample volume/trade-count checks, a score and state memory, min supported initial leverage 30 for **dynamic** selections, and at most five new dynamic arrivals per rotation. Its source currently targets 35 positions, with up to 25 dynamic selections; it does NOT simply choose the largest 24h turnover.

**Research rule:** Take the **ordered fixed + final_dynamic symbols** from the production selector's recorded config and state, retain enabled and unique symbols, and cap to **30**. The scanner does not replace server scoring with homemade scoring, cannot place orders, and will fail closed rather than invent symbols when the production-selected pool is insufficient. The **live server stays unchanged at its existing count**.

Run `python scripts/dynamic_symbol_selection.py --production-config LOCAL_CONFIG_SNAPSHOT.json --production-symbol-state LOCAL_SYMBOL_STATE_SNAPSHOT.json --output PRIVATE_RESEARCH_UNIVERSE.json`. These are *existing trusted snapshots*; do not upload full server config or state to a public repository.

**Historical caveat:** A current production snapshot is NOT a point-in-time selection for past years. For valid WF/OOS, capture/reconstruct historical dated selector snapshots and use only information available at those dates. Existing 35-symbol exact-signal cache cannot be relabeled as a new 30-symbol dynamic backtest. No historical parity or full 30-symbol backtest is claimed.


## Dated rotation captures and point-in-time replay

The **current** 30-symbol selection is never applied retrospectively. Record each
original production selection *when it is observed*, in a private filesystem.
No connection to R4 is made by these commands: they consume **read-only,
pre-existing, user-controlled** local snapshots.

```bash
python scripts/dynamic_symbol_selection.py --production-config PRIVATE_CONFIG.json --production-symbol-state PRIVATE_STATE.json --capture-now --output /private/rotations/2026-10-14T070000Z.json
python scripts/dynamic_symbol_selection.py --history-dir /private/rotations --start 2026-10-14T07:00:00Z --end 2026-10-15T00:00:00Z --output /private/rotation-plan.json
```

Capture writes **only symbol-selection data**, not API keys or full production
config; it is immutable (exclusive create). Point-in-time history requires a
capture at or before the requested first instant. Later captures mark changes
at their observed timestamps. The replay refuses duplicates, backdated
effective times, inconsistent selections, and missing initial history.

**No earlier records are manufactured.** The earliest capture only establishes
membership *from that time*, not membership in 2020-2025. An archive of
unverified snapshots is not evidence that every historic rotation was captured:
`history_complete_verified=false`, `historical_point_in_time_proven=false`,
and `promotion_allowed=false` remain mandatory. This is a preliminary
30-slot research universe, **not** a replacement for the original frozen
35-symbol formal cache or official WF/OOS approval.
