import datetime as dt
import json
import unittest
from research_addon.dispatch_next_research import dispatch_next

class Response:
    status = 204
    def __enter__(self): return self
    def __exit__(self, *args): return False

class DispatchNextTests(unittest.TestCase):
    def test_opt_in_dispatch_correct_frame_and_counter(self):
        now = dt.datetime.now(dt.timezone.utc)
        requests = []
        def open_stub(request, timeout):
            requests.append(request)
            self.assertEqual(timeout, 15)
            return Response()
        args = dict(frame="6h", job_result="success",
                    checkpoint_verified=True, enabled=True,
                    completed_hops=1, last_checkpoint_at=now.isoformat(),
                    now=now, token="test-token", opener=open_stub)
        self.assertEqual(dispatch_next(**args), {"frame":"6h","hop":2})
        self.assertEqual(len(requests), 1)
        payload = json.loads(requests[0].data)
        self.assertEqual(payload["inputs"], {"frame":"6h", "hop":"2"})
        self.assertIn("/dispatches", requests[0].full_url)

    def test_disabled_never_calls_network(self):
        now = dt.datetime.now(dt.timezone.utc)
        def fail(*a, **k):
            self.fail("network must not be called")
        result = dispatch_next(frame="6h", job_result="failure",
                               checkpoint_verified=True, enabled=True,
                               completed_hops=1,
                               last_checkpoint_at=now.isoformat(),
                               now=now, token="test", opener=fail)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
