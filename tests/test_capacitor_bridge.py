"""Opt-in design trial; production golden traces must remain unmodified."""
import json
import unittest
from pathlib import Path

from experiments.capacitor_bridge import BridgeGame, Link, options, step_bridge
from reference.charge_loom_v01 import State, Token, step


class CapacitorBridgeTests(unittest.TestCase):
    def test_all_seven_winning_traces_match_production_without_link(self):
        bank = json.loads((Path(__file__).resolve().parents[1] /
                           'reference/verified-scenario-bank.json').read_text())
        for w in bank['witnesses']:
            ref = State(seed=w['seed'])
            game = BridgeGame(ref)
            for r in w['winning_trace']:
                acts = tuple(tuple(a) for a in r['actions'])
                ref = step(ref, acts)
                game = step_bridge(game, acts)
                self.assertEqual(game.state, ref)
                self.assertIsNone(game.link)
            self.assertEqual(ref.over, 'win')

    def test_bridge_can_pay_off_over_two_distinct_collisions(self):
        # Round 8: a pair breaches NOW. Round 9: a second pair breaches.
        s = State(round=7, hp=7, progress=(3, 2, 0), coolant=3,
                  tokens=(Token(1, 1, 0, 1, 1), Token(2, 1, 0, -1, 1),
                          Token(3, 1, 1, 1, 1), Token(4, 1, 1, -1, 1)), next_id=5)
        game = step_bridge(BridgeGame(s), (('link', 1, 2),))
        self.assertEqual(game.state.progress, (3, 2, 1))
        self.assertEqual(game.link, Link(1, 2, 1))
        end = step_bridge(game)
        self.assertEqual(end.state.progress, (3, 3, 2))
        self.assertEqual(end.state.over, 'win')
        self.assertIsNone(end.link)
        # Without investment, both matches go to near-full center and the right
        # lane never earns any charge: the team loses the distribution target.
        default = step(step(s), ())
        self.assertEqual(default.over, 'loss: target')
        self.assertEqual(default.progress, (3, 3, 0))

    def test_bridge_can_be_a_strategic_mistake(self):
        s = State(round=8, hp=7, progress=(2, 3, 2), coolant=3,
                  tokens=(Token(1, 2, 0, 1, 1), Token(2, 2, 0, -1, 1)), next_id=3)
        self.assertEqual(step_bridge(BridgeGame(s)).state.over, 'win')
        # Center has 3. Spend from center -> right link, but the only match
        # happens on right, so no bridge bonus and the goal fails.
        bad = step_bridge(BridgeGame(s), (('link', 1, 2),))
        self.assertEqual(bad.state.over, 'loss: target')

    def test_exactly_one_link_at_once_and_stored_power_only(self):
        s = State(round=7, hp=7, progress=(0, 1, 0), coolant=3,
                  tokens=(), next_id=1)
        game = BridgeGame(s)
        for a in ((('link', 0, 1),), (('link', 1, 1),),
                  (('link', 1, 2), ('link', 1, 0)),
                  (('link', 1, 2), ('pass',), ('pass',), ('pass',), ('pass',))):
            with self.assertRaises(ValueError):
                step_bridge(game, a)
        active = step_bridge(game, (('link', 1, 2),))
        self.assertEqual(active.state.progress, (0, 0, 0))
        with self.assertRaises(ValueError):
            step_bridge(active, (('link', 1, 0),))
        self.assertEqual(s.progress, (0, 1, 0))

    def test_bonus_even_if_source_capacitor_already_full(self):
        s = State(round=8, hp=7, progress=(3, 3, 1), coolant=3,
                  tokens=(Token(1, 1, 0, 1, 1), Token(2, 1, 0, -1, 1)), next_id=3)
        game = BridgeGame(s, Link(1, 2, 1))
        end = step_bridge(game)
        self.assertEqual(end.state.progress, (3, 3, 2))
        self.assertEqual(end.state.over, 'win')


if __name__ == '__main__':
    unittest.main()
