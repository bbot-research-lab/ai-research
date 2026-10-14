import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.staged_official_replay import (
    stage, SOURCE_FILES, EXTRA_FILES, MODULES,
)

class OfficialStageTests(unittest.TestCase):
    def fixtures(self, directory, *, omit=None, tamper=False):
        root=Path(directory)
        files=[
            ("src.zip", SOURCE_FILES),
            ("required.zip", EXTRA_FILES),
            ("modules.zip", MODULES),
        ]
        archives=[]
        for name, expected in files:
            archive=root/name
            with zipfile.ZipFile(archive,"w") as z:
                for member in sorted(expected):
                    if member == omit:
                        continue
                    data=(b"tampered" if tamper and member=="gate_lab_fast.py" else
                          ("synthetic:"+member).encode())
                    # Original user's Windows ZIP stores backslash-separated names.
                    z.writestr(member.replace("/", "\\"), data)
            archives.append(archive)
        return archives

    def test_missing_modules_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            archives=self.fixtures(td, omit="stoch.py")
            with self.assertRaisesRegex(ValueError,"stoch.py"):
                stage(*archives, Path(td)/"staged")

    def test_pinned_hash_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            archives=self.fixtures(td, tamper=True)
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                stage(*archives, Path(td)/"staged")

    def test_windows_zip_paths_and_root_layout(self):
        with tempfile.TemporaryDirectory() as td:
            archives=self.fixtures(td)
            import scripts.staged_official_replay as replay
            expected_engine=hashlib.sha256(b"synthetic:gate_lab_fast.py").hexdigest()
            expected_cache=hashlib.sha256(b"synthetic:gate_lab_exact_long_cache.parquet").hexdigest()
            with patch.object(replay,"ENGINE_SHA",expected_engine), patch.object(replay,"CACHE_SHA",expected_cache):
                root=stage(*archives,Path(td)/"staged")
            self.assertTrue((root/"strategy_lab/run_strategy.py").is_file())
            self.assertTrue((root/"assist/strategies/ema_cross.py").is_file())
            self.assertTrue((root/"gate_lab_exact_long_cache.parquet").is_file())

if __name__=="__main__": unittest.main()
