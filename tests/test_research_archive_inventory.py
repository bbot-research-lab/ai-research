import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.research_archive_inventory import inventory

class InventoryTests(unittest.TestCase):
    def test_strategy_inside_results_is_counted(self):
        with tempfile.TemporaryDirectory() as td:
            archive=Path(td)/"x.zip"
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("strategy_lab\\results\\v3\\redeveloped_strategies\\test.py","# no trade")
                z.writestr("strategy_lab\\results\\one.json",'{}')
                z.writestr("strategy_lab\\run_strategy.py","# runner")
            result=inventory(archive)
            self.assertEqual(result["results_files"],2)
            self.assertEqual(result["strategy_python_under_results"],1)
            self.assertFalse(result["code_published"])
    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            archive=Path(td)/"bad.zip"
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("../secrets.txt","unsafe")
            with self.assertRaises(ValueError): inventory(archive)

if __name__=="__main__": unittest.main()
