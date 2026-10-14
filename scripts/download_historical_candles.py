"""Download authentic Binance USD-M futures candles into original B-BOT Parquet paths.
No private API, credentials, synthetic fill, production trading or deployment.
Requires pandas, pyarrow and requests. Fails if any requested day is unavailable.
"""
import argparse, hashlib, io, re, zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import requests

BASE="https://data.binance.vision/data/futures/um"
INTERVAL={"1h":"1h","6h":"6h","12h":"12h","1d":"1d","1w":"1w","1M":"1mo"}
COLS=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
STEP={"1h":3600,"6h":21600,"12h":43200,"1d":86400,"1w":604800}

def url(symbol,tf,date,monthly=True):
    group="monthly" if monthly else "daily"
    fmt="%Y-%m" if monthly else "%Y-%m-%d"
    stamp=date.strftime(fmt)
    name=f"{symbol}-{tf}-{stamp}"
    return f"{BASE}/{group}/klines/{symbol}/{tf}/{name}.zip"

def fetch(session, source_url):
    result=session.get(source_url,timeout=90)
    if result.status_code==404: return None
    result.raise_for_status()
    check=session.get(source_url+".CHECKSUM",timeout=30)
    check.raise_for_status()
    digest=check.text.strip().split()[0].lower()
    if not re.fullmatch("[0-9a-f]{64}",digest) or hashlib.sha256(result.content).hexdigest()!=digest:
        raise ValueError("public archive checksum mismatch: "+source_url)
    with zipfile.ZipFile(io.BytesIO(result.content)) as z:
        files=[x for x in z.namelist() if x.endswith(".csv") and "/" not in x and "\\" not in x]
        if len(files)!=1: raise ValueError("unrecognized public archive contents")
        raw=z.read(files[0])
    frame=pd.read_csv(io.BytesIO(raw),header=None,names=COLS,usecols=list(range(6)),dtype=str)
    if len(frame) and frame.iloc[0,0].strip().lower().replace(" ","_")=="open_time":
        frame=frame.iloc[1:].copy()
    for column in COLS[:6]:
        frame[column]=pd.to_numeric(frame[column],errors="raise")
    return frame

def download(symbol,tf,start,end,root,session=None):
    if not re.fullmatch("[A-Z0-9]{4,30}",symbol): raise ValueError("invalid symbol")
    if tf not in INTERVAL: raise ValueError("unsupported interval")
    if start.tzinfo is None or end.tzinfo is None or start>=end: raise ValueError("invalid UTC window")
    start,end=start.astimezone(timezone.utc),end.astimezone(timezone.utc)
    if end>datetime.now(timezone.utc): raise ValueError("cannot fetch incomplete future data")
    s=session or requests.Session()
    current=start.replace(day=1)
    frames=[];missing=[]
    while current < end:
        next_month=(current.replace(day=28)+timedelta(days=4)).replace(day=1)
        f=fetch(s,url(symbol,INTERVAL[tf],current))
        if f is None:
            day=max(start.date(),current.date())
            last=min((end-timedelta(microseconds=1)).date(),(next_month-timedelta(days=1)).date())
            pieces=[]
            while day<=last:
                p=fetch(s,url(symbol,INTERVAL[tf],datetime(day.year,day.month,day.day),monthly=False))
                if p is None: missing.append(day.isoformat())
                else: pieces.append(p)
                day += timedelta(days=1)
            if pieces: f=pd.concat(pieces,ignore_index=True)
        if f is not None and len(f): frames.append(f)
        current=next_month
    if missing: raise ValueError(f"missing {len(missing)} archive days; first: {missing[:5]}")
    if not frames: raise ValueError("no authentic archived bars")
    df=pd.concat(frames,ignore_index=True)
    t=pd.to_numeric(df["open_time"],errors="raise")
    if t.abs().median()>10**14: t=t//1000  # microseconds -> milliseconds
    df["open_time"]=(t//1000).astype("int64")  # milliseconds -> seconds
    df=df.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)
    df=df[(df.open_time>=int(start.timestamp()))&(df.open_time<int(end.timestamp()))].copy()
    if df.empty: raise ValueError("no bars in selected time window")
    if tf in STEP:
        breaks=df.open_time.diff().dropna()
        if (breaks!=STEP[tf]).any(): raise ValueError("gaps in historical bars; not interpolating")
    target=Path(root)/"data"/"candles"/symbol/("1M" if tf=="1M" else tf)
    target=target.with_suffix(".parquet")
    if target.exists(): raise FileExistsError(str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    df.to_parquet(target,index=False)
    return {"path":str(target),"rows":len(df),"first_ts":int(df.open_time.iloc[0]),"last_ts":int(df.open_time.iloc[-1])}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",required=True);p.add_argument("--tf",choices=list(INTERVAL),required=True)
    p.add_argument("--start",default="2020-01-01");p.add_argument("--end",default="2026-08-21")
    p.add_argument("--root",required=True)
    a=p.parse_args()
    parse=lambda x:datetime.fromisoformat(x).replace(tzinfo=timezone.utc)
    print(download(a.symbol,a.tf,parse(a.start),parse(a.end),a.root))
