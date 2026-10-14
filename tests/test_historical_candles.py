import hashlib,io,json,tempfile,unittest,zipfile
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import Mock,patch
from scripts.download_historical_candles import download,fetch,url,download_history_plan,expected_bounds

def fixture():
    content=("open_time,open,high,low,close,volume\n"
             "1609459200000,1,2,0.5,1.5,10\n"
             "1609462800000,1.5,2,1.0,1.8,12\n").encode()
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w") as z:z.writestr("AAVEUSDT-1h-2021-01.csv",content)
    return buff.getvalue()
class FakeSession:
    def __init__(self,blob):self.blob=blob
    def get(self,url,timeout=90):
        response=Mock();response.status_code=200
        response.content=self.blob
        response.text=hashlib.sha256(self.blob).hexdigest()+"  archive.zip"
        response.raise_for_status=lambda:None
        return response
class DownloadTests(unittest.TestCase):
    def test_url_binance_futures_not_spot(self):
        self.assertIn("/futures/um/monthly/klines/AAVEUSDT/1h/",url("AAVEUSDT","1h",datetime(2021,1,1)))
    def test_checksum_and_parquet_output(self):
        from research_addon.formal_cache_schema import REQUIRED_COLUMNS
        start=datetime(2021,1,1,tzinfo=timezone.utc)
        end=datetime(2021,1,1,2,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            result=download("AAVEUSDT","1h",start,end,tmp,session=FakeSession(fixture()))
            self.assertEqual(result["rows"],2)
            self.assertTrue(Path(result["path"]).exists())
            import pandas as pd
            data=pd.read_parquet(result["path"])
            self.assertEqual(data["open_time"].tolist(),[1609459200,1609462800])
            with self.assertRaises(FileExistsError):
                download("AAVEUSDT","1h",start,end,tmp,session=FakeSession(fixture()))
    def test_bad_checksum_fails(self):
        sess=FakeSession(fixture());orig=sess.get
        def broken(url,timeout=90):
            result=orig(url,timeout)
            if url.endswith(".CHECKSUM"):result.text="0"*64
            return result
        sess.get=broken
        with self.assertRaises(ValueError):fetch(sess,url("AAVEUSDT","1h",datetime(2021,1,1)))

    def test_missing_first_or_last_candle_fails_closed(self):
        start=datetime(2021,1,1,tzinfo=timezone.utc)
        end=datetime(2021,1,1,3,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"incomplete"):
                download("AAVEUSDT","1h",start,end,tmp,session=FakeSession(fixture()))
            self.assertFalse((Path(tmp)/"data/candles/AAVEUSDT/1h.parquet").exists())

    def test_rotation_downloads_unique_symbols_once(self):
        start="2021-01-01T00:00:00Z";mid="2021-01-02T00:00:00Z";end="2021-01-03T00:00:00Z"
        fixed=[f"AAA{i:02d}USDT" for i in range(29)]
        plan={"start":start,"end":end,"target_total":30,"promotion_allowed":False,
              "windows":[{"start":start,"end":mid,"symbols":fixed+["BTCUSDT"]},
                         {"start":mid,"end":end,"symbols":fixed+["ETHUSDT"]}]}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"plan.json";p.write_text(json.dumps(plan))
            with patch("scripts.download_historical_candles.download",return_value={"rows":1}) as dl:
                out=download_history_plan(p,tmp,["1h"])
            self.assertEqual(len(out),31)
            self.assertEqual(dl.call_count,31)
            self.assertEqual(next(c.args for c in dl.call_args_list if c.args[0]=="BTCUSDT")[2].date().isoformat(),"2021-01-01")
            self.assertEqual(next(c.args for c in dl.call_args_list if c.args[0]=="ETHUSDT")[2].date().isoformat(),"2021-01-02")
            plan["windows"][1]["start"]="2021-01-02T01:00:00Z"
            p.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                download_history_plan(p,tmp,["1h"])

    def test_weekly_boundaries_use_monday(self):
        a=datetime(2021,1,4,tzinfo=timezone.utc)
        b=datetime(2021,1,18,tzinfo=timezone.utc)
        first,last=expected_bounds("1w",a,b)
        self.assertEqual(first,int(a.timestamp()))
        self.assertEqual(last,int(datetime(2021,1,11,tzinfo=timezone.utc).timestamp()))
if __name__=="__main__":unittest.main()
