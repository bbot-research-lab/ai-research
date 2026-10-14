import base64
import tempfile
import unittest
from pathlib import Path
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_snapshot import snapshot
from research_addon.checkpoint_publish_guard import prepare_checkpoint

class PublishGuardTest(unittest.TestCase):
    def test_verified_snapshot_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with ExperimentLedger(root/"live/training_ledger.sqlite3") as ledger:
                ledger.record(identity="trial", frame="6h", status="FAILED",
                              spec={"x":1}, outcome={"reason":"synthetic"})
            snapshot(root/"live", root/"snap")
            key = base64.b64encode(b"q"*32).decode()
            index = prepare_checkpoint("6h", root/"snap", key, root/"store")
            self.assertEqual(index["frame"], "6h")
            with open(root/"snap/training_ledger.sqlite3", "ab") as file:
                file.write(b"corruption")
            with self.assertRaises(ValueError):
                prepare_checkpoint("6h", root/"snap", key, root/"store")
if __name__=="__main__":
    unittest.main()
