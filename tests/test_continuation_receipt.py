import base64
import tempfile
import unittest
from pathlib import Path

from research_addon.continuation_receipt import read_hop,write_hop
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_snapshot import snapshot
from research_addon.git_frame_checkpoint import stage_frame,restore_frame

class ContinuationReceiptTests(unittest.TestCase):
    def test_atomic_hop_and_encrypted_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            live=root/"live"
            with ExperimentLedger(live/"training_ledger.sqlite3") as ledger:
                ledger.record(identity="failed",frame="6h",status="FAILED",
                              spec={"case":"synthetic"},outcome={"reason":"synthetic"})
            write_hop(live,"6h",0)
            write_hop(live,"6h",1,expected_previous=0)
            with self.assertRaises(ValueError):
                write_hop(live,"6h",3,expected_previous=1)
            snapshot(live,root/"snap")
            key=base64.b64encode(b"m"*32).decode()
            stage_frame("6h",root/"snap",key,root/"store")
            self.assertTrue(restore_frame("6h",key,root/"store",root/"restored"))
            self.assertEqual(read_hop(root/"restored","6h",require_existing=True),1)
            with self.assertRaises(ValueError):
                read_hop(root/"restored","1h",require_existing=True)

    def test_missing_counter_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                read_hop(tmp,"6h",require_existing=True)

if __name__=="__main__":
    unittest.main()
