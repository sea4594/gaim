import unittest
from collections import Counter
from experiments.phase15_survey import base_board
from experiments.phase15_forecast_council import make_world
from experiments.phase17_storm_weave import weave_pair,apply_weave,payload_histogram,route_histogram
from experiments.phase17_survey import follow,evaluate

A=((0,1,2),(1,-1,1));B=((2,-1,2),(0,1,1))
class WeaveContract(unittest.TestCase):
    def test_preserves_every_route_and_payload_across_both_offers(self):
        changed=weave_pair(A,B)
        self.assertEqual(route_histogram(changed),route_histogram((A,B)))
        self.assertEqual(payload_histogram(changed),payload_histogram((A,B)))
        self.assertNotEqual(changed,(A,B))
        self.assertEqual(weave_pair(*changed),(A,B))
    def test_rejects_invalid_pairs(self):
        for a,b in ((A,B[:1]),((),()),(((4,1,1),),((1,-1,1),))):
            with self.assertRaises(ValueError):weave_pair(a,b)
    def test_cost_exactly_one_coolant_and_doesnt_mutate_original(self):
        g=make_world(base_board(270100),A,B)
        original=g.state
        out=apply_weave(g)
        self.assertEqual(g.state,original)
        self.assertEqual(out.state.coolant,g.state.coolant-1)
        self.assertEqual(tuple(out.game.deck[i] for i in out.game.available),weave_pair(A,B))
    def test_two_future_storms_are_not_deleted(self):
        g=make_world(base_board(270100),A,B)
        changed=apply_weave(g)
        self.assertEqual(len(changed.game.deck),len(g.game.deck))
        self.assertEqual(len(changed.game.available),2)
        end=follow(changed,0,('pass',),horizon=2)
        self.assertEqual(end.state.round,g.state.round+2)
    def test_reproducible_comparison(self):
        g=make_world(base_board(270100),A,B)
        self.assertEqual(evaluate(g,3,8),evaluate(g,3,8))

if __name__=='__main__':unittest.main()
