"""Executable Phase 5 cooperative-architecture rejection/acceptance checks."""
import unittest
import json
from pathlib import Path
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.survey import engine_waves
from experiments.redesign_phase5.coop import (owned_step, owners, joint_step,
        construction_seats, guarded_step)
from experiments.redesign_phase5.survey import run,survey
from experiments.redesign_phase5.make_witnesses import replay
DOCS=Path(__file__).resolve().parents[1]/'docs/redesign'


def late_crisis():
    s=engine.new_game([[] for _ in range(8)])
    s.update(round=8, levels=[2,1,0], hull=1, power=3,
             board=[dict(id='threat',lane=0,sign=1,strength=2,depth=1,held=False)])
    return s


class Phase5CoopTests(unittest.TestCase):
    def test_ownership_rotates_solo_and_four_players(self):
        self.assertEqual(owners(4,1),(0,1,2,0))
        self.assertEqual(owners(4,2),(0,0,1,2))
        for players in range(1,5):
            for r in range(1,9):
                a,b=construction_seats(players,r)
                self.assertIn(a,range(players))
                self.assertIn(b,range(players))
                self.assertNotEqual(a,b) if players>1 else self.assertEqual(a,b)

    def test_owned_intervention_respects_lane_seats_and_budget(self):
        s=engine.new_game(engine_waves(301))
        legal={'kind':'SHIFT','token':'r1t0','delta':1}
        # Use a known valid difference-free board instead of relying on RNG.
        s['waves'][0]=[dict(lane=i,sign=1,strength=1) for i in range(3)]
        out=owned_step(s,4,{0:legal})
        self.assertEqual(out['history'][-1]['owned_seats'],[0])
        with self.assertRaisesRegex(ValueError,'personal lane'):
            owned_step(s,4,{1:legal})
        with self.assertRaisesRegex(ValueError,'Shared edit budget'):
            owned_step(s,4,{0:legal,1:dict(kind='DAMP',token='r1t1'),
                            2:dict(kind='HOLD',token='r1t2')})
        self.assertEqual(s['round'],1)
        self.assertEqual(s['board'],[])

    def test_owned_solo_retains_two_edits(self):
        s=engine.new_game([[] for _ in range(8)])
        s['board']=[dict(id='a',lane=0,sign=1,strength=1,depth=1,held=False),
                    dict(id='b',lane=2,sign=-1,strength=1,depth=1,held=False)]
        plan=[dict(kind='SHIFT',token='a',delta=1),dict(kind='SHIFT',token='b',delta=-1)]
        self.assertEqual(owned_step(s,1,{0:plan})['history'][-1]['matched'][1],1)

    def test_joint_build_proposer_and_funding_both_change_endgame(self):
        s=late_crisis()
        rush=joint_step(s,4,1,'rush')
        slow=joint_step(s,4,1,'standard')
        other=joint_step(s,4,2,'rush')
        self.assertEqual(rush['finished'],'WIN')
        self.assertEqual(slow['finished'],'LOSS_HULL')
        self.assertEqual(other['finished'],'LOSS_HULL')
        self.assertEqual(rush['levels'],[2,2,0])
        self.assertEqual(rush['power'],0)
        self.assertEqual(rush['history'][-1]['joint']['proposer'],3)
        self.assertEqual(rush['history'][-1]['joint']['financier'],0)
        self.assertEqual(s['power'],3)
        self.assertEqual(s['levels'],[2,1,0])

    def test_joint_early_rush_immediate_aegis_effect(self):
        s=engine.new_game([[] for _ in range(8)])
        s['levels']=[0,0,0];s['power']=3;s['hull']=5
        s['board']=[dict(id='danger',lane=0,sign=1,strength=2,depth=1,held=False)]
        slow=joint_step(s,2,1,'standard')
        rush=joint_step(s,2,1,'rush')
        self.assertEqual(slow['hull'],3)
        self.assertEqual(rush['hull'],4)
        self.assertEqual(slow['pending'],1)
        self.assertIsNone(rush['pending'])
        self.assertEqual(rush['levels'][1],1)

    def test_joint_requires_real_resources_both_partners_and_no_offline(self):
        s=late_crisis()
        for p,f in [(None,'rush'),(1,None),(2,'cheap'),(7,'rush')]:
            with self.assertRaises(ValueError):joint_step(s,4,p,f)
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            joint_step(dict(s,power=2),4,1,'rush')
        with self.assertRaisesRegex(ValueError,'unavailable'):
            joint_step(dict(s,outages=[False,True,False]),4,1,'rush')
        self.assertEqual(joint_step(s,1,1,'rush')['finished'],'WIN')

    def test_guard_truth_with_primary_and_skipped_backup(self):
        s=engine.new_game([[] for _ in range(8)])
        s['board']=[dict(id='a',lane=0,sign=1,strength=2,depth=1,held=False),
                    dict(id='b',lane=1,sign=-1,strength=1,depth=1,held=False)]
        primary=dict(kind='SHIFT',token='b',delta=-1)
        backup=dict(kind='DAMP',token='a')
        # After primary, left has net +1 leak. Backup reduces it to zero.
        yes=guarded_step(s,2,primary,backup,dict(lane=0,min_leak=1))
        no=guarded_step(s,2,primary,backup,dict(lane=0,min_leak=2))
        self.assertTrue(yes['history'][-1]['guard']['triggered'])
        self.assertFalse(no['history'][-1]['guard']['triggered'])
        self.assertEqual(yes['coolant'],1)
        self.assertEqual(no['coolant'],2)
        self.assertEqual(yes['hull'],6)
        self.assertEqual(no['hull'],5)
        self.assertEqual(s['coolant'],2)
        # This exact result could be achieved with the public open action.
        direct=engine.step(s,dict(edits=[primary,backup]))
        for k in ('board','hull','power','coolant','levels','finished'):
            self.assertEqual(yes[k],direct[k])

    def test_guard_never_beats_informed_unconditional_equivalent(self):
        for seed in range(4):
            s=engine.new_game(engine_waves(seed+222))
            s['board']=[dict(id='a',lane=0,sign=1,strength=2,depth=1,held=False),
                        dict(id='b',lane=1,sign=-1,strength=1,depth=1,held=False)]
            primary=dict(kind='SHIFT',token='b',delta=-1)
            backup=dict(kind='DAMP',token='a')
            for cond in (dict(lane=0,min_leak=1),dict(lane=0,min_match=3),
                         dict(lane=1,min_leak=1)):
                guarded=guarded_step(s,3,primary,backup,cond)
                edits=guarded['history'][-1]['edits']
                ordinary=engine.step(s,dict(edits=edits))
                for k in ('board','hull','power','coolant','pending','finished'):
                    self.assertEqual(guarded[k],ordinary[k])

    def test_seeded_paired_survey_is_reproducible(self):
        self.assertEqual(survey(start=121000,n=2),survey(start=121000,n=2))

    def test_saved_survey_reproducible_and_approach_caveats(self):
        for name,start in [('development',121000),('holdout',122000)]:
            stored=json.loads((DOCS/f'phase05-coop-{name}.json').read_text())
            self.assertEqual(stored,survey(start=start,n=40))
            for players in (1,2,3,4):
                owned=stored['owned'][str(players)]
                self.assertEqual(len(owned['executed_actions_per_seat']),players)
                self.assertLessEqual(owned['owned_wins'],owned['baseline_wins'])
                if players==4:
                    self.assertGreater(owned['minimum_inactive_edit_seat_rounds'],0)
                joint=stored['joint'][str(players)]
                self.assertEqual(joint['baseline']['wins'],joint['standard']['wins'])
            self.assertEqual(stored['guarded']['cases'],stored['guarded']['equivalent_to_informed_open_order'])

    def test_exported_witnesses_replay_every_round(self):
        saved=json.loads((DOCS/'phase05-full-session-witnesses.json').read_text())
        for label,games in saved['witnesses'].items():
            self.assertEqual(len(games),2)
            self.assertEqual(games[0]['replay']['waves'],games[1]['replay']['waves'])
            for game in games:
                s=replay(game)
                self.assertEqual(len(s['history']),8)
            if label=='rush_rescue':
                self.assertNotEqual(games[0]['outcome'],'WIN')
                self.assertEqual(games[1]['outcome'],'WIN')
            if label=='owned_loss':
                self.assertEqual(games[0]['outcome'],'WIN')
                self.assertNotEqual(games[1]['outcome'],'WIN')

    def test_all_three_variants_preserve_original_on_empty_decisions(self):
        waves=engine_waves(66)
        s=engine.new_game(waves)
        baseline=engine.step(s)
        variants=[owned_step(s,1,{}),joint_step(s,4,None,None)]
        for result in variants:
            for key in ('board','hull','power','coolant','levels','pending','finished'):
                self.assertEqual(result[key],baseline[key])

if __name__=='__main__':unittest.main()
