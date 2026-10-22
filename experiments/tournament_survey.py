"""Reproducible, deliberately limited design tournament; results are not fun scores.

Two tests: enumerate legal final-round plans (fully visible threats), and trial
simple short-sighted decisions across full nine-round reference wave seeds.
The delayed variants are compared through explicit two-round witnesses, not
misleading last-round purchase metrics.
"""
from __future__ import annotations
from collections import Counter
from itertools import product
import json
import random
from reference.charge_loom_v01 import State, Token
from experiments.rules_tournament import Trial, MODES, actions, step_trial, score


def final_states(n: int, seed: int = 9504) -> tuple[State, ...]:
    rng = random.Random(seed)
    result = []
    for ix in range(n):
        amount = rng.choice((3, 4))
        tok = tuple(Token(i + 1, rng.randrange(3), 0, rng.choice((-1, 1)), rng.choice((1, 1, 2)))
                    for i in range(amount))
        s = State(round=8, hp=rng.randint(1, 6), progress=tuple(rng.choice((0,1,2,2,3)) for _ in range(3)),
                  coolant=rng.randint(0,3), tokens=tok, next_id=amount+1, seed=0)
        result.append(s)
    return tuple(result)


def action_plans(t: Trial, *, max_token_edits: int = 4, include_special: bool = True):
    opts = actions(t)
    toks = tuple(tok.id for tok in t.state.tokens) + tuple(
        tok.id for tok in t_tokens_new(t))
    by_token = []
    for tid in toks:
        by_token.append([()] + [(a,) for a in opts if a[0] in ('shift', 'hold', 'damp') and a[1] == tid])
    extras = [()]
    if include_special:
        extras += [(a,) for a in opts if a[0] not in ('shift', 'hold', 'damp', 'pass')]
    for groups in product(*by_token):
        plan = tuple(a for g in groups for a in g)
        if len(plan) > max_token_edits:
            continue
        for extra in extras:
            if len(plan) + len(extra) <= 4:
                yield plan + extra


def t_tokens_new(t: Trial):
    from experiments.rules_tournament import planning_tokens
    return [tok for tok in planning_tokens(t) if tok.id >= t.state.next_id]


def final_survey(n: int = 160, seed: int = 9504) -> dict:
    cases = final_states(n, seed)
    result = {mode: {'winnable': 0, 'states_with_spend_in_a_win': 0,
                     'exclusively_special_wins': 0, 'total_winning_plans': 0}
              for mode in ('baseline', 'sweep', 'overcharge', 'harmonic')}
    witnesses = {}
    for idx, s in enumerate(cases):
        details = {}
        for mode in result:
            t = Trial(s, mode)
            wins = 0; special_wins = 0; first_special = None
            for a in action_plans(t):
                try:
                    final = step_trial(t, a)
                except ValueError:
                    continue
                if final.state.over == 'win':
                    wins += 1
                    if any(edit[0] in ('sweep', 'overcharge') for edit in a):
                        special_wins += 1
                        if first_special is None: first_special = a
            details[mode] = (wins, special_wins, first_special)
            result[mode]['winnable'] += (wins > 0)
            result[mode]['states_with_spend_in_a_win'] += (special_wins > 0)
            result[mode]['total_winning_plans'] += wins
        for mode in ('sweep', 'overcharge', 'harmonic'):
            if details['baseline'][0] == 0 and details[mode][0] > 0:
                result[mode]['exclusively_special_wins'] += 1
                if mode not in witnesses:
                    witnesses[mode] = {'case': idx, 'state': repr(s), 'one_winning_plan': details[mode][2]}
    return {'cases': n, 'seed': seed, 'test': 'exhaustive final-round action enumeration, shared synthetic states',
            'results': result, 'newly_winnable_examples': witnesses}


def greedy_game(mode: str, seed: int, max_rounds=9) -> dict:
    t = Trial.new(mode, seed)
    chosen = Counter(); edits = 0; used_rounds = 0
    while not t.state.over and t.state.round < max_rounds:
        plan = []
        value = score(step_trial(t))
        for _ in range(4):
            best = None
            for a in actions(t):
                if a[0] == 'pass': continue
                if a in plan: continue
                try:
                    nxt = step_trial(t, plan + [a])
                except ValueError:
                    continue
                v = score(nxt)
                if v > value + 0.0001:
                    value = v
                    best = a
            if best is None: break
            plan.append(best)
        for a in plan: chosen[a[0]] += 1
        used_rounds += 1
        edits += len(plan)
        t = step_trial(t, plan)
    return {'win': t.state.over == 'win', 'hp': t.state.hp, 'power': sum(t.state.progress),
            'edits': edits, 'rounds': used_rounds, 'actions': chosen}


def greedy_survey(seeds=24) -> dict:
    report = {}
    for mode in MODES:
        games = [greedy_game(mode, i) for i in range(seeds)]
        counts = Counter()
        for g in games: counts.update(g['actions'])
        report[mode] = {'wins': sum(g['win'] for g in games),
                        'survival': sum(g['hp'] > 0 for g in games),
                        'mean_power': round(sum(g['power'] for g in games)/seeds, 2),
                        'mean_actions_per_round': round(sum(g['edits'] for g in games)/sum(g['rounds'] for g in games), 2),
                        'actions': dict(sorted(counts.items()))}
    return {'seeds': seeds, 'policy': 'one-step hill-climbing agent; delayed mechanics intentionally disadvantaged',
            'results': report}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--final-cases', type=int, default=160)
    parser.add_argument('--greedy-seeds', type=int, default=24)
    args = parser.parse_args()
    print(json.dumps({'final': final_survey(args.final_cases), 'full_games': greedy_survey(args.greedy_seeds)}, indent=2))
