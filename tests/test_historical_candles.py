import hashlib,io,tempfile,unittest,zipfile
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import Mock
from scripts.download_historical_candles import download,fetch,url

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
if __name__=="__main__":unittest.main()
