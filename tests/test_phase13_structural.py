"""Exact deterministic counterfactuals; not claims about fun or multiplayer."""
import unittest
from dataclasses import replace
from reference.charge_loom_v01 import State, Token
from experiments.phase13_structural import Structural, step, shunt_choices, _breach_balance

EMPTY = ((),) * 9


def trial(mode, state):
    return Structural.new(mode, state=state, waves=EMPTY)


class StructuralTests(unittest.TestCase):
    def test_unmodified_research_control(self):
        state = State(round=7, hp=5, tokens=(Token(1, 0, 0, 1, 2),), next_id=2)
        g = trial('control', state)
        s = step(g).state
        self.assertEqual(s.hp, 3)
        self.assertEqual(s.tokens, ())
        self.assertEqual(state.hp, 5)

    def test_rebound_creation_from_large_leak(self):
        state = State(round=6, hp=7, tokens=(Token(1, 1, 0, 1, 3),), next_id=2)
        after = step(trial('echo_breach', state))
        self.assertEqual(after.echoes, 1)
        self.assertEqual(after.state.hp, 4)
        self.assertEqual(after.state.tokens, (Token(2, 1, 1, -1, 1, 1),))
        self.assertEqual(after.state.next_id, 3)

    def test_small_leak_no_echo(self):
        state = State(round=6, hp=7, tokens=(Token(1, 1, 0, 1, 1),), next_id=2)
        after = step(trial('echo_breach', state))
        self.assertEqual(after.echoes, 0)
        self.assertEqual(after.state.tokens, ())

    def test_echo_lasts_and_can_be_repositioned(self):
        state = State(round=6, hp=7, tokens=(Token(1, 1, 0, 1, 2),), next_id=2)
        out = step(trial('echo_breach', state))
        self.assertEqual(out.state.tokens[0].row, 1)
        self.assertEqual(out.state.tokens[0].held, 1)
        changed = step(out, actions=(('shift', 2, 1),))
        self.assertEqual(changed.state.tokens[0].lane, 2)
        self.assertEqual(changed.state.tokens[0].row, 0)
        final = step(changed)
        self.assertEqual(final.state.hp, 4)  # initial 2 + returning 1

    def test_echo_cannot_be_held_again(self):
        state = State(round=6, hp=7, tokens=(Token(1, 1, 0, 1, 2),), next_id=2)
        after = step(trial('echo_breach', state))
        with self.assertRaises(ValueError): step(after, actions=(('hold', 2),))

    def test_shunt_requires_opposing_real_match(self):
        state = State(round=7, hp=7, progress=(2, 2, 2), tokens=(Token(1, 0, 0, 1, 2),), next_id=2)
        with self.assertRaises(ValueError): step(trial('shunt', state), shunt_lane=0)

    def test_shunt_cannot_claim_free_power_when_no_leak(self):
        state = State(round=7, hp=7, progress=(2, 2, 2), tokens=(Token(1,0,0,1,1),Token(2,0,0,-1,1)), next_id=3)
        self.assertFalse(shunt_choices(trial('shunt', state)))
        with self.assertRaises(ValueError): step(trial('shunt', state), shunt_lane=0)

    def test_shunt_rescues_same_turn_hull_but_costs_energy(self):
        s = State(round=7,hp=2,progress=(3,3,2),tokens=(Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,1,0,1,2)),next_id=4)
        baseline = step(trial('control',s))
        self.assertEqual(baseline.state.over,'loss: breach')
        shunt = step(trial('shunt',s), shunt_lane=0)
        self.assertEqual(shunt.state.hp,2)
        self.assertEqual(shunt.state.progress,(2,3,2))
        self.assertEqual(shunt.shielded,2)
        self.assertEqual(shunt.spent,1)

    def test_shunt_enables_two_turn_win(self):
        s = State(round=7,hp=2,progress=(3,3,2),tokens=(
            Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,1,0,1,2),
            Token(4,0,1,1,1),Token(5,0,1,-1,1)),next_id=6)
        old = step(trial('control',s))
        self.assertEqual(old.state.over,'loss: breach')
        got = step(trial('shunt',s), shunt_lane=0)
        self.assertEqual(got.state.over, '')
        got = step(got)
        self.assertEqual(got.state.over, 'win')
        self.assertEqual(got.state.progress, (3,3,2))

    def test_shunt_can_destroy_safe_win(self):
        s = State(round=8,hp=7,progress=(2,3,2),tokens=(
            Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,1,0,1,1)),next_id=4)
        baseline = step(trial('control',s))
        shunt = step(trial('shunt',s), shunt_lane=0)
        self.assertEqual(baseline.state.over,'win')
        self.assertEqual(shunt.state.over,'loss: target')

    def test_shunt_does_not_block_deadline_liability(self):
        s = State(round=8,hp=5,progress=(3,3,2),tokens=(
            Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,1,2,1,3),
            Token(4,2,0,-1,1)),next_id=5)
        shunt=step(trial('shunt',s),shunt_lane=0)
        self.assertEqual(shunt.state.hp,2)  # 1 ordinary + 3 late - 1 shield
        self.assertEqual(shunt.state.over,'loss: target')

    def test_invalid_source_and_mode(self):
        s = State(round=7,hp=7)
        with self.assertRaises(ValueError):Structural.new('fantasy', state=s)
        with self.assertRaises(ValueError):step(trial('control',s),shunt_lane=0)
        with self.assertRaises(ValueError):step(trial('shunt',s),shunt_lane=True)

    def test_no_mutation_and_replay(self):
        s=State(round=7,hp=7, tokens=(Token(1,1,0,1,2),), next_id=2)
        g=trial('echo_breach',s)
        a=step(g)
        b=step(g)
        self.assertEqual(a,b)
        self.assertEqual(g.state,s)


if __name__=='__main__': unittest.main()

class EchoDecisions(unittest.TestCase):
    def test_returning_charge_can_convert_loss_to_win(self):
        s=State(round=6,hp=5,progress=(2,3,2),tokens=(
            Token(1,0,0,1,2),Token(2,0,2,1,1)),next_id=3)
        outcomes={}
        for mode in ('control','echo_breach'):
            g=trial(mode,s)
            for _ in range(3):g=step(g)
            outcomes[mode]=g.state.over
        self.assertEqual(outcomes['control'],'loss: target')
        self.assertEqual(outcomes['echo_breach'],'win')

    def test_returning_charge_can_worsen_outcome(self):
        s=State(round=6,hp=5,progress=(3,3,2),tokens=(Token(1,0,0,1,2),),next_id=2)
        got={}
        for mode in ('control','echo_breach'):
            g=trial(mode,s)
            for _ in range(3):g=step(g)
            got[mode]=g.state.hp
        self.assertEqual(got['control'],3)
        self.assertEqual(got['echo_breach'],2)

class MarketCompatibility(unittest.TestCase):
    def test_market_draft_replays_identically_in_control(self):
        from experiments.phase06_lab import Experiment, step as forecast
        for seed in range(15):
            base=Experiment.new('market',seed=seed)
            trial=Structural(base, 'control')
            for choice in (1,0,1):
                if base.state.over:break
                base=forecast(base,draft=choice)
                trial=step(trial,draft=choice)
                self.assertEqual(base.state,trial.state)
                self.assertEqual(base.game.available,trial.exp.game.available)

    def test_seeded_storms_do_not_change_core_rule_results(self):
        from experiments.phase06_lab import Experiment, step as forecast
        for seed in range(15):
            control=Structural.new('control',seed=seed)
            reference=Experiment.new('market',seed=seed)
            for _ in range(4):
                if reference.state.over:break
                reference=forecast(reference)
                control=step(control)
                self.assertEqual(reference.state,control.state)
