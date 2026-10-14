import base64
import tempfile
import unittest
from pathlib import Path
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_snapshot import snapshot
from research_addon.encrypted_frame_transport import seal, unseal, file_identity

KEY = base64.b64encode(b"k" * 32).decode()

class EncryptedTransportTests(unittest.TestCase):
    def test_authenticated_roundtrip_tamper_and_frame_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with ExperimentLedger(root / "live/training_ledger.sqlite3") as db:
                db.record(identity="x", frame="6h", status="FAILED",
                          spec={"x": 1}, outcome={"reason": "bad synthetic"})
            snapshot(root / "live", root / "snapshot")
            blob = seal("6h", root / "snapshot", KEY)
            self.assertEqual(file_identity(blob)["size"], len(blob))
            unseal("6h", blob, KEY, root / "restored")
            with ExperimentLedger(root / "restored/training_ledger.sqlite3") as db:
                self.assertEqual(db.get("x")["status"], "FAILED")
            with self.assertRaises(ValueError):
                unseal("1h", blob, KEY, root / "wrongframe")
            tamper = bytearray(blob)
            tamper[-1] ^= 1
            with self.assertRaises(ValueError):
                unseal("6h", bytes(tamper), KEY, root / "tampered")
            with self.assertRaises(ValueError):
                unseal("6h", blob, base64.b64encode(b"z" * 32).decode(), root / "wrongkey")

if __name__ == "__main__":
    unittest.main()
