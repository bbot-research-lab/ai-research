import unittest
from research_addon.formal_simulation_objective import make_trade_objective

class OfficialAdapterTests(unittest.TestCase):
    def rows(self):
        return [{"ts":i+1,"close":x} for i,x in enumerate((100,102,105,104,100))]
    def test_official_function_called_without_modifying_inputs(self):
        calls=[]
        def official(frame, signal, fee):
            calls.append((list(signal),fee))
            frame.loc[0,"close"] = -999
            return [{"net_return":-.020607843137254944}]
        source=self.rows()
        fn=make_trade_objective(official,lambda df,p: [0,1,1,0,0],fee_rate=.0005)
        self.assertAlmostEqual(fn(source,{"x":1}),-.020607843137254944)
        self.assertEqual(source[0]["close"],100)
        self.assertEqual(calls, [([0,1,1,0,0],.0005)])
    def test_invalid_training_timestamps_fail(self):
        obj=make_trade_objective(lambda *x:[],lambda df,p:[],fee_rate=.0005)
        rows=self.rows()
        rows[1]["ts"]=1
        with self.assertRaises(ValueError):obj(rows,{"x":1})
    def test_bad_fee_rejected(self):
        with self.assertRaises(ValueError):
            make_trade_objective(lambda *x:[],lambda *_:[],fee_rate=float("nan"))
    def test_nonfinite_result_rejected(self):
        obj=make_trade_objective(lambda *_:[{"net_return":float("nan")}],lambda *_:[],fee_rate=.0005)
        with self.assertRaises(ValueError):obj(self.rows(),{"x":1})

if __name__=="__main__": unittest.main()
