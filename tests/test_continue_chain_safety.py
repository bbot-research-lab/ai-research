import base64
import datetime as dt
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame, commit_and_push

class ContinueChainSafetyTests(unittest.TestCase):
    def test_remote_state_present_but_dispatch_disabled(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)
            remote=p/"remote.git"
            subprocess.run(["git","init","--bare",str(remote)],check=True,
                           capture_output=True)
            root=p/"root"
            with ExperimentLedger(root/"6h/training_ledger.sqlite3") as ledger:
                ledger.record(identity="test",frame="6h",status="FAILED",
                              spec={"synthetic":1},outcome={"reason":"test"})
            worktree=p/"worktree"
            self.assertFalse(checkout_frame(remote,"6h",worktree))
            key=base64.b64encode(b"k"*32).decode()
            commit_and_push("6h",root,worktree,key,allow_initial_seed=True)
            env=dict(os.environ,BBOT_SYNTHETIC_CHAIN_ENABLED="false",
                     BBOT_RESEARCH_STATE_KEY=key)
            env.pop("GH_TOKEN",None)
            result=subprocess.run([sys.executable,"-m","research_addon.continue_hosted_chain",
                                   "--frame","6h","--hop","0",
                                   "--remote",str(remote),"--result","success","--previous-run-id","1"],
                                  env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("CHAIN_DISABLED",result.stdout)

if __name__=="__main__":
    unittest.main()
