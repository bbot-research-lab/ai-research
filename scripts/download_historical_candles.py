"""Download authentic Binance USD-M futures candles into original B-BOT Parquet paths.
No private API, credentials, synthetic fill, production trading or deployment.
Requires pandas, pyarrow and requests. Fails if any requested day is unavailable.
"""
import argparse, hashlib, io, json, math, re, zipfile
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
    frame=pd.read_csv(io.BytesIO(raw),header=None,names=COLS[:6],usecols=list(range(6)),dtype=str)
    if len(frame) and frame.iloc[0,0].strip().lower().replace(" ","_")=="open_time":
        frame=frame.iloc[1:].copy()
    for column in COLS[:6]:
        frame[column]=pd.to_numeric(frame[column],errors="raise")
    return frame


# -------------------------- Data integrity ---------------------------------
def expected_bounds(tf,start,end):
    """First and last candle open times strictly within UTC [start,end)."""
    if tf in STEP:
        step=STEP[tf]
        anchor=345600 if tf=="1w" else 0  # Binance UTC Monday weekly open
        first=math.ceil((start.timestamp()-anchor)/step)*step+anchor
        last=math.floor((end.timestamp()-1-anchor)/step)*step+anchor
        return (int(first),int(last))
    # Binance 1mo candles always open at 00:00 UTC on the first of each month.
    first=start.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    if first<start:
        first=(first.replace(day=28)+timedelta(days=4)).replace(day=1)
    last=(end-timedelta(microseconds=1)).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    return (int(first.timestamp()),int(last.timestamp()))

def verify_frame(df,tf,start,end,allow_extra=False):
    if not {"open_time","open","high","low","close","volume"}.issubset(df.columns):
        raise ValueError("missing original OHLCV columns")
    if df.empty:
        raise ValueError("empty archive")
    if df.open_time.isna().any() or df.open_time.duplicated().any():
        raise ValueError("duplicate or missing archived timestamps")
    df=df.sort_values("open_time")
    if not df.open_time.is_monotonic_increasing:
        raise ValueError("historical timestamps not increasing")
    first,last=expected_bounds(tf,start,end)
    lo,hi=int(df.open_time.iloc[0]),int(df.open_time.iloc[-1])
    if first>last or (lo>first or hi<last if allow_extra else (lo!=first or hi!=last)):
        raise ValueError(f"historical window incomplete: expected {first}..{last}, got {lo}..{hi}")
    for field in ("open","high","low","close","volume"):
        values=pd.to_numeric(df[field],errors="raise")
        if not values.map(math.isfinite).all():
            raise ValueError("non-finite historical OHLCV: "+field)
        if field=="volume":
            if (values<0).any():raise ValueError("negative historical volume")
        elif (values<=0).any():
            raise ValueError("nonpositive historical price")
    if ((df.high<df[["open","close","low"]].max(axis=1))|
        (df.low>df[["open","close"]].min(axis=1))).any():
        raise ValueError("inconsistent OHLC candles")
    if tf in STEP and (df.open_time.diff().dropna()!=STEP[tf]).any():
        raise ValueError("gaps in historical bars; not interpolating")
    if tf=="1M":
        months=pd.to_datetime(df.open_time,unit="s",utc=True).dt.to_period("M")
        if (months.astype(int).diff().dropna()!=1).any():
            raise ValueError("missing monthly candle")
    return df

def download_history_plan(plan_path,root,timeframes,session=None):
    """Build original private Parquet files for every symbol seen in dated rotations."""
    plan=json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if plan.get("target_total")!=30 or plan.get("promotion_allowed") is not False:
        raise ValueError("not a research-only 30-symbol rotation plan")
    windows=plan.get("windows")
    if not isinstance(windows,list) or not windows:
        raise ValueError("empty historical rotation plan")
    from_start=datetime.fromisoformat(plan["start"].replace("Z","+00:00"))
    to_end=datetime.fromisoformat(plan["end"].replace("Z","+00:00"))
    if from_start.tzinfo is None or to_end.tzinfo is None:
        raise ValueError("UTC rotation bounds required")
    cursor=from_start
    needed={}
    for window in windows:
        a=datetime.fromisoformat(window["start"].replace("Z","+00:00"))
        b=datetime.fromisoformat(window["end"].replace("Z","+00:00"))
        selected=window.get("symbols")
        if a.tzinfo is None or b.tzinfo is None or a.utcoffset()!=timedelta(0) or b.utcoffset()!=timedelta(0):
            raise ValueError("UTC rotation bounds required")
        if a!=cursor or not a<b or b>to_end or not isinstance(selected,list) or len(selected)!=30 or len(set(selected))!=30:
            raise ValueError("invalid/gapped historical rotation windows")
        for symbol in selected:
            if not isinstance(symbol,str) or not re.fullmatch("[A-Z0-9]{4,30}",symbol):
                raise ValueError("invalid archived research symbol")
            previous=needed.get(symbol,(a,b))
            needed[symbol]=(min(a,previous[0]),max(b,previous[1]))
        cursor=b
    if cursor!=to_end or not timeframes or any(tf not in INTERVAL for tf in timeframes):
        raise ValueError("invalid historical coverage or intervals")
    report=[]
    for symbol,(start,end) in sorted(needed.items()):
        for tf in dict.fromkeys(timeframes):
            path=Path(root)/"data"/"candles"/symbol/(tf+".parquet")
            if path.exists():
                existing=pd.read_parquet(path)
                verify_frame(existing,tf,start,end,allow_extra=True)
                report.append({"symbol":symbol,"tf":tf,"path":str(path),"reused":True})
            else:
                info=download(symbol,tf,start,end,root,session=session)
                report.append({"symbol":symbol,"tf":tf,**info,"reused":False})
    return report

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
    df=df.sort_values("open_time").reset_index(drop=True)
    if df.open_time.duplicated().any():
        raise ValueError("duplicate archived timestamps")
    df=df[(df.open_time>=int(start.timestamp()))&(df.open_time<int(end.timestamp()))].copy()
    verify_frame(df,tf,start,end)
    target=Path(root)/"data"/"candles"/symbol/("1M" if tf=="1M" else tf)
    target=target.with_suffix(".parquet")
    if target.exists(): raise FileExistsError(str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    df.to_parquet(target,index=False)
    return {"path":str(target),"rows":len(df),"first_ts":int(df.open_time.iloc[0]),"last_ts":int(df.open_time.iloc[-1])}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--symbol");p.add_argument("--tf",choices=list(INTERVAL))
    p.add_argument("--start",default="2020-01-01");p.add_argument("--end",default="2026-08-21")
    p.add_argument("--history-plan",type=Path,help="Dated selection plan from dynamic_symbol_selection.py")
    p.add_argument("--timeframes",nargs="+",choices=list(INTERVAL),default=["1h","6h","12h","1d","1w","1M"])
    p.add_argument("--root",required=True)
    a=p.parse_args()
    if a.history_plan:
        if a.symbol or a.tf:p.error("history plan cannot be combined with single symbol options")
        for item in download_history_plan(a.history_plan,a.root,a.timeframes):
            print(item)
    else:
        if not(a.symbol and a.tf):p.error("single download requires --symbol and --tf")
        parse=lambda x:datetime.fromisoformat(x).replace(tzinfo=timezone.utc)
        print(download(a.symbol,a.tf,parse(a.start),parse(a.end),a.root))
