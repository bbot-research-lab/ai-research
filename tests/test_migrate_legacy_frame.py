import tempfile
import unittest
from pathlib import Path
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.migrate_legacy_frame import migrate_legacy_frame
from research_addon.continuation_receipt import read_hop

class LegacyMigrationTests(unittest.TestCase):
    def test_requires_explicit_approval_and_preserves_failed_and_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with ExperimentLedger(root/"training_ledger.sqlite3") as ledger:
                ledger.record(identity="bad",frame="6h",status="FAILED",
                              spec={"name":"bad"},outcome={"reason":"synthetic"})
                ledger.record(identity="good",frame="6h",status="COMPLETED",
                              spec={"name":"good"},outcome={"score":10})
            with self.assertRaises(PermissionError):
                migrate_legacy_frame("6h",root)
            result=migrate_legacy_frame("6h",root,operator_approved=True)
            self.assertEqual(result["retained_records"],2)
            self.assertEqual(read_hop(root,"6h",require_existing=True),0)
            with ExperimentLedger(root/"training_ledger.sqlite3") as ledger:
                self.assertEqual(ledger.get("bad")["status"],"FAILED")
                self.assertEqual(ledger.get("good")["status"],"COMPLETED")
            self.assertEqual(migrate_legacy_frame("6h",root,operator_approved=True),
                             {"migrated":False,"hop":0})
    def test_never_creates_empty_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                migrate_legacy_frame("6h",tmp,operator_approved=True)

if __name__=="__main__":
    unittest.main()
