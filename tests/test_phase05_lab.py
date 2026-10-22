"""Regression and exact targeted witnesses for research rules, not shipping rules."""
import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State,Token
from experiments.phase05_lab import Design,step,options,offers
from experiments.phase04_lab import Lab,step as baseline_step

EMPTY=tuple(() for _ in range(9))

class Phase05Mechanics(unittest.TestCase):
    def game(self,mode='control',round=8,power=(0,0,0),tokens=(),hp=7,mission='standard'):
        return Design.new(mode,state=State(round=round,hp=hp,progress=power,tokens=tokens,
                       next_id=max((t.id for t in tokens),default=0)+1),waves=EMPTY,mission=mission)

    def test_unmodified_phase04_parity(self):
        for seed in range(15):
            a=Design.new('control',seed=seed);b=Lab.new('bridge_flip',seed)
            while not a.state.over:
                a=step(a);b=baseline_step(b)
                self.assertEqual(a.state,b.trial.state)

    def test_draft_oldest_choice_preserves_original_wave_order(self):
        for seed in range(10):
            a=Design.new('control',seed=seed)
            b=Design.new('draft',seed=seed)
            while not a.state.over:
                a=step(a);b=step(b,[('draft',0)] if len(b.available)>1 and b.state.round<7 else [])
                self.assertEqual(a.state,b.state)

    def test_draft_changes_arrival_order_but_not_multiset(self):
        waves=(( (0,1,1),),((1,-1,2),),((2,1,1),),(),(),(),(),(),())
        base=Design.new('draft',waves=waves)
        self.assertEqual(len(offers(base)),2)
        old=step(base,[('draft',0)])
        new=step(base,[('draft',1)])
        self.assertEqual(old.state.tokens[0].lane,0)
        self.assertEqual(new.state.tokens[0].lane,1)
        self.assertEqual(old.available,(1,2))
        self.assertEqual(new.available,(0,2))
        self.assertEqual(sorted(i for i in old.available if i<2),[1])
        self.assertEqual(sorted(i for i in new.available if i<2),[0])

    def test_draft_conserves_all_seven_storm_cards(self):
        waves=tuple((((i%3,(-1)**i,1),)) for i in range(7))+((),())
        g=Design.new('draft',waves=waves)
        selected=[]
        for i in range(7):
            ix=1 if i%2==0 and len(g.available)>1 else 0
            selected.append(g.available[ix])
            g=step(g,[('draft',ix)])
        self.assertEqual(set(selected),set(range(7)))
        self.assertEqual(len(selected),len(set(selected)))

    def test_draft_rejects_extra_and_invalid_choices(self):
        g=Design.new('draft')
        for commands in ([('draft',0),('draft',1)],[('draft',2)],[('draft',True)]):
            with self.assertRaises(ValueError):step(g,commands)
        with self.assertRaises(ValueError):step(Design.new('control'),[('draft',0)])

    def test_accelerate_can_turn_hull_death_into_win(self):
        toks=(Token(1,1,1,1,1),Token(2,1,0,-1,1))
        base=self.game('control',power=(3,2,3),tokens=toks,hp=1)
        improved=self.game('accelerate',power=(3,2,3),tokens=toks,hp=1)
        self.assertEqual(step(base).state.over,'loss: breach')
        end=step(improved,[('accelerate',1)]).state
        self.assertEqual(end.progress,(3,3,3))
        self.assertEqual(end.hp,1)
        self.assertEqual(end.over,'win')

    def test_accelerate_can_be_fatal(self):
        toks=(Token(1,1,1,1,2),Token(2,1,0,-1,2))
        g=self.game('accelerate',power=(3,3,3),tokens=toks,hp=1)
        # Without accelerate, the NOW negative charge already kills; with
        # accelerate both cancel -- this is beneficial, not proof of fatality.
        self.assertEqual(step(g,[('accelerate',1)]).state.over,'win')
        h=self.game('accelerate',power=(3,3,3),tokens=(Token(1,1,1,1,2),),hp=2)
        # The arriving future threat could instead be held out of the finale
        # only if this were not the deadline, so test one earlier turn.
        h=self.game('accelerate',round=7,power=(3,3,3),tokens=(Token(1,1,1,1,2),),hp=2)
        self.assertEqual(step(h).state.hp,2)
        self.assertLess(step(h,[('accelerate',1)]).state.hp,2)

    def test_accelerate_validation_and_one_edit_per_token(self):
        g=self.game('accelerate',tokens=(Token(1,0,0,1,1),Token(2,1,1,1,1)))
        for a in ([('accelerate',1)], [('accelerate',2),('flip',2)], [('accelerate',2),('hold',2)], [('accelerate',2),('accelerate',2)]):
            with self.assertRaises(ValueError):step(g,a)
        with self.assertRaises(ValueError):step(self.game('control',tokens=(Token(2,1,1,1,1),)),[('accelerate',2)])

    def test_missions_have_distinct_terminal_conditions(self):
        state=State(round=8,hp=5,progress=(2,2,3))
        for mission,winner in [('standard',False),('shield',True),('choreography',False),('voltage',False)]:
            with self.subTest(mission=mission):
                g=Design.new('mission',state=state,waves=EMPTY,mission=mission)
                self.assertEqual(step(g).state.over=='win',winner)

    def test_choreography_requires_two_lanes_same_turn(self):
        toks=(Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,2,0,1,1),Token(4,2,0,-1,1))
        s=State(round=8,hp=7,progress=(1,2,1),tokens=toks,next_id=5)
        a=Design.new('mission',state=s,waves=EMPTY,mission='choreography')
        x=step(a)
        self.assertEqual(x.synchronized,1)
        self.assertEqual(x.state.progress,(2,2,2))
        self.assertNotEqual(x.state.over,'win') # 6 total, requires 7
        s=replace(s,progress=(1,3,1))
        y=step(Design.new('mission',state=s,waves=EMPTY,mission='choreography'))
        self.assertEqual(y.state.over,'win')

    def test_voltage_uses_distinct_lanes(self):
        toks=(Token(1,0,0,1,2),Token(2,0,0,-1,2),Token(3,2,0,1,2),Token(4,2,0,-1,2))
        s=State(round=8,hp=7,progress=(0,3,0),tokens=toks,next_id=5)
        y=step(Design.new('mission',state=s,waves=EMPTY,mission='voltage'))
        self.assertEqual(y.large,0b101)
        self.assertEqual(y.state.over,'win')

    def test_heat_high_output_tradeoff(self):
        toks=(Token(1,0,0,1,2),Token(2,0,0,-1,2))
        g=self.game('heat',round=7,power=(3,3,3),tokens=toks,hp=2)
        # Existing heat from one previous reactor overload.
        g=replace(g,heat=1)
        y=step(g)
        self.assertEqual(y.state.hp,0)
        self.assertEqual(y.heat,0)
        self.assertEqual(y.state.over,'loss: breach')
        ok=step(self.game('control',round=7,power=(3,3,3),tokens=toks,hp=2))
        self.assertEqual(ok.state.hp,2)

    def test_four_edits_and_validation(self):
        x=Design.new('draft_accelerate',state=State(tokens=(Token(1,1,1,1,1),),next_id=2),waves=EMPTY)
        with self.assertRaises(ValueError):step(x,[('pass',)]*5)
        with self.assertRaises(ValueError):step(x,[('accelerate',999)])

if __name__=='__main__':unittest.main()

class StructuralWitnesses(unittest.TestCase):
    def test_storm_draft_changes_win_without_free_resource_creation(self):
        # Existing +1 is in FAR, and two visible waves are [-1 match] / [+1 elsewhere].
        # Bringing [-1 match] NOW aligns its breach with the existing charge.
        waves=(((1,-1,1),),((0,1,1),),(),(),(),(),(),(),())
        base=State(round=0,hp=7,progress=(3,1,3),tokens=(Token(10,1,2,1,1),),next_id=11)
        results={}
        for first in (0,1):
            g=Design.new('draft',state=base,waves=waves)
            g=step(g,[('draft',first)])
            while not g.state.over:g=step(g)
            results[first]=g.state
        self.assertEqual(results[0].over,'win')
        self.assertEqual(results[1].over,'loss: target')
        self.assertEqual(results[0].progress,(3,2,3))
        self.assertEqual(results[1].progress,(3,1,3))

    def test_accelerate_early_can_destroy_later_match(self):
        toks=(Token(1,1,1,1,2),Token(2,1,1,-1,2))
        s=State(round=6,hp=3,progress=(3,3,3),tokens=toks,next_id=3)
        a=Design.new('accelerate',state=s,waves=EMPTY)
        # Wait, then matched charges breach together in round 8.
        safe=step(a)
        safe=step(safe)
        self.assertEqual(safe.state.hp,3)
        while not safe.state.over:safe=step(safe)
        self.assertEqual(safe.state.over,'win')
        # Early +2 causes 2 hull this turn and -2 leakage the next.
        rushed=step(a,[('accelerate',1)])
        rushed=step(rushed)
        self.assertEqual(rushed.state.over,'loss: breach')

    def test_pruned_variants_reject_excluded_actions(self):
        for variant,command in (
            ('accelerate_no_hold',('hold',1)),
            ('accelerate_no_damp',('damp',1)),
            ('accelerate_no_flip',('flip',1)),
        ):
            s=State(round=6,progress=(2,2,2),tokens=(Token(1,1,1,1,1),),next_id=2)
            g=Design.new(variant,state=s,waves=EMPTY)
            self.assertNotIn(command,options(g))
            with self.assertRaises(ValueError):step(g,[command])
