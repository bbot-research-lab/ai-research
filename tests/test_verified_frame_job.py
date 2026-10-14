import io
import json
import unittest
from research_addon.verified_frame_job import verify_frame_job

class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

def job(frame="6h",state="success"):
    return {"name":f"synthetic-frame ({frame})","status":"completed",
            "conclusion":state,"steps":[
                {"name":"Restore authenticated frame before training","conclusion":"success"},
                {"name":"Commit encrypted state to isolated branch","conclusion":"success"}]}

class VerifiedFrameJobTests(unittest.TestCase):
    def test_frame_success(self):
        payload={"total_count":2,"jobs":[job(),job("1h")]}
        def opener(req,timeout):
            self.assertEqual(timeout,15)
            return Response(json.dumps(payload).encode())
        self.assertTrue(verify_frame_job(11,"6h","fake",opener=opener))
    def test_other_frame_or_failed_checkpoint_rejected(self):
        for record in [job("1h"),job("6h","failure"),
                       {**job(),"steps":[]},
                       {**job(),"steps":[{"name":"Restore authenticated frame before training","conclusion":"success"}]}]:
            with self.subTest(record=record):
                with self.assertRaises(RuntimeError):
                    verify_frame_job(11,"6h","fake",opener=lambda *_args,**_kw:Response(
                        json.dumps({"total_count":1,"jobs":[record]}).encode()))
    def test_pagination_and_invalid_frame_refused(self):
        with self.assertRaises(RuntimeError):
            verify_frame_job(11,"6h","fake",opener=lambda *_a,**_k:Response(
                json.dumps({"total_count":101,"jobs":[job()]}).encode()))
        with self.assertRaises(ValueError):
            verify_frame_job(11,"5m","fake")

if __name__=="__main__":
    unittest.main()
