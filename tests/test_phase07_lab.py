import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State,Token
from experiments.phase07_lab import Audit,step,demand_options
from experiments.phase06_lab import step as market_step

EMPTY=tuple(() for _ in range(9))

class Pass07Tests(unittest.TestCase):
    def make(self,mode='market',round=8,progress=(3,2,3),tokens=(),hp=7):
        return Audit.new(mode,state=State(round=round,hp=hp,progress=progress,tokens=tokens,
                        next_id=max((t.id for t in tokens),default=0)+1),waves=EMPTY)
    def test_market_exact_parity(self):
        for seed in range(20):
            a=Audit.new('market',seed=seed)
            b=a.experiment
            while not a.state.over:
                a=step(a)
                b=market_step(b)
                self.assertEqual(a.state,b.state)
    def test_demand_rotates_and_consumes(self):
        g=self.make('demand',round=2)
        self.assertEqual(demand_options(g),(0,))
        result=step(g)
        self.assertEqual(result.state.progress,(2,2,3))
        self.assertEqual(result.serviced,1)
    def test_blackout_hurts_hull(self):
        g=self.make('demand',round=2,progress=(0,2,3),hp=4)
        result=step(g)
        self.assertEqual(result.state.hp,3)
        self.assertEqual(result.blackouts,1)
    def test_flex_selection_consumes_alternate(self):
        g=self.make('flex_demand',round=2,progress=(0,2,3),hp=4)
        a=step(g,demand=1);b=step(g,demand=0)
        self.assertEqual(a.state.hp,4)
        self.assertEqual(a.state.progress,(0,1,3))
        self.assertEqual(b.state.hp,3)
    def test_illegal_demand_rejected(self):
        g=self.make('flex_demand',round=2)
        with self.assertRaises(ValueError):step(g,demand=2)
        with self.assertRaises(ValueError):step(self.make('market'),demand=1)
    def test_wager_loss_costs_power(self):
        s=self.make('pledge',round=6,progress=(3,2,3))
        a=step(s,pledge=('surge',1));b=step(s)
        self.assertEqual(a.state.progress,(3,1,3))
        self.assertEqual(b.state.progress,(3,2,3))
        self.assertEqual(a.wagers_won,0)
    def test_sync_wager_repaid_and_profitable(self):
        toks=(Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,2,0,1,1),Token(4,2,0,-1,1))
        g=self.make('pledge',round=6,progress=(2,2,2),tokens=toks)
        result=step(g,pledge=('sync',1))
        self.assertEqual(result.state.progress[1],3)
        self.assertEqual(result.wagers_won,1)
    def test_pledge_only_even_turns_one_and_must_afford(self):
        with self.assertRaises(ValueError):step(self.make('pledge',round=7),pledge=('sync',0))
        with self.assertRaises(ValueError):step(self.make('pledge',round=6,progress=(0,2,3)),pledge=('sync',0))
    def test_tide_moves_far_band_only(self):
        toks=(Token(1,0,2,1,1),Token(2,2,2,-1,1),Token(3,2,1,1,1))
        g=self.make('tide',round=1,tokens=toks)
        result=step(g)
        # FAR -> SOON then lateral drift; newly drifted tokens move to Center.
        self.assertEqual([t.id for t in result.state.tokens],[1,2,3])
        self.assertEqual(tuple(t.lane for t in result.state.tokens[:2]),(1,1))
    def test_purity_and_errors(self):
        g=self.make('demand',round=2)
        with self.assertRaises(ValueError):step(g,demand=9)
        self.assertEqual(g.state.progress,(3,2,3))

if __name__=='__main__':unittest.main()

class CouncilCounterexamples(unittest.TestCase):
    def test_last_checkpoint_council_choice_changes_victory(self):
        # Before the third checkpoint: two earlier demands already serviced.
        # Paying Right empties it, while paying Left retains 1+ in all lanes.
        s=State(round=8,hp=7,progress=(3,2,1),next_id=1)
        g=Audit(Audit.new('council',state=s,waves=EMPTY).experiment,'council',serviced=2)
        right=step(g,demand=2)
        left=step(g,demand=0)
        self.assertEqual(right.state.over,'loss: target')
        self.assertEqual(left.state.over,'win')
        self.assertEqual(left.state.progress,(2,2,1))
        self.assertEqual(right.serviced,3)
        self.assertEqual(left.serviced,3)

    def test_checkpoint_must_be_paid_and_changes_survival(self):
        s=State(round=8,hp=1,progress=(3,2,0),next_id=1)
        g=Audit(Audit.new('council',state=s,waves=EMPTY).experiment,'council',serviced=2)
        unpaid=step(g,demand=2)
        paid=step(g,demand=0)
        self.assertEqual(unpaid.state.over,'loss: breach')
        self.assertEqual(paid.state.hp,1)

    def test_checkpoint_lanes_are_deterministic_and_public(self):
        for round_index,expected in ((2,(0,1)),(5,(1,2)),(8,(2,0))):
            s=State(round=round_index,progress=(1,1,1))
            g=Audit.new('council',state=s,waves=EMPTY)
            self.assertEqual(demand_options(g),expected)

    def test_three_demand_serviced_goal_is_real(self):
        s=State(round=8,hp=7,progress=(3,2,1))
        game=Audit.new('council',state=s,waves=EMPTY)
        zero_service=Audit(game.experiment,'council',serviced=0)
        one_service=Audit(game.experiment,'council',serviced=1)
        self.assertEqual(step(zero_service,demand=0).state.over,'loss: target')
        self.assertEqual(step(one_service,demand=0).state.over,'win')
