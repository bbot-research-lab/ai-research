import unittest
from unittest.mock import patch
from research_addon.inspect_completion_event import inspect

class InspectCompletionEventTests(unittest.TestCase):
    def test_unapproved_never_reads_remote(self):
        with patch("research_addon.inspect_completion_event.verify_predecessor") as predecessor:
            self.assertEqual(inspect({"action":"requested"},"token","remote","key"),
                             {"eligible":False,"frames":[]})
            predecessor.assert_not_called()
    def test_verified_frame_only_and_no_dispatch(self):
        with patch("research_addon.inspect_completion_event.eligible_completion",return_value=42),patch(
             "research_addon.inspect_completion_event.verify_predecessor"),patch(
             "research_addon.inspect_completion_event.verify_frame_job",
             side_effect=lambda run,frame,token: None if frame=="6h" else (_ for _ in ()).throw(RuntimeError("missing"))),patch(
             "research_addon.inspect_completion_event.check_remote_state",
             return_value={"verified":True,"hop":2,"records":31}) as state:
            result=inspect({},"fake","remote","key")
        self.assertEqual(result,{"eligible":True,"frames":[{"frame":"6h","hop":2,"records":31}]})
        state.assert_called_once_with("6h","remote","key")

if __name__=="__main__":
    unittest.main()
