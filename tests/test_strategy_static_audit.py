import ast
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.strategy_static_audit import inspect_ast,audit

class AuditTests(unittest.TestCase):
    def test_embedded_exec_is_detected(self):
        payload = "import subprocess\nsubprocess.run(['x'])"
        s = "_SRC = " + repr(payload) + "\nexec(compile(_SRC, '<x>', 'exec'))"
        flags=inspect_ast(ast.parse(s))
        self.assertIn("DYNAMIC_EXECUTION:exec",flags)
        self.assertTrue(any("EMBEDDED_NETWORK_OR_PROCESS_IMPORT:subprocess" == x for x in flags))
    def test_short_embedded_import_is_not_skipped(self):
        source = "_SRC = 'import subprocess'\nexec(_SRC)"
        flags = inspect_ast(ast.parse(source))
        self.assertIn("EMBEDDED_NETWORK_OR_PROCESS_IMPORT:subprocess", flags)

    def test_safe_source_does_not_get_auto_published(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"test.zip"
            with zipfile.ZipFile(target,"w") as z:
                z.writestr("strategy_lab/strategies/test.py","def signal(df): return 0")
            result=audit(target)
            self.assertEqual(result["files"],1)
            self.assertEqual(result["statuses"].get("STATIC_LOW_RISK"),1)
            self.assertIn("No source",result["notice"])
    def test_dynamic_exec_requires_review(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"test.zip"
            with zipfile.ZipFile(target,"w") as z:
                z.writestr("strategy_lab/results/v3/redeveloped_strategies/a.py","exec('a=1')")
            result=audit(target)
            self.assertEqual(result["statuses"].get("REVIEW_REQUIRED"),1)

if __name__=="__main__":unittest.main()
