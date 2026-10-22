"""Exhaustive one-round synthetic endgame survey; not a claim of live difficulty.

Answers whether adding a power expenditure creates extra mathematically winning
final-round action plans. Not a human playtest and not a future-knowledge test.
"""
import argparse
import json
import random
from itertools import product

from reference.charge_loom_v01 import State, Token
from experiments.power_economy import options, step_experimental
from experiments.capacitor_bridge import BridgeGame, options as bridge_options, step_bridge


def synthetic_states(count: int, *, seed: int = 406) -> list[State]:
    rng = random.Random(seed)
    result = []
    for _ in range(count):
        tokens = tuple(Token(i + 1, rng.randrange(3), 0,
                             rng.choice((-1, 1)), rng.choice((1, 1, 2)))
                       for i in range(rng.choice((2, 3))))
        progress = tuple(rng.choice((1, 2, 2, 3)) for _ in range(3))
        result.append(State(round=8, hp=rng.randint(1, 5), progress=progress,
                            coolant=rng.randint(0, 3), tokens=tokens,
                            next_id=len(tokens) + 1, seed=0))
    return result


def all_legal_plans(state: State, mode: str):
    by_token = []
    for t in state.tokens:
        choices = [()]
        choices += [(a,) for a in options(state, mode)
                    if a[0] != 'barrier' and a[1] == t.id]
        by_token.append(choices)
    special = [()]
    if mode == 'barrier':
        special += [(a,) for a in options(state, mode) if a[0] == 'barrier']
    for choices in product(*by_token):
        plan = tuple(a for group in choices for a in group)
        if mode == 'barrier':
            for extra in special:
                if len(plan) + len(extra) <= 4:
                    yield plan + extra
        else:
            yield plan


def winning_actions(state: State, mode: str) -> tuple[int, int, tuple | None]:
    wins = 0
    power_wins = 0
    example = None
    if mode == 'bridge':
        token_opts = [[()] + [(a,) for a in bridge_options(BridgeGame(state))
                               if a[0] != 'link' and a[1] == t.id]
                      for t in state.tokens]
        add = [()] + [(a,) for a in bridge_options(BridgeGame(state)) if a[0] == 'link']
        plans = (tuple(a for g in groups for a in g) + special
                 for groups in product(*token_opts) for special in add
                 if sum(len(g) for g in groups) + len(special) <= 4)
    else:
        plans = all_legal_plans(state, mode)
    for plan in plans:
        try:
            final = (step_bridge(BridgeGame(state), plan).state if mode == 'bridge'
                     else step_experimental(state, plan, mode=mode))
        except ValueError:
            continue
        if final.over == 'win':
            wins += 1
            uses_power = any(a[0] in ('barrier', 'relay', 'link') for a in plan)
            power_wins += uses_power
            if uses_power and example is None:
                example = plan
    return wins, power_wins, example


def survey(count: int, *, seed: int = 406) -> dict:
    states = synthetic_states(count, seed=seed)
    outcome = {mode: {'winnable': 0, 'total_winning_plans': 0, 'power_spend_winning_plans': 0,
                      'power_essential_states': 0}
               for mode in ('baseline', 'barrier', 'relay', 'bridge')}
    examples = {}
    for ix, state in enumerate(states):
        results = {mode: winning_actions(state, mode) for mode in outcome}
        base_wins = results['baseline'][0]
        for mode, (wins, powered, example) in results.items():
            rec = outcome[mode]
            rec['winnable'] += wins > 0
            rec['total_winning_plans'] += wins
            rec['power_spend_winning_plans'] += powered
            if mode != 'baseline' and base_wins == 0 and wins > 0:
                rec['power_essential_states'] += 1
                if mode not in examples:
                    examples[mode] = {
                        'case_index': ix, 'hull': state.hp,
                        'capacitors': list(state.progress),
                        'tokens': [[t.id, t.lane, t.sign, t.size] for t in state.tokens],
                        'winning_spend_plan': example,
                    }
    return {'method': 'exhaustive one-round action enumeration on synthetic final-round states',
            'cases': count, 'seed': seed, 'results': outcome, 'first_essential_spend': examples}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=int, default=120)
    p = parser.parse_args()
    if not 1 <= p.cases <= 1000:
        parser.error('--cases must be 1..1000')
    print(json.dumps(survey(p.cases), indent=2, sort_keys=True))
