"""No shipping rule changes: test opt-in split-forecast experiment contracts."""
from __future__ import annotations
import unittest
from dataclasses import replace
from experiments.phase06_lab import Experiment, step
from experiments.phase15_forecast_council import (
    public_view, private_view, candidate_edits, resolve, make_world,
    payoff_table, information_value, truthful_signal, signal_value,
    two_signal_value,score)
from experiments.phase15_survey import survey

class LimitedInformationContract(unittest.TestCase):
    def setUp(self):
        self.g=Experiment.new('market',seed=200)
        self.g=step(self.g,draft=0)

    def test_public_view_has_no_undisclosed_storm_card_values(self):
        g=self.g
        choices=g.game.available
        a=make_world(g, ((0,1,2),(1,-1,2)),((2,1,1),(0,1,1)))
        b=make_world(g, ((2,-1,1),(2,-1,2)),((1,1,2),(1,-1,2)))
        self.assertEqual(public_view(a), public_view(b))
        self.assertNotEqual(private_view(a,'routes'),private_view(b,'routes'))
        self.assertNotEqual(private_view(a,'polarity'),private_view(b,'polarity'))
        self.assertNotEqual(private_view(a,'strength'),private_view(b,'strength'))
        self.assertEqual(g.game.available,choices)

    def test_private_views_are_strictly_sensor_limited(self):
        g=self.g
        a=make_world(g, ((0,1,1),(1,-1,2)),((2,1,1),))
        b=make_world(g, ((0,-1,2),(1,1,1)),((2,-1,2),))
        self.assertEqual(private_view(a,'routes'),private_view(b,'routes'))
        self.assertNotEqual(private_view(a,'polarity'),private_view(b,'polarity'))
        with self.assertRaises(ValueError):private_view(g,'oracle')

    def test_sealed_edit_cannot_target_unseen_new_tokens(self):
        g=self.g
        old_ids={t.id for t in g.state.tokens}
        for a in candidate_edits(g):
            if a != ('pass',):self.assertIn(a[1],old_ids)
        fresh_id=max(old_ids)+1
        self.assertNotIn(('hold',fresh_id),candidate_edits(g))
        with self.assertRaises(ValueError):resolve(g,0,('hold',fresh_id))

    def test_resolution_matches_unmodified_market_reducer(self):
        g=self.g
        a=next(a for a in candidate_edits(g) if a!=('pass',))
        original=g
        out=resolve(g,1,a)
        expected=step(g,(a,),draft=1)
        self.assertEqual(out,expected)
        self.assertEqual(g,original)
        with self.assertRaises(ValueError):resolve(g,9,a)
        with self.assertRaises(ValueError):resolve(g,True,a)

    def test_signal_facts_are_truthful_and_binary(self):
        g=make_world(self.g,((0,1,2),(0,-1,1)),((1,-1,1),(2,1,1)))
        self.assertEqual(truthful_signal(g,'left_route'),1)
        self.assertEqual(truthful_signal(g,'negative'),0)
        self.assertEqual(truthful_signal(g,'large'),1)
        with self.assertRaises(ValueError):truthful_signal(g,'perfect')

    def test_information_upper_bound_can_be_strict(self):
        a=('pass',);b=('shift',1,1)
        worlds=[{a:(10,10),b:(0,0)},{a:(0,0),b:(10,10)}]
        x=information_value(worlds)
        self.assertEqual(x['blind'],5)
        self.assertEqual(x['one_bit_upper'],10)
        self.assertEqual(x['perfect_upper'],10)
        self.assertEqual(signal_value(worlds,[0,1]),10)
        self.assertEqual(signal_value(worlds,[0,0]),5)
        self.assertEqual(two_signal_value(worlds,[0,0],[0,1]),10)

    def test_no_information_value_when_same_action_always_best(self):
        worlds=[{('pass',):(10,10),('hold',1):(3,3)},
                {('pass',):(9,9),('hold',1):(2,2)}]
        self.assertEqual(information_value(worlds)['perfect_value'],0)

    def test_research_deterministic_heldout(self):
        a=survey(6,215000,horizon=3)
        b=survey(6,215000,horizon=3)
        self.assertEqual(a,b)
        self.assertLessEqual(a['mean_truthful_gain']['negative'],a['mean_signal_value']+1e-7)
        self.assertLessEqual(a['mean_two_signal_gain'],a['mean_perfect_information_value']+1e-7)

if __name__=='__main__':unittest.main()
