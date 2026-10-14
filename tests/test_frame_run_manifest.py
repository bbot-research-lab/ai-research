import datetime as dt
import unittest
from research_addon.frame_run_manifest import make_manifest, eligible_for_resume

class FrameRunManifestTests(unittest.TestCase):
    def test_resume_and_reject_wrong_revision(self):
        now = dt.datetime.now(dt.timezone.utc)
        start = (now - dt.timedelta(minutes=10)).isoformat()
        end = now.isoformat()
        commit = "a" * 40
        m = make_manifest("6h", head_sha=commit, checkpoint_sha="b" * 64,
                          run_id=123, started_at=start, ended_at=end,
                          status="SUCCESS", completed=30)
        self.assertTrue(eligible_for_resume(m, current_head_sha=commit))
        self.assertFalse(eligible_for_resume(m, current_head_sha="c" * 40))
    def test_reject_invalid_run(self):
        with self.assertRaises(ValueError):
            make_manifest("6h", head_sha="wrong", checkpoint_sha="b" * 64,
                          run_id=1, started_at="2026-10-14T00:00:00+00:00",
                          ended_at="2026-10-14T01:00:00+00:00",
                          status="SUCCESS", completed=1)

if __name__ == "__main__":
    unittest.main()
