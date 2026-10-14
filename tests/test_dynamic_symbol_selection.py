import tempfile
import unittest
from pathlib import Path
from scripts.dynamic_symbol_selection import DEFAULT_FIXED,from_official_state,write_selection

class ProductionParityTests(unittest.TestCase):
    def setUp(self):
        self.dynamic=[f"ALT{i:02d}USDT" for i in range(25)]
        all_symbols=DEFAULT_FIXED+self.dynamic
        self.cfg={"SYMBOLS":{s:True for s in all_symbols}}
        self.state={"_meta":{"final_dynamic":self.dynamic,"total_output_target":35}}
    def test_exactly_30_selected_in_original_server_order(self):
        self.assertEqual(from_official_state(self.cfg,self.state),
                         DEFAULT_FIXED+self.dynamic[:20])
    def test_fixed_override_from_production_config(self):
        cfg=dict(self.cfg,FIXED_SYMBOLS=["BTCUSDT","ETHUSDT"])
        with self.assertRaises(ValueError):
            from_official_state(cfg,self.state)  # 2 + 25 < 30, no invented fill
    def test_no_fabricated_fills(self):
        with self.assertRaises(ValueError):
            from_official_state(self.cfg,{"_meta":{"final_dynamic":[]}})
    def test_missing_production_state_fails_closed(self):
        with self.assertRaises(ValueError):
            from_official_state(self.cfg,{})
    def test_snapshot_does_not_authorize_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"selected.json"
            write_selection(path,from_official_state(self.cfg,self.state))
            self.assertIn('"promotion_allowed": false',path.read_text())
            with self.assertRaises(FileExistsError):
                write_selection(path,[])
if __name__=="__main__":unittest.main()
