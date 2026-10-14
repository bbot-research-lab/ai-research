import tempfile
import unittest
from pathlib import Path
from research_addon.handoff_claim import claim_handoff

class HandoffClaimTests(unittest.TestCase):
    def test_first_claim_and_duplicate_refusal(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(claim_handoff(temp,frame="6h",run_id=42,hop=2))
            self.assertFalse(claim_handoff(temp,frame="6h",run_id=42,hop=2))
            self.assertTrue(claim_handoff(temp,frame="1h",run_id=42,hop=2))
            self.assertTrue(claim_handoff(temp,frame="6h",run_id=43,hop=2))
            self.assertEqual(len(list(Path(temp).glob("*.json"))),3)
    def test_reject_invalid_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            for kwargs in ({"frame":"6h","run_id":0,"hop":0},
                           {"frame":"6h","run_id":1,"hop":48},
                           {"frame":"5m","run_id":1,"hop":1},
                           {"frame":"6h","run_id":True,"hop":1}):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaises(ValueError):
                        claim_handoff(temp,**kwargs)
    def test_corrupt_existing_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(claim_handoff(temp,frame="6h",run_id=2,hop=1))
            (Path(temp)/"2-6h-1.json").write_text('{"bad":true}')
            with self.assertRaises(RuntimeError):
                claim_handoff(temp,frame="6h",run_id=2,hop=1)

if __name__=="__main__":
    unittest.main()
