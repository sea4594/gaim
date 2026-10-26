"""End-to-end experimental reducers; no production code is imported."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from experiments.redesign_phase3 import engine, operations, survey

FIX=json.loads((Path(__file__).resolve().parents[1]/'docs/redesign/phase02-sanity-fixtures.json').read_text())

class StormEngineTests(unittest.TestCase):
    def test_phase2_full_win_and_no_build_loss(self):
        f=FIX['engine']
        good=engine.play(f['rounds'],{int(k):{'build':v} for k,v in f['builds'].items()})
        self.assertEqual((good['finished'],good['hull'],good['power'],good['levels']),
                         ('WIN',6,8,[2,2,0]))
        self.assertEqual(engine.play(f['rounds'],{})['finished'],'LOSS_SYSTEMS')
        self.assertEqual(good['history'][2]['bonus'],0) # Level-1 Dynamo is Left-only.
    def test_atomic_invalid_plan_and_resource_edges(self):
        s=engine.new_game(FIX['engine']['rounds']); before=deepcopy(s)
        with self.assertRaises(ValueError):
            engine.step(s,{'build':0,'edits':[{'kind':'DAMP','token':'r1t0'}]*2})
        self.assertEqual(s,before)
        with self.assertRaises(ValueError):
            engine.step(s,{'build':0,'edits':[{'kind':'FLIP','token':'r1t0'}]})
        with self.assertRaises(ValueError):
            engine.step(s,{'free':{'token':'r1t0','delta':1}})
        s=engine.step(s,{'build':0});self.assertEqual(s['power'],0)
        with self.assertRaises(ValueError): engine.step(s,{'build':0})
    def test_lifetime_hold_and_deadline(self):
        waves=[[dict(lane=0,sign=1,strength=1)]]+[[] for _ in range(7)]
        s=engine.step(engine.new_game(waves),{'edits':[dict(kind='HOLD',token='r1t0')]})
        self.assertEqual(s['board'][0]['depth'],2)
        with self.assertRaises(ValueError):
            engine.step(s,{'edits':[dict(kind='HOLD',token='r1t0')]})
        for _ in range(7):
            if s['finished']:break
            s=engine.step(s)
        self.assertNotEqual(s['finished'],'WIN')
    def test_breach_offline_next_round_and_victory(self):
        # Round 7 mismatch in Dynamo lane disables it for Round 8 victory.
        waves=deepcopy(FIX['engine']['rounds'])
        waves[5]=[dict(lane=0,sign=1,strength=2)]
        plan={int(k):{'build':v} for k,v in FIX['engine']['builds'].items()}
        s=engine.play(waves,plan)
        self.assertEqual(s['history'][7]['offline'][0],True)
        self.assertEqual(s['finished'],'LOSS_SYSTEMS')
    def test_token_strength_matching_and_aegis(self):
        waves=[[dict(lane=0,sign=1,strength=3),dict(lane=0,sign=-1,strength=1)]]+[[] for _ in range(7)]
        s=engine.new_game(waves);s=engine.step(s)
        s=engine.step(s)
        self.assertEqual((s['history'][-1]['matched'],s['history'][-1]['raw'],s['hull']),([1,0,0],[2,0,0],4))
        self.assertTrue(s['outages'][0])
    def test_multiple_upgrades_from_same_scenario(self):
        found=None
        for i in range(32):
            a=survey.run_engine(i+5000,'dynamo_aegis')
            b=survey.run_engine(i+5000,'aegis_switchyard')
            if a['finished']==b['finished']=='WIN':found=(a,b);break
        self.assertIsNotNone(found)
        self.assertNotEqual(found[0]['levels'],found[1]['levels'])

class StormOperationsTests(unittest.TestCase):
    def test_phase2_win_loss_and_hands(self):
        f=FIX['operations']; hands=[['DAMP','LEFT','RIGHT'],['HOLD','LEFT','RIGHT']]
        plans={3:[[dict(kind='DAMP',token='r2t2')],[]]}
        win=operations.play(f['rounds'],2,f['missions'],plans,1,hands)
        loss=operations.play(f['rounds'],2,f['missions'],{},1,hands)
        self.assertEqual((win['finished'],win['hull']),('WIN',1))
        self.assertIn('deep_capture',operations.completed(win))
        self.assertIn('precision_route',operations.completed(win))
        self.assertEqual(loss['finished'],'LOSS_HULL')
        self.assertEqual(sum(win['played_by']),1)
    def test_validation_and_atomicity(self):
        f=FIX['operations']; hands=[['DAMP','LEFT','RIGHT'],['HOLD','LEFT','RIGHT']]
        s=operations.new_game(f['rounds'],2,f['missions'],starting_hands=hands)
        original=deepcopy(s)
        with self.assertRaises(ValueError): operations.step(s,[[dict(kind='FLIP',token='r1t0')],[]])
        with self.assertRaises(ValueError): operations.step(s,[[dict(kind='LEFT',token='r1t2')],[]])
        with self.assertRaises(ValueError): operations.step(s,[[dict(kind='DAMP',token='missing')],[]])
        self.assertEqual(s,original)
    def test_two_orders_on_token_and_damp_fizzle(self):
        f=FIX['operations'];hands=[['DAMP','LEFT','RIGHT'],['DAMP','LEFT','HOLD']]
        s=operations.new_game(f['rounds'],2,f['missions'],starting_hands=hands)
        s=operations.step(s,[[dict(kind='DAMP',token='r1t2')],[dict(kind='DAMP',token='r1t2')]])
        self.assertEqual(s['history'][0]['fizzles'],1)
        self.assertEqual(s['played_by'],[1,1])
        self.assertFalse(any(t['id']=='r1t2' for t in s['board']))
    def test_initiative_changes_by_round(self):
        waves=survey.operations_waves(51,3);s=operations.new_game(waves,3,['deep_capture','precision_route','double_pulse'])
        s=operations.step(s)
        s=operations.step(s)
        self.assertEqual(s['history'][0]['seat_order'],[0,1,2])
        self.assertEqual(s['history'][1]['seat_order'],[1,2,0])
    def test_mission_three_stations_and_double_pulse(self):
        waves=[[dict(lane=0,sign=1,strength=1),dict(lane=0,sign=-1,strength=1),
                dict(lane=1,sign=1,strength=1)] for _ in range(6)]+[[],[]]
        s=operations.new_game(waves,2,['double_pulse','three_stations','clean_passage'])
        for _ in range(8):
            if s['finished']:break
            s=operations.step(s)
        self.assertNotIn('three_stations',operations.completed(s))
    def test_owned_two_shift_synergy_and_missing_hand(self):
        waves=[[dict(lane=0,sign=1,strength=1),dict(lane=2,sign=-1,strength=1),
                dict(lane=1,sign=1,strength=1)]]+[
                [dict(lane=1,sign=1,strength=1),dict(lane=1,sign=-1,strength=1),dict(lane=1,sign=1,strength=1)]
                for _ in range(5)]+[[],[]]
        h=[['RIGHT','DAMP','HOLD'],['LEFT','DAMP','FLIP']]
        s=operations.step(operations.new_game(waves,2,['deep_capture','precision_route','three_stations'],starting_hands=h))
        s['hull']=2 # Tactical survival fixture, not a natural full-game start.
        both=operations.step(s,[[dict(kind='RIGHT',token='r1t0')],[dict(kind='LEFT',token='r1t1')]])
        alone=operations.step(s,[[dict(kind='RIGHT',token='r1t0')],[]])
        self.assertTrue(both['hull']>0)
        self.assertEqual(alone['finished'],'LOSS_HULL')
        self.assertEqual(s['hull'],2)
    def test_all_player_counts_complete_witnesses(self):
        for players in range(1,5):
            found_winner=False; found_loser=False
            for seed in range(20):
                s=survey.run_operations(seed+7000,players,'active')
                t=survey.run_operations(seed+7000,players,'pass')
                found_winner |= s['finished']=='WIN'
                found_loser |= t['finished']!='WIN'
            self.assertTrue(found_winner, f'No winning witness for {players}p')
            self.assertTrue(found_loser, f'No losing witness for {players}p')
    def test_replay_determinism_and_wave_counts(self):
        for players in range(1,5):
            waves=survey.operations_waves(500,players)
            a=operations.new_game(waves,players,['deep_capture','precision_route','double_pulse'],123)
            b=operations.new_game(waves,players,['deep_capture','precision_route','double_pulse'],123)
            self.assertEqual(a,b)
            a=operations.step(a);b=operations.step(b)
            self.assertEqual(a,b)
            self.assertEqual(len(waves[0]),players+1)

class PublishedEvidenceTests(unittest.TestCase):
    def test_recorded_engine_strategies_replay_exactly(self):
        file=Path(__file__).resolve().parents[1]/'docs/redesign/phase03-full-game-witnesses.json'
        w=json.loads(file.read_text())
        contested=w['engine_contested_seed']
        self.assertTrue(5000 <= contested['seed'] < 5090)
        for mode,record in contested['results'].items():
            plans={h['round']:dict(edits=h['edits'],build=h['build'],free=h['free'])
                   for h in record['history']}
            result=engine.play(contested['waves'],plans)
            self.assertEqual(result['finished'],record['outcome'])
            self.assertEqual(result['levels'],record['levels'])
            self.assertEqual(result['hull'],record['hull'])
    def test_recorded_player_count_witnesses_replay_exactly(self):
        file=Path(__file__).resolve().parents[1]/'docs/redesign/phase03-full-game-witnesses.json'
        witnesses=json.loads(file.read_text())['operations_by_player_count']
        self.assertEqual(set(witnesses),{'1','2','3','4'})
        for count,item in witnesses.items():
            n=int(count)
            plans={h['round']:h['order'] for h in item['active']['history']}
            result=operations.play(item['waves'],n,['deep_capture','precision_route','double_pulse'],
                                   plans,int(item['seed']))
            self.assertEqual(result['finished'],'WIN')
            self.assertEqual(result['history'],item['active']['history'])
            self.assertEqual(result['played_by'],item['active']['played_by'])
            self.assertEqual(survey.run_operations(item['seed'],n,'pass')['finished'],
                             item['passive']['outcome'])

if __name__=='__main__': unittest.main()
