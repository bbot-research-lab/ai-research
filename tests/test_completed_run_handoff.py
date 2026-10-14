import unittest
from research_addon.completed_run_handoff import eligible_completion,next_frame_hop

class CompletedRunHandoffTests(unittest.TestCase):
    def setUp(self):
        self.event={"action":"completed","workflow_run":{
            "id":77,"status":"completed","conclusion":"success",
            "head_branch":"feature/research-multiframe-foundation-20261014",
            "path":".github/workflows/multiframe-persistence-smoke.yml@refs/heads/feature/research-multiframe-foundation-20261014",
            "repository":{"full_name":"bbot-research-lab/ai-research"}}}
    def test_explicit_opt_in_only(self):
        self.assertIsNone(eligible_completion(self.event))
        self.assertEqual(eligible_completion(self.event,enabled=True),77)
    def test_fail_closed_event_validation(self):
        for patch in [{"conclusion":"failure"},{"status":"in_progress"},
                      {"head_branch":"main"},{"id":"77"},
                      {"repository":{"full_name":"other/repo"}},
                      {"path":".github/workflows/research-ci.yml"}]:
            with self.subTest(patch=patch):
                event={"action":"completed","workflow_run":self.event["workflow_run"]|patch}
                self.assertIsNone(eligible_completion(event,enabled=True))
        self.assertIsNone(eligible_completion(self.event|{"action":"requested"},enabled=True))
    def test_hops_are_bounded(self):
        self.assertEqual(next_frame_hop("6h",0),{"frame":"6h","hop":1})
        self.assertIsNone(next_frame_hop("6h",48))
        self.assertIsNone(next_frame_hop("6h",-1))
        self.assertIsNone(next_frame_hop("5m",0))

if __name__=="__main__":
    unittest.main()
