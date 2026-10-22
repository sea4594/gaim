"""Mechanics tournament tests. Reference v0.1 and online code remain canonical."""
import json
import unittest
from pathlib import Path
from reference.charge_loom_v01 import State, Token, step, start
from experiments.rules_tournament import Trial, Bridge, MODES, step_trial, planning_tokens, actions
from experiments.commitment_survey import survey as commitment_survey
from experiments.tournament_survey import final_survey, greedy_survey

ZERO_WAVES = tuple(() for _ in range(9))


class TournamentTests(unittest.TestCase):
    def test_no_special_edit_matches_all_seven_golden_scenarios(self):
        bank = json.loads((Path(__file__).resolve().parents[1] / 'reference/verified-scenario-bank.json').read_text())
        for mode in ('baseline', 'bridge', 'sweep', 'overcharge', 'contract', 'front', 'bridge_sweep'):
            for case in bank['witnesses']:
                ref = start(case['seed'])
                trial = Trial.new(mode, case['seed'])
                for turn in case['winning_trace']:
                    a = [tuple(x) for x in turn['actions']]
                    ref = step(ref, a)
                    trial = step_trial(trial, a)
                    self.assertEqual(trial.state, ref, (mode, case['seed'], turn['round']))
                self.assertEqual(trial.state.over, 'win')

    def test_parity_for_replayable_unedited_seeds(self):
        for seed in range(20):
            ref, trial = start(seed), Trial.new('baseline', seed)
            while not ref.over:
                ref = step(ref)
                trial = step_trial(trial)
                self.assertEqual(ref, trial.state)

    def test_delayed_bridge_is_a_real_two_round_investment(self):
        s = State(round=6, hp=4, progress=(3,2,0), coolant=3,
                  tokens=(Token(1,1,1,1,1), Token(2,1,1,-1,1),
                          Token(3,1,2,1,1), Token(4,1,2,-1,1)), next_id=5)
        g = Trial(s,'bridge',waves=ZERO_WAVES)
        purchased = step_trial(g,[('bridge',1,2)])
        self.assertEqual(purchased.state.progress,(3,1,0))
        self.assertEqual(purchased.bridge, Bridge(1,2,8,9))
        next_round = step_trial(purchased)
        self.assertEqual(next_round.state.progress,(3,2,1))
        final = step_trial(next_round)
        self.assertEqual(final.state.progress,(3,3,2))
        self.assertEqual(final.state.over,'win')
        without = step_trial(step_trial(step_trial(g)))
        self.assertEqual(without.state.over,'loss: target')
        self.assertEqual(without.state.progress,(3,3,0))

    def test_bridge_and_later_shift_are_complementary_actions(self):
        # Simulates an Engineer buying an investment, then a Router aligning a
        # different token a turn later. This is synergy, NOT proof of social co-op.
        s=State(round=6,hp=5,progress=(3,2,0),coolant=3,
                tokens=(Token(1,0,1,1,1),Token(2,1,1,-1,1),
                        Token(3,1,2,1,1),Token(4,1,2,-1,1)),next_id=5)
        g=Trial(s,'bridge',waves=ZERO_WAVES)
        # Build r7, align r8, then two consecutive matches feed RIGHT.
        g=step_trial(g,[('bridge',1,2)])
        g=step_trial(g,[('shift',1,1)])
        g=step_trial(g)
        self.assertEqual(g.state.over,'win')
        self.assertEqual(g.state.progress,(3,3,2))
        missing_bridge=step_trial(step_trial(step_trial(Trial(s,'bridge',waves=ZERO_WAVES)),[('shift',1,1)]))
        self.assertEqual(missing_bridge.state.over,'loss: target')
        missing_shift=step_trial(step_trial(step_trial(Trial(s,'bridge',waves=ZERO_WAVES),[('bridge',1,2)])))
        self.assertNotEqual(missing_shift.state.over,'win')

    def test_bridge_can_lose_a_winning_state(self):
        s=State(round=6,hp=4,progress=(2,3,3),next_id=1)
        g=Trial(s,'bridge',waves=ZERO_WAVES)
        self.assertEqual(step_trial(step_trial(step_trial(g))).state.over,'win')
        bad=step_trial(step_trial(step_trial(g,[('bridge',0,1)])))
        self.assertEqual(bad.state.progress,(1,3,3))
        self.assertEqual(bad.state.over,'loss: target')

    def test_other_mechanics_are_real_rules_not_descriptions(self):
        s=State(round=8,hp=4,progress=(1,1,1),coolant=2,
                tokens=(Token(1,0,0,1,1),Token(2,0,0,-1,1)),next_id=3)
        swept=step_trial(Trial(s,'sweep',waves=ZERO_WAVES),[('sweep',0,1)])
        self.assertEqual(swept.state.coolant,1)
        self.assertNotEqual(swept.state.progress,step_trial(Trial(s,'baseline',waves=ZERO_WAVES)).state.progress)
        harmonic=step_trial(Trial(s,'harmonic',waves=ZERO_WAVES))
        baseline=step_trial(Trial(s,'baseline',waves=ZERO_WAVES))
        # The harmonic bonus is only applied when matches span 2+ lanes.
        self.assertEqual(harmonic.state.progress,baseline.state.progress)
        sn=State(round=8,hp=5,progress=(1,1,1),coolant=3,
                 tokens=(Token(1,0,0,1,1),Token(2,0,0,-1,1),Token(3,2,0,1,1),Token(4,2,0,-1,1)),next_id=5)
        self.assertEqual(step_trial(Trial(sn,'harmonic',waves=ZERO_WAVES)).state.progress,(3,1,3))
        self.assertEqual(step_trial(Trial(sn,'baseline',waves=ZERO_WAVES)).state.progress,(2,1,2))
        pledge=Trial(State(round=6,hp=3,progress=(1,1,1)), 'contract', waves=ZERO_WAVES)
        after=step_trial(pledge,[('contract',0,1)])
        missed=step_trial(after)
        self.assertEqual(missed.state.hp,2)
        self.assertIsNone(missed.pledge)

    def test_front_changes_next_wave_and_then_resets(self):
        waves=[() for _ in range(9)]
        waves[6] = ((0,1,2),(2,-1,1))
        g = Trial(State(round=5,next_id=1,progress=(0,0,0)), 'front', waves=tuple(waves))
        selected=step_trial(g,[('front',1)])
        self.assertEqual(selected.front,1)
        spawned=planning_tokens(selected)
        self.assertEqual([t.lane for t in spawned],[1,0])
        after=step_trial(selected)
        self.assertEqual(after.front,0)
        self.assertEqual([t.lane for t in after.state.tokens],[1,0])

    def test_no_forecast_clairvoyance_in_delayed_bridge(self):
        # A purchase on round r pays off in r+1/r+2; a wave newly spawned in
        # those rounds enters row 2 and cannot breach until r+3 or later.
        s=State(round=6,hp=7,progress=(3,2,0))
        waves=[() for _ in range(9)]
        waves[7]=((1,1,1),(1,-1,1))
        t=Trial(s,'bridge',waves=tuple(waves))
        t=step_trial(t,[('bridge',1,2)])
        t=step_trial(t)
        self.assertEqual(t.state.progress,(3,1,0))
        t=step_trial(t)
        self.assertEqual(t.state.progress,(3,1,0))

    def test_rejects_invalid_actions_and_not_enough_resources(self):
        s=State(round=6,progress=(0,0,0),coolant=0)
        g=Trial(s,'bridge',waves=ZERO_WAVES)
        with self.assertRaises(ValueError):step_trial(g,[('bridge',0,1)])
        with self.assertRaises(ValueError):step_trial(g,[('contract',0,1)])
        with self.assertRaises(ValueError):step_trial(g,[('shift',777,1)])
        with self.assertRaises(ValueError):step_trial(g,[('pass',)]*5)
        q=Trial(State(round=8,progress=(1,1,1)), 'bridge', waves=ZERO_WAVES)
        with self.assertRaises(ValueError):step_trial(q,[('bridge',1,2)])
        x=Trial(State(round=7,progress=(1,1,1)), 'bridge', waves=ZERO_WAVES)
        with self.assertRaises(ValueError):step_trial(x,[('bridge',1,2),('bridge',1,0)])

    def test_hybrid_can_operate_and_cannot_double_buy_or_double_special(self):
        s=State(round=6,hp=7,progress=(1,1,1),coolant=1,
                tokens=(Token(1,0,0,1,1),Token(2,0,0,-1,1)),next_id=3)
        g=Trial(s,'bridge_sweep',waves=ZERO_WAVES)
        bought=step_trial(g,[('bridge',0,1)])
        self.assertEqual(bought.bridge,Bridge(0,1,8,9))
        self.assertEqual(bought.state.progress[0],1)  # purchase and source collision cancel
        with self.assertRaises(ValueError):
            step_trial(g,[('bridge',0,1),('sweep',0,1)])
        shifted=step_trial(Trial(s,'bridge_sweep',waves=ZERO_WAVES),[('sweep',0,1)])
        self.assertEqual(shifted.state.coolant,0)

    def test_commitment_counts_reproducible_with_both_outcomes(self):
        result=commitment_survey()
        self.assertEqual(result['cases_per_variant'],576)
        self.assertEqual((result['results']['bridge']['good'],result['results']['bridge']['bad']),(44,24))
        self.assertEqual((result['results']['contract']['good'],result['results']['contract'].get('bad',0)),(88,0))

    def test_small_tournament_is_repeatable(self):
        result=final_survey(60)
        self.assertEqual(result['results']['baseline']['winnable'],10)
        self.assertEqual(result['results']['sweep']['winnable'],11)
        self.assertEqual(result['results']['overcharge']['winnable'],10)
        self.assertEqual(result['results']['harmonic']['winnable'],10)
        self.assertEqual(greedy_survey(12)['results']['baseline']['wins'],4)

if __name__=='__main__': unittest.main()
