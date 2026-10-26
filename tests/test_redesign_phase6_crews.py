"""Complete-phase crew reducers: accounting, causality, replay and analysis."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from experiments.redesign_phase3 import engine
from experiments.redesign_phase6.crew import (
    STATIONS,FIXED,staff_counts,work_units,fixed_assignment,
    deterministic_assignment,crew_step,staffed_step)
from experiments.redesign_phase6.survey import (
    play,policy,pick,roster_options,survey,replay,STRATEGIES)
from experiments.redesign_phase6.make_witnesses import build

DOCS=Path(__file__).resolve().parents[1]/'docs/redesign'


def crisis():
    s=engine.new_game([[] for _ in range(8)])
    s.update(round=7,hull=1,power=2,coolant=1,
             levels=[2,1,0],board=[dict(id='threat',lane=2,sign=1,strength=2,
                                      depth=1,held=False)])
    return s


class Phase6CrewTests(unittest.TestCase):
    def test_four_work_units_regardless_player_count(self):
        for players in range(1,5):
            for round_number in range(1,9):
                caps=work_units(players,round_number)
                self.assertEqual(sum(caps),4)
                self.assertEqual(len(caps),players)
                self.assertEqual(staff_counts(fixed_assignment(players,round_number),players,round_number),FIXED)
                self.assertEqual(staff_counts(deterministic_assignment((0,0,2,2),players,round_number),players,round_number),(0,0,2,2))
        self.assertEqual(len(roster_options()),19)

    def test_illegal_staffing_does_not_mutate_state(self):
        s=crisis();original=deepcopy(s)
        for staffing,plan in [((3,0,1,0),{}),((1,1,1,0),{}),
                               ((0,0,2,2),{'nav':[dict(kind='SHIFT',token='threat',delta=1)]}),
                               (FIXED,{'control':[dict(kind='FLIP',token='threat')]}),
                               (FIXED,{'engineer':{'build':1},'dispatch':{'kind':'cover','lane':2}}),
                               (FIXED,{'dispatch':{'kind':'cover','lane':9}})]:
            with self.assertRaises(ValueError):crew_step(s,staffing,plan)
            self.assertEqual(s,original)
        with self.assertRaises(ValueError):staff_counts((("nav",),),4,1)
        with self.assertRaises(ValueError):staff_counts((('nav',),('nav',),('nav',),('engineer',)),4,1)

    def test_two_engineers_and_dispatch_create_a_mutual_dependency(self):
        s=crisis();plan={'engineer':{'build':1},'dispatch':{'kind':'cover','lane':2}}
        combo=crew_step(s,(1,0,2,1),plan)
        self.assertEqual(combo['hull'],1)
        self.assertEqual(combo['pending'],1)
        final=crew_step(combo,FIXED,{})
        self.assertEqual(final['finished'],'WIN')
        # No engineer support: cannot afford building and covering this turn.
        with self.assertRaisesRegex(ValueError,'Not enough'):
            crew_step(s,FIXED,plan)
        unprotected=crew_step(s,(1,0,2,1),{'engineer':{'build':1}})
        self.assertEqual(unprotected['finished'],'LOSS_HULL')
        no_build=crew_step(s,(1,0,2,1),{'dispatch':{'kind':'cover','lane':2}})
        self.assertEqual(crew_step(no_build,FIXED,{})['finished'],'LOSS_SYSTEMS')
        self.assertEqual(s['power'],2)

    def test_cover_protects_only_leak_in_declared_lane(self):
        s=crisis();s['power']=1
        wrong=crew_step(s,(1,1,1,1),{'dispatch':{'kind':'cover','lane':1}})
        correct=crew_step(s,(1,1,1,1),{'dispatch':{'kind':'cover','lane':2}})
        self.assertEqual(wrong['finished'],'LOSS_HULL')
        self.assertIsNone(correct['finished'])
        self.assertEqual(correct['hull'],1)
        self.assertEqual(correct['history'][-1]['cover_saved'],1)
        self.assertEqual(correct['power'],0)

    def test_recharge_requires_a_collision_and_respects_cap(self):
        s=engine.new_game([[] for _ in range(8)])
        s['coolant']=1;s['power']=2
        s['board']=[dict(id='p',lane=0,sign=1,strength=1,depth=1,held=False),
                    dict(id='m',lane=0,sign=-1,strength=1,depth=1,held=False)]
        good=crew_step(s,(1,0,1,2),{'dispatch':{'kind':'recharge','lane':0}})
        bad=crew_step(s,(1,0,1,2),{'dispatch':{'kind':'recharge','lane':2}})
        self.assertEqual(good['coolant'],3)
        self.assertEqual(bad['coolant'],1)
        self.assertEqual(good['history'][-1]['recharged'],2)
        self.assertEqual(good['power'],2) # 2 - 1 + 1 collision

    def test_same_orders_and_assignment_independent_of_player_count(self):
        # Seat assignments are the only changed input; the common reducer has
        # no hidden bonus for adding humans.
        s=crisis();p={'engineer':{'build':1},'dispatch':{'kind':'cover','lane':2}}
        for players in range(1,5):
            assigned=deterministic_assignment((1,0,2,1),players,7)
            out=staffed_step(s,players,assigned,p)
            self.assertEqual(out['hull'],1)
            self.assertEqual(out['power'],0)
            self.assertEqual(out['levels'],[2,1,0])

    def test_full_session_witnesses_replay_exactly(self):
        data=json.loads((DOCS/'phase06-crew-witnesses.json').read_text())
        self.assertEqual(data,json.loads(json.dumps(build())))
        for witness in data['witnesses']:
            variants=witness['variants']
            for name,record in variants.items():
                state=replay(record['waves'],record['decisions'],4)
                self.assertEqual(state['finished'],record['outcome'])
                self.assertEqual(state['hull'],record['hull'])
                self.assertEqual(len(state['history']),record['rounds'])
            self.assertNotEqual(variants['fixed']['outcome'],variants['flexible']['outcome'])

    def test_json_surveys_match_recomputed_independent_sets(self):
        for start,filename in ((231000,'phase06-crew-development.json'),
                               (232000,'phase06-crew-holdout.json')):
            expected=json.loads((DOCS/filename).read_text())
            self.assertEqual(expected,survey(start,40))
            self.assertLess(expected['flexible']['all_seats_active_rounds'],
                            expected['flexible']['played_rounds']//3)

    def test_incomplete_execution_and_illegal_future_orders(self):
        s=crisis()
        with self.assertRaises(ValueError):crew_step(dict(s,finished='WIN'),FIXED,{})
        with self.assertRaises(ValueError):crew_step(s,FIXED,{'pilot':[]})
        with self.assertRaises(ValueError):crew_step(s,FIXED,{'engineer':{'service':False}})
        with self.assertRaises(ValueError):crew_step(s,(2,0,1,1),{'nav':[{'kind':'DAMP','token':'threat'}]})


if __name__=='__main__':unittest.main()
