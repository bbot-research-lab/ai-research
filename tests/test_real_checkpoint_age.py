import base64
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from research_addon.experiment_ledger import ExperimentLedger
from research_addon.frame_remote_git import checkout_frame, commit_and_push
from research_addon.continue_hosted_chain import main

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
            env=dict(os.environ,GIT_AUTHOR_DATE="2001-01-01T00:00:00+00:00",
                     GIT_COMMITTER_DATE="2001-01-01T00:00:00+00:00")
            subprocess.run(["git","-C",str(checkout),"commit","--amend",
                            "--no-edit","--date","2001-01-01T00:00:00+00:00"],
                           env=env,check=True,capture_output=True)
            subprocess.run(["git","-C",str(checkout),"push","--force","origin",
                            "HEAD:refs/heads/synthetic-frame-state-6h"],
                           check=True,capture_output=True)
            argv=["continue_hosted_chain","--frame","6h","--hop","1",
                  "--remote",str(remote),"--result","success",
                  "--previous-run-id","1"]
            with patch.object(sys,"argv",argv), patch.dict(os.environ,{
                "BBOT_SYNTHETIC_CHAIN_ENABLED":"true",
                "BBOT_RESEARCH_STATE_KEY":key,"GH_TOKEN":"mock-not-used"
            }), patch("research_addon.continue_hosted_chain.verify_predecessor",return_value=True), patch("research_addon.continue_hosted_chain.verify_frame_job",return_value=True), patch(
                "research_addon.continue_hosted_chain.dispatch_next",return_value=None
            ) as mocked:
                self.assertEqual(main(),0)
                self.assertEqual(mocked.call_args.kwargs["last_checkpoint_at"][:4],"2001")

if __name__=="__main__":
    unittest.main()
