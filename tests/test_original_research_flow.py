# 파일명: tests/test_original_research_flow.py
# 원본 연결 테스트. 합성 입력·모의 결과는 실제 전략 합격 증거가 아니다.
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd


@unittest.skipUnless(os.environ.get('BBOT_TEST_ORIGINAL_ROOT'), 'Private original source required')
class OriginalFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(os.environ['BBOT_TEST_ORIGINAL_ROOT']).resolve()
        os.environ['BBOT_LOCAL_ROOT']=str(root)
        os.environ['BBOT_RESEARCH_TIMEFRAME']='1H'
        sys.path.insert(0,str(root/'strategy_lab'))
        sys.path.insert(0,str(root))
        cls.research=importlib.import_module('v3_strategy_research')
        cls.factory=importlib.import_module('v3_hypothesis_factory')
        cls.controller=importlib.import_module('research_controller')
        cls.knowledge=importlib.import_module('v3_research_knowledge')

    def test_frame_scope_and_signal_prefix_causality(self):
        self.assertEqual(self.research.TF_ORDER,['1H'])
        self.assertEqual(self.factory.TF_ORDER,['1H'])
        frame=pd.DataFrame({'close':100+np.sin(np.arange(400)/8)*7+np.arange(400)*.05})
        for mode in ('TREND_Z','CHANNEL_Z','MEAN_REVERSION_Z','EMA_CROSS_Z','MOMENTUM_Z'):
            recipe={'mode':mode,'window':18,'threshold':.4}
            short=self.factory.generate_signals_recipe(frame.iloc[:250],recipe)
            full=self.factory.generate_signals_recipe(frame,recipe)
            np.testing.assert_array_equal(short,full[:250])

    def test_completed_failure_still_blocks_after_detailed_ledger_trim(self):
        k=self.knowledge
        with tempfile.TemporaryDirectory() as tmp, patch.multiple(k,TRIALS=Path(tmp)/'trials.json',KNOWLEDGE=Path(tmp)/'knowledge.json',RUNTIME_SUMMARY=Path(tmp)/'runtime.json'):
            trial=k.reserve_trial('fixture','candidate','1H')
            k.complete_trial(trial,'failure.json','FAIL')
            _,ledger=k.ensure()
            ledger['entries']=[]
            k.atomic(k.TRIALS,ledger)
            with self.assertRaisesRegex(RuntimeError,'DUPLICATE_COMPLETED'):
                k.reserve_trial('fixture','candidate','1H')
            k.record_result('fixture',{'strategy':'candidate','timeframe':'1H','trial':trial,'status':'FAIL','reason':'fixture'},failed=True)
            knowledge,_=k.ensure()
            self.assertEqual(len(knowledge['failed_index']),1)

    def test_infrastructure_failure_keeps_history_and_requires_verified_retry(self):
        k=self.knowledge
        with tempfile.TemporaryDirectory() as tmp, patch.multiple(k,TRIALS=Path(tmp)/'trials.json',KNOWLEDGE=Path(tmp)/'knowledge.json',RUNTIME_SUMMARY=Path(tmp)/'runtime.json'):
            trial=k.reserve_trial('fixture','interrupted','1H')
            k.complete_trial(trial,'RUN_STRATEGY_FAIL','FAIL')
            _,ledger=k.ensure()
            self.assertEqual(ledger['entries'][0]['event'],'INTERRUPTED')
            self.assertEqual(len(ledger['infrastructure_index']),1)
            self.assertEqual(ledger['completed_index'],{})
            with patch.dict(os.environ,{'BBOT_RESEARCH_INPUTS_VERIFIED':'0'}):
                with self.assertRaisesRegex(RuntimeError,'REQUIRES_VERIFIED_INPUTS'):
                    k.reserve_trial('fixture','interrupted','1H')
            with patch.dict(os.environ,{'BBOT_RESEARCH_INPUTS_VERIFIED':'1'}):
                self.assertEqual(k.reserve_trial('fixture','interrupted','1H'),trial+1)

    def test_repair_retries_only_unevaluated_pair_in_own_frame(self):
        sr=self.research
        rows=[{'eligible':True,'timeframe':tf,'canonical_identity_key':tf,'pipeline_stage':'INDIVIDUAL_TRAILING_RESEARCH_INCOMPLETE'} for tf in ('1H','6H')]
        rows.append({'eligible':True,'timeframe':'1H','canonical_identity_key':'sealed','pipeline_stage':'SEALED_FINAL_BLIND_PENDING','sealed_final_blind':{'cohort_id':'fixture'}})
        item=lambda:{'coarse_results':{'error':{'status':'RUNTIME_FAIL','trial':1},'evaluated':{'status':'MEASURED','pass':False}},'fine_candidates':[]}
        data={sr.HISTORICAL_STAGE2:{'entries':rows},sr.TRAILING_STAGE3:{'entries':{key:item() for key in ('1H','6H','sealed')}},sr.REENTRY_STAGE4:{'entries':{}}}
        with patch.dict(os.environ,{'BBOT_RESEARCH_INPUTS_VERIFIED':'1'}), patch.object(Path,'is_file',return_value=True), patch.object(sr,'load',side_effect=lambda path,default=None:data.get(path,default)), patch.object(sr,'hard_pass_dates',return_value=('start','end')), patch.object(sr.knowledge,'ensure',return_value=({'records':{}},{})), patch.object(sr,'atomic'):
            sr.sync_new_pipeline_entries()
        entries=data[sr.TRAILING_STAGE3]['entries']
        self.assertNotIn('error',entries['1H']['coarse_results'])
        self.assertIn('evaluated',entries['1H']['coarse_results'])
        self.assertEqual(len(entries['1H']['infrastructure_attempts']),1)
        self.assertIn('error',entries['6H']['coarse_results'])
        self.assertIn('error',entries['sealed']['coarse_results'])
        self.assertEqual(rows[0]['pipeline_stage'],'INDIVIDUAL_TRAILING_OPTIMIZATION_PENDING')

    def test_trailing_selects_own_frame_without_mutating_other_frame(self):
        sr=self.research
        rows=[{'eligible':True,'timeframe':tf,'pipeline_stage':'INDIVIDUAL_TRAILING_OPTIMIZATION_PENDING'} for tf in ['6H','1H']]
        with patch.object(sr,'load',side_effect=lambda path,default=None:{'entries':rows} if path==sr.HISTORICAL_STAGE2 else {}), patch.object(sr,'_ensure_stage3_entry',return_value={'coarse_candidates':[{'start_pct':3,'callback_pct':1.5}]}), patch.object(sr,'_run_trailing_pair',side_effect=lambda state,target,*args:target['timeframe']):
            self.assertEqual(sr.run_individual_trailing_one(),'1H')
        self.assertEqual(rows[0]['pipeline_stage'],'INDIVIDUAL_TRAILING_OPTIMIZATION_PENDING')

    def test_original_full_validation_moves_only_qualified_frame_to_blind(self):
        sr=self.research
        rows=[{'eligible':True,'timeframe':tf,'pipeline_stage':'FULL_VALIDATION_PENDING','strategy_id':'FIXTURE','exact_strategy_version':tf} for tf in ['6H','1H']]
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'result.json';report.write_text('{}')
            with patch.object(sr,'load',side_effect=lambda path,default=None:{'entries':rows} if path==sr.HISTORICAL_STAGE2 else {'entries':{}} if path==sr.FULL_VALIDATION_STAGE5 else {'fixture':True}), patch.object(sr,'evaluate_full_validation_gate',return_value={'pass':True,'decision':'PASS','pass_mode':'fixture'}), patch.object(sr,'_save_historical_stage2'), patch.object(sr,'atomic'), patch.object(sr.knowledge,'record_result'):
                result=sr.run_full_validation_one()
            self.assertEqual(result['timeframe'],'1H')
            self.assertEqual(rows[1]['pipeline_stage'],'SEALED_FINAL_BLIND_PENDING')
            self.assertEqual(rows[0]['pipeline_stage'],'FULL_VALIDATION_PENDING')

    def test_controller_gives_pending_validation_to_original_dispatch(self):
        c=self.controller
        work={'full_validation_pending':1,'historical_backlog_mode':False}
        availability={'NEW_PURE_AND_HARD_PASS':True,'FULL_VALIDATION':True}
        with patch.object(c.strategy_research,'sync_new_pipeline_entries',return_value={}), patch.object(c.strategy_research,'pipeline_work_status',return_value=work), patch.object(c.strategy_research,'_pipeline_local_shadow_choice',return_value=None), patch.object(c,'_managed_availability',return_value=availability), patch.object(c.task_queue,'preview_auto_research_bucket',side_effect=lambda flags,*args:{'bucket':next(k for k,v in flags.items() if v)}), patch.object(c,'_dispatch_managed_bucket',return_value={'status':'fixture'}) as dispatch, patch.object(c.task_queue,'record_auto_research_bucket'):
            c.managed_research_once(True)
            self.assertEqual(dispatch.call_args.args[0],'FULL_VALIDATION')
        self.assertEqual(c.managed_research_once(False)['action'],'GOVERNANCE_BLOCK')

    def test_genetic_and_optuna_create_candidates_using_training_rows_only(self):
        h=self.factory
        import run_strategy as official
        old_rows=h.research_recipes()
        times=np.arange(800)*3600+1577836800
        candles=pd.DataFrame({'open_time':times,'open':100.,'high':110.,'low':90.,'close':100+np.sin(np.arange(800)/9)*5,'volume':10.})
        cache=pd.DataFrame({'symbol':['FIXTUREUSDT']*800,'ts':times,'close':candles.close})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'strategy_lab').mkdir();(root/'data/candles/FIXTUREUSDT').mkdir(parents=True)
            (root/'strategy_lab/lab_config.json').write_text(json.dumps({'data_file':'fixture','fee_rate':.0004}))
            candles.to_parquet(root/'data/candles/FIXTUREUSDT/1h.parquet',index=False)
            dest=root/'search.json'
            done={(row['name'].upper(),'1H') for row in old_rows}
            observed=[]
            actual_simulate=official.simulate
            def simulate(frame,*args,**kwargs):
                observed.extend(frame.ts.tolist())
                return actual_simulate(frame,*args,**kwargs)
            with patch.multiple(h,ROOT=root,LAB=root/'strategy_lab',DEVELOPMENT=dest), patch.object(h,'completed_pairs',return_value=done), patch.dict(os.environ,{'BBOT_DEVELOP_BASIC_STRATEGIES':'1'}), patch.object(official,'load_cache',return_value=cache), patch.object(official,'make_hard_pass_dataset_windows',return_value={official.HARD_PASS_DATASET:{'symbols':['FIXTUREUSDT']}}), patch.object(official,'simulate',side_effect=simulate):
                selected=h.choose_next()
            history=json.loads(dest.read_text())
            self.assertIsNotNone(selected)
            self.assertGreater(history['searches'][0]['genetic_proposals'],0)
            self.assertGreater(history['searches'][0]['optuna_proposals'],0)
            self.assertTrue(observed)
            self.assertLess(max(observed),history['searches'][0]['training_end_exclusive'])
            self.assertFalse(history['searches'][0]['approval'])

    def test_parallel_frames_never_share_blind_time_windows(self):
        sr=self.research
        seen=set()
        for frame in ['30M','1H','6H','12H','1D','1W']:
            with patch.object(sr,'RESEARCH_FRAME',frame):
                windows=sr._blind_window_candidates({'blind_window_days':30})
            identities={(a.isoformat(),b.isoformat()) for a,b in windows}
            self.assertFalse(seen & identities)
            seen.update(identities)
        with patch.object(sr,'RESEARCH_FRAME',''):
            all_windows=sr._blind_window_candidates({'blind_window_days':30})
        self.assertEqual(len(seen),len(all_windows))

    def test_blind_reads_canonical_candles_and_epoch_seconds(self):
        from datetime import datetime,timedelta,timezone
        sr=self.research
        start=datetime(2020,1,1,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'data/candles/FIXTUREUSDT/1h.parquet';target.parent.mkdir(parents=True)
            frame=pd.DataFrame({'open_time':int(start.timestamp())+np.arange(48)*3600,'open':100.,'high':102.,'low':99.,'close':101.,'volume':10.})
            frame.to_parquet(target,index=False)
            with patch.object(sr,'ROOT',root):
                profile=sr._blind_candle_profile_window('FIXTUREUSDT','1H',start,start+timedelta(days=2))
                raw=sr._blind_raw_ohlcv('FIXTUREUSDT','1H')
            self.assertEqual(profile['coverage_ratio'],1.0)
            self.assertEqual(profile['gap_ratio'],0.0)
            self.assertEqual(len(raw),48)

    def test_shadow_report_cannot_replace_original_approval(self):
        c=self.controller
        candidate={'strategy':'FIXTURE','exact_strategy_version':'fixture'}
        with patch.object(c.strategy_research,'sync_new_pipeline_entries',return_value={}), patch.object(c.strategy_research,'pipeline_work_status',return_value={}), patch.object(c.strategy_research,'_pipeline_local_shadow_choice',return_value=candidate), patch.object(c,'candidate_already_tracked',return_value=True), patch.object(c.shadow_engine,'process_pending_shadows',return_value={'status':'PASS'}), patch.object(c.deploy,'state',return_value={'frames':{'1H':{'strategy':'FIXTURE','strategy_version':'fixture','strategy_instance_id':'fixture'}}}), patch.object(c.deploy,'minimal_shadow_pass',return_value=False), patch.object(c.strategy_research,'atomic') as atomic, patch.object(c,'_managed_availability',return_value={}), patch.object(c.task_queue,'preview_auto_research_bucket',return_value=None), patch.object(c.task_queue,'select_next',return_value=None), patch.object(c.task_queue,'auto_research_manager_status',return_value={}):
            c.managed_research_once(True)
            atomic.assert_not_called()


if __name__=='__main__':
    unittest.main()
