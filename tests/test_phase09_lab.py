"""Research-only objective, storm-choice and complementarity regression tests."""
import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State,Token
from experiments.phase06_lab import Experiment,step as base_step
from experiments.phase09_lab import Trial,step,victory,mission_offers,MISSIONS
from experiments.phase09_market import new as market_new,choose,available
from experiments.phase09_coop_probe import probe


class Phase09Rules(unittest.TestCase):
    def test_missions_have_distinct_exact_predicates(self):
        s=State(round=9,hp=5,progress=(3,3,2))
        self.assertTrue(victory('grid',s))
        self.assertFalse(victory('fortress',s))
        self.assertFalse(victory('voltage',s))
        self.assertTrue(victory('voltage',s,large_mask=3))
        self.assertFalse(victory('concord',s,synchronized=1))
        self.assertTrue(victory('concord',s,synchronized=2))
        self.assertFalse(victory('circuit',s,lane_mask=3))
        self.assertTrue(victory('circuit',s,lane_mask=7))
        self.assertFalse(victory('grid',replace(s,hp=0)))
        self.assertRaises(ValueError,victory,'unrecognized',s)

    def test_no_mission_change_to_current_grid_rules(self):
        # All 7 first-party storm cards are consumed in each 9-round match.
        for seed in (2,8,17,41,317):
            plain=Experiment.new('market',seed=seed)
            wrapped=Trial.new('grid',seed=seed)
            while not plain.state.over:
                plain=base_step(plain,draft=0 if plain.state.round<7 else None)
                wrapped=step(wrapped,draft=0 if wrapped.state.round<7 else None)
                self.assertEqual(plain.state,wrapped.state)

    def test_history_and_cap_saturation_are_not_false_zero_matches(self):
        s=State(round=8,hp=7,progress=(3,2,2),tokens=(
            Token(1,0,0,1,1),Token(2,0,0,-1,1)),next_id=3)
        g=Trial.new('circuit',state=s,waves=((),)*9,lane_mask=6)
        out=step(g)
        self.assertEqual(out.state.over,'win')
        self.assertEqual(out.lane_mask,7)
        self.assertEqual(out.state.progress,(3,2,2))

    def test_no_automatic_powered_lane_from_empty_match(self):
        s=State(round=8,hp=7,progress=(3,2,2),tokens=(Token(1,0,0,1,1),),next_id=2)
        g=Trial.new('circuit',state=s,waves=((),)*9,lane_mask=6)
        after=step(g)
        self.assertNotEqual(after.lane_mask,7)
        self.assertEqual(after.state.over,'loss: target')

    def test_public_mission_offer_deterministic_and_distinct(self):
        for seed in range(150):
            a,b=mission_offers(seed)
            self.assertIn(a,MISSIONS)
            self.assertIn(b,MISSIONS)
            self.assertNotEqual(a,b)
            self.assertEqual((a,b),mission_offers(seed))

    def test_invalid_mission_and_plan_rejected(self):
        self.assertRaises(ValueError,Trial.new,'nonsense')
        g=Trial.new('grid')
        self.assertRaises(ValueError,step,g,tuple([('pass',)]*5))
        self.assertRaises(ValueError,step,g,draft=3)
        self.assertEqual(g.state.round,0)

    def test_market_width_two_matches_original_for_pass_only(self):
        for seed in (1,2,6,15,50):
            first=Experiment.new('market',seed=seed)
            other=market_new(seed,2)
            while not first.state.over:
                choice=0 if first.state.round<7 else None
                first=base_step(first,draft=choice)
                other=choose(other,choice)
                self.assertEqual(first.state,other.state)
                self.assertEqual(first.game.available,other.game.available)
                self.assertEqual(first.game.cursor,other.game.cursor)

    def test_market_width_only_reorders_never_discards_cards(self):
        for width in (1,2,3):
            g=market_new(271,width,waves=((),)*9)
            chosen=[]
            for _ in range(7):
                self.assertLessEqual(len(available(g)),width)
                idx=min(1,len(g.game.available)-1)
                chosen.append(g.game.available[idx])
                g=choose(g,idx)
            self.assertEqual(set(chosen),set(range(7)))
            while not g.state.over:
                g=choose(g,None)
            self.assertEqual(g.state.round,9)

    def test_bad_market_width_and_choice_rejected(self):
        for width in (0,4,True,'3'):
            self.assertRaises(ValueError,market_new,0,width)
        g=market_new(1,3)
        self.assertRaises(ValueError,choose,g,3)
        self.assertRaises(ValueError,choose,g,True)
        self.assertEqual(g.state.round,0)

    def test_missions_have_reproducible_terminal_outcomes(self):
        for mission in MISSIONS:
            g=Trial.new(mission,seed=271)
            while not g.state.over:
                g=step(g,draft=0 if g.state.round<7 else None)
            g2=Trial.new(mission,seed=271)
            while not g2.state.over:
                g2=step(g2,draft=0 if g2.state.round<7 else None)
            self.assertEqual(g,g2)

    def test_mechanical_complementarity_exists_but_is_not_human_proof(self):
        x=probe(1,44000)
        self.assertGreater(x['count']['strict_complements'],0)
        self.assertGreater(x['example']['scores']['both'],x['example']['scores']['pass'])
        self.assertLessEqual(x['example']['scores']['first'],x['example']['scores']['pass'])
        self.assertLessEqual(x['example']['scores']['second'],x['example']['scores']['pass'])


if __name__=='__main__':unittest.main()
