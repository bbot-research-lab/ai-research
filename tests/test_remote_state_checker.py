import base64
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame,commit_and_push
from research_addon.remote_state_checker import check_remote_state
from research_addon.continuation_receipt import write_hop

class RemoteStateCheckerTests(unittest.TestCase):
    def test_readonly_restoration_and_missing_frame(self):
        with TemporaryDirectory() as tmp:
            base=Path(tmp)
            remote=base/"remote.git"
            subprocess.run(["git","init","--bare",str(remote)],check=True,capture_output=True)
            key=base64.b64encode(b"y"*32).decode()
            self.assertEqual(check_remote_state("6h",remote,key),{"verified":False})
            with ExperimentLedger(base/"live/6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="failure",frame="6h",status="FAILED",
                              spec={"test":1},outcome={"reason":"synthetic"})
            write_hop(base/"live/6h","6h",0)
            worktree=base/"git"
            checkout_frame(remote,"6h",worktree)
            commit_and_push("6h",base/"live",worktree,key,allow_initial_seed=True)
            result=check_remote_state("6h",remote,key)
            self.assertTrue(result["verified"])
            self.assertEqual(result["records"],1)
            self.assertEqual(result["hop"],0)
            self.assertIn("timestamp",result)
            with self.assertRaises(ValueError):
                check_remote_state("6h",remote,base64.b64encode(b"x"*32).decode())

if __name__=="__main__":
    unittest.main()
