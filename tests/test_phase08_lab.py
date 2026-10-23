"""Exact Phase 08 acceptance cases: no shipping changes."""
import unittest
from dataclasses import replace
from experiments.phase08_lab import Trial,step
from reference.charge_loom_v01 import State,Token

EMPTY=((),)*9

class MechanicTests(unittest.TestCase):
    def fixture(self,mode='control',**attrs):
        state=State(seed=1,**attrs)
        return Trial.new(mode=mode,state=state,waves=EMPTY)

    def test_control_matches_free_market(self):
        from experiments.phase06_lab import step as base_step
        g=self.fixture()
        self.assertEqual(step(g,draft=1).state,base_step(g.exp,draft=1).state)

    def test_coolant_bid_costs_exactly_one(self):
        s=dict(coolant=3)
        old=step(self.fixture('coolant_bid',**s),draft=0)
        newer=step(self.fixture('coolant_bid',**s),draft=1)
        self.assertEqual(old.state.coolant-newer.state.coolant,1)
        self.assertEqual(newer.paid_drafts,1)
        self.assertEqual(self.fixture('coolant_bid',**s).state.coolant,3)

    def test_coolant_bid_refuses_when_empty(self):
        g=self.fixture('coolant_bid',coolant=0)
        with self.assertRaises(ValueError):step(g,draft=1)
        self.assertEqual(g.state.coolant,0)

    def test_power_bid_cost_and_refusal(self):
        g=self.fixture('power_bid',progress=(0,1,0))
        self.assertEqual(step(g,draft=1).state.progress[1],0)
        with self.assertRaises(ValueError):step(self.fixture('power_bid',progress=(0,0,0)),draft=1)

    def test_repair_cost_and_cap(self):
        g=self.fixture('repair',progress=(3,0,0),hp=6)
        out=step(g,actions=(('repair',0),))
        self.assertEqual(out.state.hp,7)
        self.assertEqual(out.state.progress,(1,0,0))
        self.assertTrue(out.repaired)
        with self.assertRaises(ValueError):step(out,actions=(('repair',0),))

    def test_repair_insufficient_and_invalid(self):
        for pr,hp in (((1,0,0),4),((3,0,0),7)):
            with self.assertRaises(ValueError):step(self.fixture('repair',progress=pr,hp=hp),actions=(('repair',0),))

    def test_council_different_payment_results(self):
        # Round 9: options Left or Right, no future wave. State has paid two checkpoints.
        g=self.fixture('council',round=8,progress=(3,2,1),hp=7)
        g=replace(g,council=replace(g.council,serviced=2))
        left=step(g,demand=0)
        right=step(g,demand=2)
        self.assertEqual(left.state.progress,(2,2,1))
        self.assertEqual(right.state.progress,(3,2,0))
        self.assertEqual(left.state.over,'win')
        self.assertEqual(right.state.over,'loss: target')

    def test_council_coolant_combination(self):
        g=self.fixture('council_coolant',round=0,coolant=2)
        out=step(g,draft=1)
        self.assertEqual(out.state.coolant,1)
        self.assertEqual(out.council.mode,'council')

    def test_four_action_limit_kept_in_other_modes(self):
        for mode in ('control','coolant_bid','power_bid','repair','council','council_coolant','surge'):
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                step(self.fixture(mode),actions=(('pass',),)*5)

    def test_surge_spawns_both_and_preserves_remaining_waves(self):
        waves=(((0,1,1),),((1,-1,2),),((2,1,1),),((0,-1,2),),
               ((1,1,2),),((2,-1,1),),((0,1,2),),(),())
        g=Trial.new('surge',seed=2,waves=waves,state=State(hp=100,seed=2))
        a=step(g,surge=True)
        self.assertTrue(a.surged)
        self.assertEqual(a.state.coolant,g.state.coolant-1)
        self.assertEqual(len(a.state.tokens),2)
        self.assertEqual({(t.lane,t.sign,t.size) for t in a.state.tokens},
                         {(0,1,1),(1,-1,2)})
        self.assertEqual(len(a.exp.game.available),2)
        with self.assertRaises(ValueError):step(a,surge=True)
        observed=[]
        while not a.state.over:
            a=step(a)
            observed += [(t.lane,t.sign,t.size) for t in a.state.tokens if t.row==1 and t.id>=3]
        self.assertEqual(len(observed),5)
        self.assertEqual(a.state.next_id,8)

    def test_surge_refuses_without_coolant(self):
        g=self.fixture('surge',coolant=0)
        with self.assertRaises(ValueError):step(g,surge=True)

    def test_surge_creates_early_pair_payoff(self):
        waves=(((0,1,2),),((0,-1,2),),(),(),(),(),(),(),())
        state=State(seed=2,hp=7)
        normal=Trial.new('surge',state=state,waves=waves)
        rush=normal
        for r in range(3):
            normal=step(normal)
            rush=step(rush,surge=(r==0))
        self.assertEqual(normal.state.hp,5)
        self.assertEqual(rush.state.hp,7)
        self.assertEqual(rush.state.progress[0],2)

    def test_surge_spending_coolant_can_cause_immediate_loss(self):
        waves=((),)*9
        state=State(seed=2,hp=1,coolant=1,tokens=(Token(1,0,0,1,1),),next_id=2)
        g=Trial.new('surge',state=state,waves=waves)
        safe=step(g,actions=(('damp',1),))
        unsafe=step(g,surge=True)
        self.assertFalse(safe.state.over)
        self.assertEqual(unsafe.state.over,'loss: breach')

    def test_seed_replay_for_all_modes(self):
        for mode in ('control','coolant_bid','power_bid','repair','council','council_coolant','surge'):
            with self.subTest(mode=mode):
                a=Trial.new(mode,seed=9)
                b=Trial.new(mode,seed=9)
                while not a.state.over:
                    a=step(a)
                    b=step(b)
                    self.assertEqual(a,b)

if __name__=='__main__': unittest.main()
