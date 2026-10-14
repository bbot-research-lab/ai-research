import base64
import subprocess
import tempfile
import unittest
from pathlib import Path
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame,commit_and_push
from research_addon.migrate_remote_synthetic import migrate_remote
from research_addon.remote_state_checker import check_remote_state

class RemoteMigrationTests(unittest.TestCase):
    def test_legacy_remote_roundtrip_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            remote=p/"remote.git"
            subprocess.run(["git","init","--bare",str(remote)],check=True,capture_output=True)
            key=base64.b64encode(b"a"*32).decode()
            state=p/"live"
            with ExperimentLedger(state/"6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="failed",frame="6h",status="FAILED",
                              spec={"test":1},outcome={"reason":"synthetic"})
                ledger.record(identity="completed",frame="6h",status="COMPLETED",
                              spec={"test":2},outcome={"score":3})
            checkout=p/"checkout"
            checkout_frame(remote,"6h",checkout)
            commit_and_push("6h",state,checkout,key,allow_initial_seed=True)
            original_sha=subprocess.run(["git","-C",str(checkout),"rev-parse","HEAD"],check=True,capture_output=True,text=True).stdout.strip()
            with self.assertRaises(PermissionError):
                migrate_remote("6h",remote,key,expected_remote_sha=original_sha)
            with self.assertRaises(RuntimeError):
                migrate_remote("6h",remote,key,operator_approved=True,expected_remote_sha="0"*40)
            migrated=migrate_remote("6h",remote,key,operator_approved=True,expected_remote_sha=original_sha)
            self.assertTrue(migrated["migrated"])
            self.assertEqual(migrated["retained_records"],2)
            result=check_remote_state("6h",remote,key)
            self.assertEqual(result["records"],2)
            self.assertEqual(result["hop"],0)
            current_sha=subprocess.run(["git","ls-remote",str(remote),"refs/heads/synthetic-frame-state-6h"],check=True,capture_output=True,text=True).stdout.split()[0]
            self.assertFalse(migrate_remote("6h",remote,key,operator_approved=True,expected_remote_sha=current_sha)["migrated"])
if __name__=="__main__":
    unittest.main()
