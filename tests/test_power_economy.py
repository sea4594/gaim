"""Game-design laboratory tests. Never modify production v0.1 parity fixtures."""
import json
import unittest
from pathlib import Path
from random import Random

from experiments.power_economy import (
    benchmark, choose_greedy, options, planning_tokens, step_experimental,
)
from reference.charge_loom_v01 import State, Token, step

ROOT = Path(__file__).resolve().parents[1]


def endgame(*, hull, power, tokens):
    return State(round=8, hp=hull, progress=power, coolant=3,
                 tokens=tuple(tokens), next_id=1 + len(tokens), seed=0)


class PowerEconomyExperiments(unittest.TestCase):
    def test_no_power_activation_is_exactly_baseline_on_all_seven_winning_scripts(self):
        bank = json.loads((ROOT / 'reference/verified-scenario-bank.json').read_text())
        for witness in bank['witnesses']:
            base = State(seed=witness['seed'])
            modes = {'barrier': base, 'relay': base}
            for record in witness['winning_trace']:
                edits = [tuple(e) for e in record['actions']]
                base = step(base, edits)
                for mode in modes:
                    modes[mode] = step_experimental(modes[mode], edits, mode=mode)
                    self.assertEqual(base, modes[mode], (witness['seed'], mode, record['round']))
            self.assertEqual(base.over, 'win')

    def test_no_power_activation_exactly_baseline_under_random_legal_edits(self):
        rng = Random(119)
        for seed in range(20):
            ref = State(seed=seed)
            other = {'barrier': ref, 'relay': ref}
            while not ref.over:
                actions = []
                used = set()
                damps = 0
                for a in rng.sample(options(ref, 'baseline'), k=min(4, len(options(ref, 'baseline')))):
                    if a[1] not in used and rng.random() < 0.55:
                        if a[0] == 'damp' and damps >= ref.coolant:
                            continue
                        actions.append(a)
                        used.add(a[1])
                        damps += a[0] == 'damp'
                ref = step(ref, actions)
                for mode in other:
                    other[mode] = step_experimental(other[mode], actions, mode=mode)
                    self.assertEqual(ref, other[mode])

    def test_barrier_spending_is_necessary_for_one_win(self):
        s = endgame(hull=1, power=(3, 3, 2), tokens=(
            Token(1, 0, 0, 1, 1), Token(2, 0, 0, -1, 1), Token(3, 0, 0, -1, 2),
        ))
        self.assertEqual(step_experimental(s, (), mode='barrier').over, 'loss: breach')
        protected = step_experimental(s, (('barrier', 0),), mode='barrier')
        self.assertEqual(protected.over, 'win')
        self.assertEqual(protected.progress, (3, 3, 2))
        self.assertEqual(protected.hp, 1)

    def test_barrier_spending_can_turn_win_into_loss(self):
        s = endgame(hull=5, power=(2, 3, 2), tokens=(
            Token(1, 2, 0, 1, 1), Token(2, 2, 0, -1, 1),
        ))
        self.assertEqual(step_experimental(s, (), mode='barrier').over, 'win')
        paid = step_experimental(s, (('barrier', 1),), mode='barrier')
        self.assertEqual(paid.over, 'loss: target')
        self.assertEqual(paid.hp, 5)

    def test_relay_spending_can_be_necessary_to_win(self):
        s = endgame(hull=2, power=(3, 3, 2), tokens=(
            Token(1, 0, 0, 1, 1), Token(2, 2, 0, -1, 1),
        ))
        self.assertEqual(step_experimental(s, (), mode='relay').over, 'loss: breach')
        self.assertEqual(step_experimental(s, (('shift', 1, 1),), mode='relay').over, 'loss: breach')
        redirected = step_experimental(s, (('relay', 1),), mode='relay')
        self.assertEqual(redirected.over, 'win')
        self.assertEqual(redirected.progress, (2, 3, 3))

    def test_relay_spending_can_turn_win_into_loss(self):
        s = endgame(hull=6, power=(3, 3, 2), tokens=(
            Token(1, 0, 2, 1, 1),
        ))
        self.assertEqual(step_experimental(s, (), mode='relay').over, 'win')
        paid = step_experimental(s, (('relay', 1),), mode='relay')
        self.assertEqual(paid.over, 'loss: target')

    def test_power_must_exist_before_round_and_is_lane_local(self):
        s = endgame(hull=5, power=(0, 3, 2), tokens=(
            Token(1, 0, 0, 1, 1), Token(2, 0, 0, -1, 1),
        ))
        for mode, action in [('barrier', ('barrier', 0)), ('relay', ('relay', 1))]:
            with self.assertRaises(ValueError):
                step_experimental(s, (action,), mode=mode)
        self.assertEqual(s.progress, (0, 3, 2))

    def test_no_double_spend_invalid_ownership_or_extra_budget(self):
        s = endgame(hull=5, power=(2, 3, 2), tokens=(
            Token(1, 0, 0, 1, 1), Token(2, 2, 0, -1, 1),
        ))
        for mode, acts in [
            ('barrier', (('barrier', 0), ('barrier', 1))),
            ('relay', (('relay', 1), ('relay', 2))),
            ('relay', (('relay', 1), ('shift', 1, 1))),
            ('barrier', (('barrier', 0), ('pass',), ('pass',), ('pass',), ('pass',))),
        ]:
            with self.assertRaises(ValueError, msg=(mode, acts)):
                step_experimental(s, acts, mode=mode)
        self.assertEqual(s.progress, (2, 3, 2))

    def test_barrier_applies_to_final_leak_once_not_twice(self):
        s = endgame(hull=2, power=(3, 3, 2), tokens=(
            Token(1, 0, 2, 1, 2),
        ))
        self.assertEqual(step_experimental(s, (), mode='barrier').over, 'loss: breach')
        a = step_experimental(s, (('barrier', 0),), mode='barrier')
        self.assertEqual(a.hp, 2)
        self.assertEqual(a.over, 'loss: target')  # spending still sacrifices a victory point

    def test_benchmark_repeatable_no_nans_and_invariant_bounds(self):
        report = benchmark(range(3))
        self.assertEqual(report, benchmark(range(3)))
        for result in report.values():
            self.assertEqual(result['games'], 3)
            self.assertTrue(0 <= result['wins'] <= 3)
            self.assertGreaterEqual(result['power_activations'], 0)


if __name__ == '__main__':
    unittest.main()
