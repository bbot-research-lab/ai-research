import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.staged_official_replay import stage, SOURCE_FILES, EXTRA_FILES, MODULES

class OfficialStageTests(unittest.TestCase):
    def test_missing_modules_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name,expected in [("src.zip",SOURCE_FILES),("required.zip",EXTRA_FILES),("modules.zip",MODULES)]:
                with zipfile.ZipFile(root/name,"w") as z:
                    for x in expected:
                        if x!="stoch.py": z.writestr(x,"fixture")
            with self.assertRaises(ValueError):
                stage(root/"src.zip",root/"required.zip",root/"modules.zip",root/"staged")

if __name__=="__main__":unittest.main()
