import unittest
from unittest.mock import patch
from research_addon.completion_listener import handle_event

class CompletionListenerTests(unittest.TestCase):
    def setUp(self):
        self.event={"action":"completed","workflow_run":{
          "id":321,"status":"completed","conclusion":"success",
          "head_branch":"feature/research-multiframe-foundation-20261014",
          "path":".github/workflows/multiframe-persistence-smoke.yml",
          "repository":{"full_name":"bbot-research-lab/ai-research"}}}
    def test_default_off_never_checks_network_or_state(self):
        self.assertEqual(handle_event(self.event,enabled=False,token="none",
                         state_checker=lambda f:self.fail("called")),[])
    def test_only_valid_frame_jobs_dispatch(self):
        called=[]
        def frame_check(run_id,frame,token):
            if frame!="6h": raise RuntimeError("not present")
        def dispatch(**kwargs):
            called.append(kwargs)
            return {"frame":kwargs["frame"],"hop":kwargs["completed_hops"]+1}
        with patch("research_addon.completion_listener.verify_predecessor",return_value=True),patch(
             "research_addon.completion_listener.verify_frame_job",side_effect=frame_check):
            result=handle_event(self.event,enabled=True,token="fake",
                state_checker=lambda f:{"verified":True,"hop":1,
                  "timestamp":"2026-10-14T10:00:00+00:00"},
                dispatcher=dispatch)
        self.assertEqual(result,[{"frame":"6h","hop":2}])
        self.assertEqual(len(called),1)
    def test_unverified_remote_state_blocks_dispatch(self):
        with patch("research_addon.completion_listener.verify_predecessor",return_value=True),patch(
             "research_addon.completion_listener.verify_frame_job",return_value=True):
            self.assertEqual(handle_event(self.event,enabled=True,token="fake",
                state_checker=lambda f:{"verified":False},
                dispatcher=lambda **kwargs:self.fail("unexpected dispatch")),[])
if __name__=="__main__":
    unittest.main()
