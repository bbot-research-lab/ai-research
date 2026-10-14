import tempfile
import unittest
from pathlib import Path
from research_addon.continuation_receipt import write_hop,read_hop
from research_addon.prepare_hosted_hop import prepare_hop

class PrepareHostedHopTests(unittest.TestCase):
    def test_exact_retry_and_single_forward_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            frame=Path(tmp)/"6h"
            write_hop(frame,"6h",0)
            self.assertFalse(prepare_hop("6h",tmp,0)["advanced"])
            self.assertTrue(prepare_hop("6h",tmp,1)["advanced"])
            self.assertFalse(prepare_hop("6h",tmp,1)["advanced"])
            self.assertEqual(read_hop(frame,"6h",require_existing=True),1)
            for bad in (0,3,49,-1):
                with self.subTest(bad=bad):
                    with self.assertRaises(ValueError):
                        prepare_hop("6h",tmp,bad)
            self.assertEqual(read_hop(frame,"6h",require_existing=True),1)
    def test_no_checkpoint_cannot_initialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                prepare_hop("6h",tmp,0)

if __name__=="__main__":
    unittest.main()
