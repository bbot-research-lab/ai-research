import io
import json
import unittest
from research_addon.verified_previous_run import verify_predecessor

class Reply(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class PreviousRunTests(unittest.TestCase):
    def test_exact_approved_success(self):
        record={"status":"completed","conclusion":"success",
                "head_branch":"feature/research-multiframe-foundation-20261014",
                "repository":{"full_name":"bbot-research-lab/ai-research"},
                "event":"workflow_dispatch",
                "path":".github/workflows/multiframe-persistence-smoke.yml@refs/heads/feature/research-multiframe-foundation-20261014"}
        def fake(req,timeout):
            self.assertEqual(timeout,15)
            return Reply(json.dumps(record).encode())
        self.assertTrue(verify_predecessor(42,"test-token",opener=fake))
        for patch in ({"conclusion":"failure"},{"status":"in_progress"},
                      {"head_branch":"main"},{"repository":{"full_name":"wrong/repo"}},
                      {"event":"schedule"},{"path":".github/workflows/continuous-research.yml@refs/heads/main"}):
            with self.subTest(patch=patch):
                bad=record|patch
                with self.assertRaises(RuntimeError):
                    verify_predecessor(42,"test-token",
                      opener=lambda *_args,**_kwargs:Reply(json.dumps(bad).encode()))
    def test_invalid_identity_rejected(self):
        with self.assertRaises(ValueError):
            verify_predecessor(0,"test")

if __name__=="__main__":
    unittest.main()
