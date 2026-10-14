import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

class ContinueHostedChainTests(unittest.TestCase):
    def test_default_disabled_requires_no_credentials_or_network(self):
        with TemporaryDirectory() as temp:
            env=dict(os.environ)
            env.pop("BBOT_SYNTHETIC_CHAIN_ENABLED",None)
            env.pop("GH_TOKEN",None)
            env.pop("BBOT_RESEARCH_STATE_KEY",None)
            result=subprocess.run([sys.executable,"-m",
                "research_addon.continue_hosted_chain","--frame","6h",
                "--hop","0","--remote",str(Path(temp)/"missing.git"),
                "--result","success","--previous-run-id","1"],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("CHAIN_DISABLED",result.stdout)

if __name__=="__main__":
    unittest.main()
