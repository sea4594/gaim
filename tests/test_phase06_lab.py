"""Reproducibility, invariants and mechanical counterexamples for research pass 06."""
import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State,Token
from experiments.phase06_lab import Experiment,step,opportunities,owners,hand,public_forecast
from experiments.phase05_lab import Design,step as established_step

EMPTY=tuple(() for _ in range(9))

class Pass06LabTests(unittest.TestCase):
    def game(self,mode='open',round=8,progress=(2,2,2),tokens=(),hp=7,coolant=3,seed=0):
        return Experiment.new(mode,seed=seed,state=State(round=round,progress=progress,hp=hp,coolant=coolant,
            tokens=tokens,next_id=max([t.id for t in tokens],default=0)+1,seed=seed),waves=EMPTY)

    def test_open_exactly_matches_established_accelerate_bridge_flip(self):
        for seed in range(24):
            x=Experiment.new('open',seed)
            y=Design.new('accelerate',seed)
            while not x.state.over:
                x=step(x)
                y=established_step(y)
                self.assertEqual(x.state,y.state)

    def test_market_preserves_old_order_and_all_available_waves(self):
        for seed in range(5):
            x=Experiment.new('market',seed)
            y=Experiment.new('open',seed)
            while not x.state.over:
                x=step(x,draft=0 if len(x.game.available)>1 else None)
                y=step(y)
                self.assertEqual(x.state,y.state)

    def test_market_new_offer_changes_timing_but_does_not_delete_waves(self):
        waves=(((0,1,1),),((2,-1,2),),(),(),(),(),(),(),())
        a=Experiment.new('market',waves=waves)
        o=step(a,draft=0)
        n=step(a,draft=1)
        self.assertEqual(o.state.tokens[0].lane,0)
        self.assertEqual(n.state.tokens[0].lane,2)
        self.assertEqual(o.game.available,(1,2))
        self.assertEqual(n.game.available,(0,2))

    def test_operator_ownership_rotates_without_changing_total_slots(self):
        for count in (1,2,3,4):
            for round_index in range(9):
                allocated=owners(count,round_index)
                self.assertEqual(len(allocated),4)
                self.assertTrue(all(0<=o<count for o in allocated))
            counts=[sum(owners(count,r).count(i) for r in range(12)) for i in range(count)]
            self.assertLessEqual(max(counts)-min(counts),1)

    def test_operator_rejects_mismatched_card_and_reused_console(self):
        g=self.game('operator',round=7,tokens=(Token(1,0,1,1,1),),progress=(3,3,3))
        h=hand(g.state.seed,g.state.round)
        kind=next(x for x in ('hold','shift','damp','flip','accelerate') if x not in h[0])
        command={'shift':('shift',1,1),'hold':('hold',1),'damp':('damp',1),
                 'flip':('flip',1),'accelerate':('accelerate',1)}[kind]
        with self.assertRaises(ValueError):step(g,(command,),operators=(0,))
        a=('hold',1)
        with self.assertRaises(ValueError):step(g,(a,a),operators=(0,0))

    def test_operator_complementary_consoles_enable_two_action_match(self):
        # The pair of shifts is possible when different shift-capable consoles exist.
        g=self.game('operator',round=8,progress=(3,2,2),tokens=(
            Token(1,0,0,1,1),Token(2,2,0,-1,1)),hp=2)
        consoles=[i for i,pair in enumerate(hand(0,8)) if 'shift' in pair]
        self.assertGreaterEqual(len(consoles),2)
        combo=step(g,(('shift',1,1),('shift',2,-1)),operators=tuple(consoles[:2]))
        self.assertEqual(combo.state.hp,2)
        self.assertEqual(combo.state.over,'win')
        for tid,d in ((1,1),(2,-1)):
            g2=Experiment.new('open',state=g.state,waves=EMPTY)
            alone=step(g2,(('shift',tid,d),))
            self.assertLess(alone.state.hp,combo.state.hp)

    def test_recycle_spends_power_for_coolant_with_both_outcomes(self):
        s=State(round=8,hp=4,progress=(3,2,3),coolant=0,tokens=(),next_id=1)
        g=Experiment.new('recycle',state=s,waves=EMPTY)
        purchased=step(g,(('recycle',1),))
        kept=step(g)
        self.assertEqual(purchased.state.coolant,1)
        self.assertEqual(purchased.state.progress,(3,1,3))
        self.assertNotEqual(purchased.state.over,'win')
        self.assertEqual(kept.state.over,'win')
        with self.assertRaises(ValueError):step(g,(('recycle',0),('recycle',1)))

    def test_regulator_flip_power_cost_and_extra_coolant_for_size_two(self):
        tokens=(Token(1,1,0,1,2),Token(2,1,0,1,2))
        g=self.game('regulator',progress=(3,2,3),tokens=tokens,coolant=0)
        with self.assertRaises(ValueError):step(g,(('flip',1),))
        g=self.game('regulator',progress=(3,2,3),tokens=tokens,coolant=1)
        result=step(g,(('flip',1),))
        self.assertEqual(result.state.coolant,0)
        self.assertEqual(result.state.over,'win')

    def test_no_mutation_when_invalid(self):
        g=self.game('market_operator',round=0,tokens=(Token(1,1,1,1,1),))
        before=g
        with self.assertRaises(ValueError):step(g,(('flip',1),),operators=(4,))
        self.assertEqual(g,before)

if __name__=='__main__':unittest.main()

class MarketAndOpportunityCost(unittest.TestCase):
    EMPTY=tuple(() for _ in range(9))

    def test_selected_newer_storm_changes_win_from_loss_to_victory(self):
        waves=(((0,1,1),),((1,-1,1),),(),(),(),(),(),(),())
        from reference.charge_loom_v01 import State,Token
        s=State(hp=7,progress=(3,1,3),tokens=(Token(10,1,2,1,1),),next_id=11)
        endings=[]
        for choice in (0,1):
            g=Experiment.new('paid_market',state=s,waves=waves)
            g=step(g,draft=choice)
            while not g.state.over:g=step(g)
            endings.append(g.state.over)
        self.assertEqual(endings,['loss: target','win'])

    def test_paid_market_cannot_replace_a_necessary_fourth_edit(self):
        from reference.charge_loom_v01 import State,Token
        s=State(hp=1,progress=(3,2,3),tokens=(Token(1,0,0,1,1),Token(2,0,0,1,1),
             Token(3,2,0,-1,1),Token(4,2,0,-1,1)),next_id=5)
        four=(('shift',1,1),('shift',2,1),('shift',3,-1),('shift',4,-1))
        free=step(Experiment.new('market',state=s,waves=self.EMPTY),four,draft=1)
        self.assertEqual(free.state.hp,1)
        self.assertEqual(free.state.progress,(3,3,3))
        paid=Experiment.new('paid_market',state=s,waves=self.EMPTY)
        with self.assertRaises(ValueError):step(paid,four,draft=1)
        for i in range(4):
            result=step(paid,four[:i]+four[i+1:],draft=1)
            self.assertEqual(result.state.over,'loss: breach')

    def test_paid_market_first_offer_has_no_fee(self):
        g=Experiment.new('paid_market',waves=self.EMPTY)
        self.assertEqual(step(g,draft=0).state,step(g).state)

    def test_experimental_market_does_not_mutate_production_engine(self):
        from reference.charge_loom_v01 import step as shipping_step, State
        before=State()
        g=Experiment.new('market')
        step(g,draft=1)
        self.assertEqual(before,State())


class PublicInformationContract(unittest.TestCase):
    def test_market_exposes_two_offers_one_preview_only(self):
        waves=tuple((((i%3,1,1),)) for i in range(7))+((),())
        g=Experiment.new('market',waves=waves)
        self.assertEqual(tuple(ix for ix,_ in public_forecast(g)),(0,1,2))
        g=step(g,draft=1)
        self.assertEqual(tuple(ix for ix,_ in public_forecast(g)),(0,2,3))

    def test_baseline_has_same_three_card_forecast_window(self):
        waves=tuple((((i%3,1,1),)) for i in range(7))+((),())
        g=Experiment.new('open',waves=waves)
        self.assertEqual(tuple(ix for ix,_ in public_forecast(g)),(0,1,2))
        g=step(g)
        self.assertEqual(tuple(ix for ix,_ in public_forecast(g)),(1,2,3))
