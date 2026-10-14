"""Automatic current Binance USD-M research universe (NOT historical point-in-time selection).

For contemporary exploratory research only. Never use today's rankings to
select a historical WF/SEALED universe; use original historical snapshots.
No credentials, account access, orders, or promotion.
"""
import argparse
import json
import re
from pathlib import Path
import requests

EXCHANGE_URL="https://fapi.binance.com/fapi/v1/exchangeInfo"
TICKER_URL="https://fapi.binance.com/fapi/v1/ticker/24hr"

def select_current_symbols(session=None, limit=35):
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError("limit must be 1..200")
    s=session or requests.Session()
    info=s.get(EXCHANGE_URL,timeout=25)
    info.raise_for_status()
    tickers=s.get(TICKER_URL,timeout=25)
    tickers.raise_for_status()
    eligible={
        item["symbol"] for item in info.json()["symbols"]
        if item.get("status")=="TRADING"
        and item.get("contractType")=="PERPETUAL"
        and item.get("quoteAsset")=="USDT"
        and re.fullmatch(r"[A-Z0-9]{4,30}",item.get("symbol",""))
    }
    ranked=[]
    for ticker in tickers.json():
        symbol=ticker.get("symbol")
        if symbol not in eligible: continue
        try: volume=float(ticker["quoteVolume"])
        except (ValueError,TypeError,KeyError): continue
        if not 0 <= volume < float("inf"): continue
        ranked.append((symbol,volume))
    ranked.sort(key=lambda p:(-p[1],p[0]))
    if not ranked: raise ValueError("no eligible current futures tickers")
    return [symbol for symbol,_ in ranked[:limit]]

def write_selection(path, symbols):
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): raise FileExistsError("refusing to overwrite reviewed universe snapshot")
    payload={"type":"CURRENT_DISCOVERY_ONLY","promotion_allowed":False,
             "historical_validation_universe":False,"symbols":symbols}
    target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--limit",type=int,default=35,help="Maximum candidates, not fixed membership")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=select_current_symbols(limit=a.limit)
    print("Dynamic current symbols:",", ".join(result))
    print("Saved:",write_selection(a.output,result))
