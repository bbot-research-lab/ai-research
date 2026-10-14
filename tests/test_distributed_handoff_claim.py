import subprocess
import tempfile
import unittest
from pathlib import Path
from research_addon.distributed_handoff_claim import claim_remote,claim_ref

class DistributedClaimTests(unittest.TestCase):
    def test_cross_worktree_duplicate_rejected_by_bare_git_remote(self):
        with tempfile.TemporaryDirectory() as temp:
            remote=Path(temp)/"claims.git"
            subprocess.run(["git","init","--bare",str(remote)],check=True,capture_output=True)
            first=claim_remote(str(remote),"6h",100,2)
            self.assertEqual(first,claim_ref("6h",100,2))
            with self.assertRaises(RuntimeError):
                claim_remote(str(remote),"6h",100,2)
            claim_remote(str(remote),"6h",101,2)
            claim_remote(str(remote),"1h",100,2)
            listing=subprocess.run(["git","ls-remote","--heads",str(remote)],check=True,capture_output=True,text=True).stdout
            self.assertEqual(listing.count("synthetic-handoff-claim-"),3)
    def test_invalid_input_fails_before_remote_access(self):
        with self.assertRaises(ValueError):
            claim_remote("/missing","5m",100,1)
        with self.assertRaises(ValueError):
            claim_remote("/missing","6h",0,1)

if __name__=="__main__":
    unittest.main()
