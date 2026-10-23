"""Exact semantics, non-dominance, and safe rejection tests for pass 14."""
import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State, Token
from experiments.phase14_network import Network, step, options
from experiments.phase06_lab import Experiment, step as forecast_step

EMPTY=((),)*9

def game(mode,round=7,progress=(3,1,2),hp=7,tokens=(),link=None,served=(False,False,False)):
    s=State(round=round,progress=progress,hp=hp,tokens=tuple(tokens),
            next_id=1+max((t.id for t in tokens),default=0),seed=7)
    return Network.new(mode,state=s,waves=EMPTY,link=link,served=served)

class Phase14NetworkTest(unittest.TestCase):
    def test_no_bridge_on_network(self):
        with self.assertRaises(ValueError): step(game('conduit'), [('bridge',0,1)])

    def test_new_link_not_active_until_following_round(self):
        before=game('conduit',round=5,progress=(3,0,0))
        built=step(before,[('wire',0,1)])
        self.assertEqual(built.state.progress,(2,0,0))
        self.assertEqual(built.link,(0,1))
        next_round=step(built)
        self.assertEqual(next_round.state.progress,(1,1,0))
        self.assertEqual(next_round.transferred,1)

    def test_conduit_transfers_before_collision(self):
        # Capacity is freed before the incoming collision: total power increases.
        toks=(Token(1,0,0,1,1),Token(2,0,0,-1,1))
        linked=game('conduit',round=8,progress=(3,1,2),tokens=toks,link=(0,1))
        control=game('control',round=8,progress=(3,1,2),tokens=toks)
        out=step(linked)
        no=step(control)
        self.assertEqual(out.state.progress,(3,2,2))
        self.assertEqual(no.state.progress,(3,1,2))
        self.assertEqual(out.transferred,1)

    def test_source_retains_one_power_and_destination_cap(self):
        self.assertEqual(step(game('switch',progress=(1,1,2),link=(0,1))).transferred,0)
        self.assertEqual(step(game('switch',progress=(3,3,1),link=(0,1))).transferred,0)

    def test_switch_config_free_but_action_costs_edit(self):
        g=game('switch',round=6,progress=(0,0,0))
        self.assertIn(('wire',0,1),options(g))
        a=step(g,[('wire',0,1)])
        self.assertEqual(a.state.progress,(0,0,0))
        self.assertEqual(a.invested,0)

    def test_conduit_option_needs_preexisting_power(self):
        self.assertNotIn(('wire',0,1),options(game('conduit',progress=(0,0,0))))
        with self.assertRaises(ValueError):step(game('conduit',progress=(0,0,0)),[('wire',0,1)])

    def test_one_structure_per_round_and_reject_bad_lanes(self):
        g=game('conduit',round=5,progress=(3,3,3))
        for a in ((('wire',0,2),),(('wire',True,1),),(('wire',0,1),('wire',1,2))):
            with self.subTest(a=a),self.assertRaises(ValueError):step(g,a)

    def test_immutable_rejected_action(self):
        g=game('conduit',round=5)
        with self.assertRaises(ValueError):step(g,[('wire',0,2)])
        self.assertIsNone(g.link)
        self.assertEqual(g.state.progress,(3,1,2))

    def test_delivery_before_generated_energy(self):
        tok=(Token(1,0,0,1,2),Token(2,0,0,-1,2))
        g=game('service',round=7,progress=(1,0,0),tokens=tok)
        with self.assertRaises(ValueError):step(g,[('deliver',0)])
        obtained=step(g)
        self.assertEqual(obtained.state.progress[0],3)
        self.assertIn(('deliver',0),options(obtained))

    def test_service_goal_replaces_original_goal(self):
        # Complete two loads, finish with 4 stored power: no lane minimum.
        g=game('service',round=8,progress=(3,0,1),served=(True,True,False))
        self.assertEqual(step(g).state.over,'win')
        control=game('control',round=8,progress=(3,0,1))
        self.assertNotEqual(step(control).state.over,'win')

    def test_service_spends_power_and_may_destroy_victory(self):
        g=game('service',round=8,progress=(3,0,2),served=(True,True,False))
        self.assertEqual(step(g).state.over,'win')
        self.assertNotEqual(step(g,[('deliver',2)]).state.over,'win')

    def test_control_exact_engine_parity(self):
        # Includes the real two-offer market and all existing edits.
        first=Network.new('control',seed=123)
        direct=Experiment.new('market',seed=123)
        for i in range(9):
            if first.state.over:break
            draft=1 if i%2==0 and i<7 else 0 if i<7 else None
            first=step(first,draft=draft)
            direct=forecast_step(direct,draft=draft)
            self.assertEqual(first.exp,direct)

    def test_player_count_unchanged_four_edit_budget(self):
        g=game('switch',round=6,progress=(3,3,3))
        with self.assertRaises(ValueError):step(g,[('wire',0,1)]*5)

if __name__ == '__main__':unittest.main()

class Phase14MultiRoundTest(unittest.TestCase):
    def test_conduit_can_convert_three_wasted_matches_into_distributed_victory(self):
        # Three pairs approach Left on consecutive rounds. Configuring a
        # conduit in advance redirects production that would hit cap=3.
        toks=tuple(Token(i*2+1,0,i,1,1) for i in range(3))+tuple(
            Token(i*2+2,0,i,-1,1) for i in range(3))
        s=State(round=6,hp=7,progress=(3,1,2),tokens=toks,next_id=7,seed=117)
        net=Network.new('conduit',state=s,waves=EMPTY)
        base=Network.new('control',state=s,waves=EMPTY)
        net=step(net,[('wire',0,1)])
        base=step(base)
        while not net.state.over:net=step(net)
        while not base.state.over:base=step(base)
        self.assertEqual(net.transferred,2)
        self.assertEqual(net.state.progress,(3,3,2))
        self.assertEqual(net.state.over,'win')
        self.assertEqual(base.state.progress,(3,1,2))
        self.assertEqual(base.state.over,'loss: target')

    def test_paid_build_is_worse_when_no_future_production(self):
        s=State(round=8,progress=(3,3,2),hp=7,seed=4)
        base=step(Network.new('control',state=s,waves=EMPTY))
        paid=step(Network.new('conduit',state=s,waves=EMPTY),[('wire',0,1)])
        self.assertEqual(base.state.over,'win')
        self.assertEqual(paid.state.over,'loss: target')
