# Research symbol universe: production parity, 30-symbol cap

Verified upstream source: `hans1177/binance-bot/symbol.py` (GitHub default branch as reviewed 2026-10-14).

The live selector uses `config.json FIXED_SYMBOLS` (or default ten BTC/ETH/BNB/SOL/XRP/ADA/DOGE/AVAX/LTC/LINK), official USD-M liquidity/price/spread/listing-age checks, 7-day and recent-three-sample volume/trade-count checks, a score and state memory, min supported initial leverage 30 for **dynamic** selections, and at most five new dynamic arrivals per rotation. Its source currently targets 35 positions, with up to 25 dynamic selections; it does NOT simply choose the largest 24h turnover.

**Research rule:** Take the **ordered fixed + final_dynamic symbols** from the production selector's recorded config and state, retain enabled and unique symbols, and cap to **30**. The scanner does not replace server scoring with homemade scoring, cannot place orders, and will fail closed rather than invent symbols when the production-selected pool is insufficient. The **live server stays unchanged at its existing count**.

Run `python scripts/dynamic_symbol_selection.py --production-config LOCAL_CONFIG_SNAPSHOT.json --production-symbol-state LOCAL_SYMBOL_STATE_SNAPSHOT.json --output PRIVATE_RESEARCH_UNIVERSE.json`. These are *existing trusted snapshots*; do not upload full server config or state to a public repository.

**Historical caveat:** A current production snapshot is NOT a point-in-time selection for past years. For valid WF/OOS, capture/reconstruct historical dated selector snapshots and use only information available at those dates. Existing 35-symbol exact-signal cache cannot be relabeled as a new 30-symbol dynamic backtest. No historical parity or full 30-symbol backtest is claimed.
