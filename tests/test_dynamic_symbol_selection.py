import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from scripts.dynamic_symbol_selection import select_current_symbols,write_selection

class Fake:
    def __init__(self,data):self.data=data
    def json(self):return self.data
    def raise_for_status(self):pass
class Session:
    def get(self,url,timeout=25):
        if "exchangeInfo" in url:
            return Fake({"symbols":[
                {"symbol":"AAAUSDT","status":"TRADING","contractType":"PERPETUAL","quoteAsset":"USDT"},
                {"symbol":"BBBUSDT","status":"TRADING","contractType":"PERPETUAL","quoteAsset":"USDT"},
                {"symbol":"OLDUSDT","status":"BREAK","contractType":"PERPETUAL","quoteAsset":"USDT"},
                {"symbol":"CCCUSDT","status":"TRADING","contractType":"CURRENT_QUARTER","quoteAsset":"USDT"}]})
        return Fake([{"symbol":"BBBUSDT","quoteVolume":"900"},
                     {"symbol":"AAAUSDT","quoteVolume":"1000"},
                     {"symbol":"OLDUSDT","quoteVolume":"999999"}])
class DynamicSymbolTests(unittest.TestCase):
    def test_auto_select_ranked_and_filter_inactive(self):
        self.assertEqual(select_current_symbols(Session(),limit=2),["AAAUSDT","BBBUSDT"])
    def test_not_fixed_count_when_fewer_eligible(self):
        self.assertEqual(len(select_current_symbols(Session(),limit=20)),2)
    def test_requires_valid_limit(self):
        with self.assertRaises(ValueError):select_current_symbols(Session(),limit=0)
    def test_snapshot_not_promotion_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"universe.json"
            write_selection(p,["AAAUSDT"])
            self.assertIn('"promotion_allowed": false',p.read_text())
            with self.assertRaises(FileExistsError):write_selection(p,["BBBUSDT"])
if __name__=="__main__":unittest.main()
