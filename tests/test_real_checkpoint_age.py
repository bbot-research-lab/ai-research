import base64
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame, commit_and_push

class RealTimestampChainTests(unittest.TestCase):
    def test_stale_verified_checkpoint_cannot_dispatch(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            remote=root/"bare.git"
            subprocess.run(["git","init","--bare",str(remote)],check=True,capture_output=True)
            dbroot=root/"data"
            with ExperimentLedger(dbroot/"6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="old",frame="6h",status="FAILED",
                              spec={"synthetic":True},outcome={"reason":"test"})
            checkout=root/"checkout"
            self.assertFalse(checkout_frame(remote,"6h",checkout))
            key=base64.b64encode(b"p"*32).decode()
            commit_and_push("6h",dbroot,checkout,key,allow_initial_seed=True)
            # With enabled chain, check the real remote commit rather than
            # replacing its timestamp with current time.
            env=dict(os.environ,BBOT_SYNTHETIC_CHAIN_ENABLED="true",
                     BBOT_RESEARCH_STATE_KEY=key, GH_TOKEN="mock-not-used")
            env["GIT_AUTHOR_DATE"]="2001-01-01T00:00:00+00:00"
            env["GIT_COMMITTER_DATE"]="2001-01-01T00:00:00+00:00"
            # Rewrite remote branch commit timestamp without changing ciphertext.
            subprocess.run(["git","-C",str(checkout),"commit","--amend",
                            "--no-edit","--date","2001-01-01T00:00:00+00:00"],
                           env=env,check=True,capture_output=True)
            subprocess.run(["git","-C",str(checkout),"push","--force","origin",
                            "HEAD:refs/heads/synthetic-frame-state-6h"],
                           check=True,capture_output=True)
            proc=subprocess.run([sys.executable,"-m","research_addon.continue_hosted_chain",
                                 "--frame","6h","--hop","1","--remote",str(remote),
                                 "--result","success"],env=env,capture_output=True,text=True,timeout=30)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertIn("CHAIN_STOPPED",proc.stdout)

if __name__=="__main__":
    unittest.main()
