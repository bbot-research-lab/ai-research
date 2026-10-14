import unittest
from datetime import datetime, timedelta, timezone
from research_addon.restart_gate import can_continue, next_hop

class RestartGateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
        self.good = dict(frame="6h", job_result="success",
                         checkpoint_verified=True, enabled=True,
                         completed_hops=2,
                         last_checkpoint_at=(self.now-timedelta(minutes=1)).isoformat(),
                         now=self.now)

    def test_authorized_chain_advances_once(self):
        self.assertEqual(next_hop(**self.good), {"frame": "6h", "hop": 3})

    def test_refuse_failed_unverified_disabled_expired_or_exhausted(self):
        changes = [
            {"job_result": "failure"}, {"checkpoint_verified": False},
            {"enabled": False}, {"completed_hops": 48},
            {"last_checkpoint_at": (self.now-timedelta(hours=7)).isoformat()},
            {"last_checkpoint_at": (self.now+timedelta(hours=1)).isoformat()},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assertIsNone(next_hop(**(self.good | change)))

    def test_invalid_frame_and_hop_fail_closed(self):
        with self.assertRaises(ValueError):
            can_continue(**(self.good | {"frame": "5m"}))
        with self.assertRaises(ValueError):
            can_continue(**(self.good | {"completed_hops": True}))

if __name__ == "__main__":
    unittest.main()
