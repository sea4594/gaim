"""Targeted mechanical witnesses and conservation assertions for Pass 04."""
import unittest
from reference.charge_loom_v01 import State, Token
from experiments.phase04_lab import Lab, step, options
from experiments.rules_tournament import Trial, step_trial

EMPTY=tuple(() for _ in range(9))

def game(mode, round=8, power=(0,0,0), toks=(), hp=7):
    return Lab.new(mode, state=State(round=round,hp=hp,progress=power,coolant=3,tokens=tuple(toks),next_id=1+max((t.id for t in toks), default=0)), waves=EMPTY)

class Phase04(unittest.TestCase):
    def test_reference_parity_empty_edits(self):
        for seed in (0,3,8,12,17):
            a=Lab.new('baseline',seed)
            b=Lab.new('split',seed)
            c=Lab.new('flip',seed)
            for _ in range(9):
                if a.trial.state.over: break
                a=step(a)
                b=step(b)
                c=step(c)
                self.assertEqual(a.trial.state,b.trial.state)
                self.assertEqual(a.trial.state,c.trial.state)

    def test_bridge_parity_without_experimental_action(self):
        for seed in (1,3,8):
            a=Lab.new('bridge',seed)
            b=Lab.new('bridge_split',seed)
            c=Lab.new('bridge_flip',seed)
            for _ in range(9):
                if a.trial.state.over: break
                a=step(a)
                b=step(b)
                c=step(c)
                self.assertEqual(a.trial.state,b.trial.state)
                self.assertEqual(a.trial.state,c.trial.state)

    def test_split_turns_loss_into_win_by_distributing_matching(self):
        p=(Token(1,0,0,1,2),Token(2,0,0,-1,1),Token(3,1,0,-1,1))
        origin=game('baseline',power=(2,1,3),toks=p)
        split=game('split',power=(2,1,3),toks=p)
        self.assertNotEqual(step(origin).trial.state.over,'win')
        state=step(split,[('split',1,1)]).trial.state
        self.assertEqual(state.over,'win')
        self.assertEqual(state.progress,(3,2,3))
        self.assertEqual(state.hp,7)
        self.assertEqual(sum(t.size for t in p),4)

    def test_split_preserves_charge_and_limits_followup_hold(self):
        p=(Token(4,0,1,1,3),)
        result=step(game('split',round=6,toks=p),[('split',4,1)])
        self.assertEqual(sorted(t.size for t in result.trial.state.tokens),[1,2])
        self.assertEqual([t.held for t in result.trial.state.tokens if t.id!=4],[1])
        self.assertEqual(sum(t.size for t in result.trial.state.tokens),3)

    def test_flip_can_win_but_consumes_preexisting_power(self):
        p=(Token(1,0,0,1,2),Token(2,0,0,1,2))
        yes=step(game('flip',power=(1,3,3),toks=p),[('flip',1)])
        self.assertEqual(yes.trial.state.progress,(2,3,3))
        self.assertEqual(yes.trial.state.over,'win')
        self.assertEqual(step(game('baseline',power=(1,3,3),toks=p)).trial.state.over,'loss: target')
        with self.assertRaises(ValueError):
            step(game('flip',power=(0,3,3),toks=p),[('flip',1)])

    def test_transfer_uses_wasted_capacity_not_free_energy(self):
        p=(Token(1,1,0,1,2),Token(2,1,0,-1,2))
        initial=game('transfer',power=(3,3,1),toks=p)
        self.assertEqual(step(initial).trial.state.over,'loss: target')
        out=step(initial,[('transfer',1,2)]).trial.state
        self.assertEqual(out.progress,(3,3,2))
        self.assertEqual(out.over,'win')
        with self.assertRaises(ValueError):
            step(game('transfer',power=(0,3,1)),[('transfer',0,1)])

    def test_reactor_rewards_large_future_collision_not_small(self):
        strength_two=(Token(1,1,1,1,2),Token(2,1,1,-1,2))
        base=game('resonator',round=6,power=(3,2,0),toks=strength_two)
        purchased=step(base,[('resonator',1,2)])
        self.assertEqual(purchased.trial.state.progress,(3,1,0))
        activated=step(purchased)
        self.assertEqual(activated.trial.state.progress,(3,3,2))
        result=step(activated)
        self.assertEqual(result.trial.state.over,'win')
        small=(Token(1,1,1,1,1),Token(2,1,1,-1,1))
        p=step(game('resonator',round=6,power=(3,2,0),toks=small),[('resonator',1,2)])
        p=step(p)
        self.assertEqual(p.trial.state.progress[2],0)

    def test_reactor_purchase_can_hurt(self):
        start=game('resonator',round=6,power=(3,2,3))
        unchanged=step(step(step(start)))
        paid=step(step(step(start,[('resonator',1,2)])))
        self.assertEqual(unchanged.trial.state.over,'win')
        self.assertNotEqual(paid.trial.state.over,'win')

    def test_illegal_actions_rejected(self):
        p=(Token(1,1,0,1,2),)
        for mode,acts in [('split',[('split',1,1),('hold',1)]),
                          ('flip',[('flip',1),('shift',1,1)]),
                          ('bridge_split',[('split',1,1),('split',1,-1)]),
                          ('baseline',[('flip',1)])]:
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):step(game(mode,power=(2,2,2),toks=p),acts)

    def test_no_more_than_four_actions(self):
        with self.assertRaises(ValueError):step(game('split'),[('pass',)]*5)

if __name__=='__main__': unittest.main()

class IntegrationProbes(unittest.TestCase):
    def test_real_winning_reference_witnesses_remain_unchanged(self):
        import json
        from pathlib import Path
        from reference.charge_loom_v01 import start as ref_start, step as ref_step
        data=json.loads((Path(__file__).resolve().parents[1]/'reference/verified-scenario-bank.json').read_text())
        for witness in data['witnesses']:
            seed=witness['seed']
            base=ref_start(seed)
            unchanged=Lab.new('baseline',seed)
            split=Lab.new('bridge_split',seed)
            for record in witness['winning_trace']:
                actions=record['actions']
                base=ref_step(base,actions)
                unchanged=step(unchanged,actions)
                split=step(split,actions)
                self.assertEqual(base,unchanged.trial.state)
                self.assertEqual(base,split.trial.state)
            self.assertEqual(base.over,'win')

    def test_bridge_split_witness_has_two_and_only_two_winning_plans_in_fixture(self):
        from experiments.phase04_survey import plans
        p=(Token(1,0,1,1,2),Token(2,0,1,-1,1),Token(3,1,1,-1,1),
           Token(4,1,2,1,1),Token(5,1,2,-1,1))
        initial=State(round=6,hp=7,progress=(2,2,0),coolant=3,tokens=p,next_id=6)
        results={}
        for mode in ('bridge','bridge_split'):
            before=Lab.new(mode,state=initial,waves=EMPTY)
            bought=step(before,[('bridge',1,2)])
            wins=[]
            for edits in plans(bought):
                try: final=step(step(bought,edits)).trial.state
                except ValueError:continue
                if final.over=='win':wins.append(edits)
            results[mode]=wins
        self.assertEqual(len(results['bridge']),0)
        self.assertEqual(len(results['bridge_split']),2)
        self.assertIn((('split',1,1),),results['bridge_split'])

    def test_split_can_turn_unmodified_win_into_hull_death(self):
        tokens=(Token(1,0,0,1,2),Token(2,0,0,-1,2))
        fixture=game('split',power=(2,3,3),toks=tokens,hp=1)
        self.assertEqual(step(fixture).trial.state.over,'win')
        self.assertEqual(step(fixture,[('split',1,1)]).trial.state.over,'loss: breach')

class CompetingInvestments(unittest.TestCase):
    def test_bridge_and_flip_needed_in_two_round_sequence(self):
        tokens=(Token(1,1,1,1,2),Token(2,1,1,1,2),Token(3,1,2,1,1),Token(4,1,2,-1,1))
        s=State(round=6,hp=7,progress=(3,2,0),tokens=tokens,next_id=5)
        scenarios={'bridge_flip':([('bridge',1,2)],[('flip',1)]),
                   'bridge':([('bridge',1,2)],[]),
                   'flip':([],[('flip',1)])}
        endings={}
        for mode,(r7,r8) in scenarios.items():
            g=Lab.new(mode,state=s,waves=EMPTY)
            for a in (r7,r8,[]):g=step(g,a)
            endings[mode]=g.trial.state.over
        self.assertEqual(endings['bridge_flip'],'win')
        self.assertEqual(endings['bridge'],'loss: target')
        self.assertEqual(endings['flip'],'loss: target')

    def test_flip_not_always_worth_purchasing(self):
        tokens=(Token(1,0,0,1,2),Token(2,0,0,-1,2))
        case=game('flip',power=(2,3,3),toks=tokens,hp=1)
        self.assertEqual(step(case).trial.state.over,'win')
        self.assertEqual(step(case,[('flip',1)]).trial.state.over,'loss: breach')
