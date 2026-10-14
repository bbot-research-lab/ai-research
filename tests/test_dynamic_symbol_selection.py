import tempfile
import unittest
from pathlib import Path
import json
from scripts.dynamic_symbol_selection import DEFAULT_FIXED,from_official_state,write_selection,capture_production_state,replay_historical_rotations

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

    def test_capture_is_sanitized_and_replay_follows_real_rotation_order(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            first=base/"a.json"
            capture_production_state({**self.cfg,"API_SECRET":"must_not_copy"},self.state,first)
            self.assertNotIn("must_not_copy",first.read_text())
            initial=json.loads(first.read_text())
            initial["captured_at"]=initial["effective_at"]="2025-01-01T00:00:00Z"
            first.write_text(json.dumps(initial))
            second=base/"b.json"
            reordered={"_meta":{"final_dynamic":list(reversed(self.dynamic))}}
            capture_production_state(self.cfg,reordered,second)
            subsequent=json.loads(second.read_text())
            subsequent["captured_at"]=subsequent["effective_at"]="2025-01-03T00:00:00Z"
            second.write_text(json.dumps(subsequent))
            plan=replay_historical_rotations(base,"2025-01-02T00:00:00Z","2025-01-05T00:00:00Z")
            self.assertEqual(len(plan["windows"]),2)
            self.assertEqual(plan["windows"][0]["symbols"],DEFAULT_FIXED+self.dynamic[:20])
            self.assertEqual(plan["windows"][1]["symbols"],DEFAULT_FIXED+list(reversed(self.dynamic))[:20])
            self.assertFalse(plan["promotion_allowed"])
            self.assertFalse(plan["history_complete_verified"])
            with self.assertRaises(ValueError):
                replay_historical_rotations(base,"2024-12-31T00:00:00Z","2025-01-05T00:00:00Z")
            subsequent["captured_at"]="2025-01-04T00:00:00Z"
            second.write_text(json.dumps(subsequent))
            with self.assertRaises(ValueError):
                replay_historical_rotations(base,"2025-01-02T00:00:00Z","2025-01-05T00:00:00Z")
if __name__=="__main__":unittest.main()
