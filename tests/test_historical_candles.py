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

    def test_halfhour_boundary_and_missing_bar_rejected(self):
        import pandas as pd
        from scripts.download_historical_candles import verify_frame
        a=datetime(2021,1,1,tzinfo=timezone.utc)
        b=datetime(2021,1,1,1,30,tzinfo=timezone.utc)
        times=[int(a.timestamp())+i*1800 for i in range(3)]
        data=pd.DataFrame({"open_time":times,"open":[1.0]*3,"high":[2.0]*3,
                           "low":[0.5]*3,"close":[1.5]*3,"volume":[10.0]*3})
        self.assertEqual(expected_bounds("30m",a,b),(times[0],times[-1]))
        self.assertEqual(len(verify_frame(data,"30m",a,b)),3)
        with self.assertRaisesRegex(ValueError,"gaps"):
            verify_frame(data.drop(index=1),"30m",a,b)
        self.assertIn("/30m/",url("BTCUSDT","30m",a))

    def test_monthly_gap_recovers_only_from_checksum_verified_daily_archive(self):
        import pandas as pd
        def archive(times):
            buff=io.BytesIO()
            content="\n".join(f"{t},1,2,0.5,1.5,10" for t in times)
            with zipfile.ZipFile(buff,"w") as z:z.writestr("AAVEUSDT-12h.csv",content)
            return buff.getvalue()
        first=1609459200000;second=first+43200000
        monthly=archive([first]);daily=archive([first,second])
        class DailySession:
            def get(self,source_url,timeout=90):
                return FakeSession(daily if "/daily/" in source_url else monthly).get(source_url,timeout)
        start=datetime(2021,1,1,tzinfo=timezone.utc)
        end=datetime(2021,1,2,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            out=download("AAVEUSDT","12h",start,end,tmp,session=DailySession())
            self.assertEqual(pd.read_parquet(out['path']).open_time.tolist(),[first//1000,second//1000])
        # A verified daily file with the same gap must still fail; never invent a candle.
        daily=monthly
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"incomplete"):
                download("AAVEUSDT","12h",start,end,tmp,session=DailySession())
            self.assertFalse((Path(tmp)/"data/candles/AAVEUSDT/12h.parquet").exists())

    def test_daily_recovery_wrong_day_and_corrupt_checksum_are_rejected(self):
        def archive(times):
            buff=io.BytesIO()
            with zipfile.ZipFile(buff,"w") as z:
                z.writestr("AAVEUSDT-12h.csv","\n".join(f"{t},1,2,0.5,1.5,10" for t in times))
            return buff.getvalue()
        monthly=archive([1609459200000])
        daily=archive([1609545600000,1609588800000])
        corrupt=False
        class DailySession:
            def get(self,source_url,timeout=90):
                response=FakeSession(daily if "/daily/" in source_url else monthly).get(source_url,timeout)
                if corrupt and "/daily/" in source_url and source_url.endswith('.CHECKSUM'):
                    response.text='0'*64
                return response
        start=datetime(2021,1,1,tzinfo=timezone.utc);end=datetime(2021,1,2,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"wrong UTC day"):
                download("AAVEUSDT","12h",start,end,tmp,session=DailySession())
        corrupt=True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"checksum"):
                download("AAVEUSDT","12h",start,end,tmp,session=DailySession())

    def test_weekly_boundaries_use_monday(self):
        a=datetime(2021,1,4,tzinfo=timezone.utc)
        b=datetime(2021,1,18,tzinfo=timezone.utc)
        first,last=expected_bounds("1w",a,b)
        self.assertEqual(first,int(a.timestamp()))
        self.assertEqual(last,int(datetime(2021,1,11,tzinfo=timezone.utc).timestamp()))

    def test_weekly_bars_require_all_verified_daily_constituents(self):
        import pandas as pd
        first=1609718400000
        rows=[f"{first+i*86400000},1,2,0.5,1.5,10" for i in range(14)]
        def archive(lines):
            buff=io.BytesIO()
            with zipfile.ZipFile(buff,'w') as z:z.writestr('fixture.csv','\n'.join(lines))
            return buff.getvalue()
        start=datetime(2021,1,4,tzinfo=timezone.utc);end=datetime(2021,1,18,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            info=download('AAVEUSDT','1w',start,end,tmp,session=FakeSession(archive(rows)))
            weekly=pd.read_parquet(info['path'])
            self.assertEqual(weekly.open_time.tolist(),[first//1000,first//1000+604800])
            self.assertEqual(weekly.volume.tolist(),[70,70])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download('AAVEUSDT','1w',start,end,tmp,session=FakeSession(archive(rows[:3]+rows[4:])))
            self.assertFalse((Path(tmp)/'data/candles/AAVEUSDT/1w.parquet').exists())

    def test_cached_history_extends_without_changing_existing_bars(self):
        import pandas as pd
        from scripts.download_historical_candles import prewarm_official_history
        first=1609459200000
        buff=io.BytesIO()
        with zipfile.ZipFile(buff,'w') as z:
            z.writestr('fixture.csv','\n'.join(f'{first+i*3600000},1,2,0.5,1.5,10' for i in range(3)))
        session=FakeSession(buff.getvalue())
        start=datetime(2021,1,1,tzinfo=timezone.utc);mid=datetime(2021,1,1,2,tzinfo=timezone.utc);end=datetime(2021,1,1,3,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            info=download('AAVEUSDT','1h',start,mid,tmp,session=session)
            original=pd.read_parquet(info['path'])
            records=prewarm_official_history(['AAVEUSDT'],tmp,start,end,['1h'],session=session)
            self.assertNotEqual(records[0]['state'],'FAILED')
            extended=pd.read_parquet(info['path'])
            pd.testing.assert_frame_equal(original,extended.iloc[:2].reset_index(drop=True))
            self.assertEqual(len(extended),3)
if __name__=="__main__":unittest.main()

