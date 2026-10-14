import base64
import tempfile
import unittest
from pathlib import Path
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_snapshot import snapshot
from research_addon.remote_frame_objects import publish_bundle, recover_bundle

KEY = base64.b64encode(b"r" * 32).decode()

class RemoteFrameObjectTests(unittest.TestCase):
    def test_index_roundtrip_and_corrupt_object(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with ExperimentLedger(root / "work/training_ledger.sqlite3") as ledger:
                ledger.record(identity="first", frame="1h", status="FAILED",
                              spec={"name": "test"}, outcome={"reason": "test-only"})
            snapshot(root / "work", root / "snap")
            index = publish_bundle("1h", root / "snap", KEY, root / "objects")
            recover_bundle(index, root / "objects", KEY, root / "restored")
            with ExperimentLedger(root / "restored/training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.get("first")["status"], "FAILED")
            damaged = root / "objects" / (index["object"] + ".enc")
            damaged.write_bytes(damaged.read_bytes() + b"x")
            with self.assertRaises(ValueError):
                recover_bundle(index, root / "objects", KEY, root / "corrupt")

if __name__ == "__main__":
    unittest.main()
