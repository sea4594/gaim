"""Experimental Charge Loom energy economy; NOT the production v0.1 rules.

This deliberately uses the Phase 5 Python token/state representation to measure
rule changes without breaking the TypeScript golden traces. No external deps.

Modes:
    barrier: once/round, one edit and one stored energy from lane prevents up
             to two damage from that lane this round (breach AND final leakage).
    relay:   once/round, one edit and one energy from a source outer lane moves
             ONE charge directly to the opposite outer lane.

All payments use energy stored BEFORE this round's collisions. Ordinary edits,
limits, arrival schedule, charging and victory remain unchanged. Power cannot
be spent from another lane, paid twice in one round, or paid from energy earned
this round. Effects are part of the shared team budget (max four total edits).
"""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from reference.charge_loom_v01 import State, Token, arrivals, step

MODES = ('baseline', 'barrier', 'relay')


def planning_tokens(state: State) -> tuple[Token, ...]:
    return state.tokens + tuple(Token(state.next_id + index, lane, 2, sign, size)
                                for index, (lane, sign, size)
                                in enumerate(arrivals(state.seed, state.round + 1)))


def options(state: State, mode: str) -> list[tuple]:
    if mode not in MODES:
        raise ValueError('unknown experiment mode')
    result = []
    for t in planning_tokens(state):
        if t.lane > 0:
            result.append(('shift', t.id, -1))
        if t.lane < 2:
            result.append(('shift', t.id, 1))
        if not t.held:
            result.append(('hold', t.id))
        if state.coolant:
            result.append(('damp', t.id))
        if mode == 'relay' and t.lane in (0, 2) and state.progress[t.lane] > 0:
            result.append(('relay', t.id))
    if mode == 'barrier':
        for lane, stored in enumerate(state.progress):
            if stored > 0:
                result.append(('barrier', lane))
    return result


def step_experimental(state: State, actions: Iterable[tuple] = (), *, mode: str = 'baseline') -> State:
    """Atomic experimental transition, preserving v0.1 when no new edit appears."""
    if mode not in MODES:
        raise ValueError('unknown experiment mode')
    if mode == 'baseline':
        return step(state, tuple(actions))
    if state.over:
        raise ValueError('game ended')
    actions = tuple(tuple(a) for a in actions)
    if len(actions) > 4:
        raise ValueError('maximum four edits including a power activation')
    round_number = state.round + 1
    charges = list(planning_tokens(state))
    used = set()
    held = set()
    coolant = state.coolant
    power = list(state.progress)
    shields = [0, 0, 0]
    special_used = False
    # Validate all edits and compute on local state; any error must leave caller
    # State unchanged. Energy spending never uses this round's newly produced power.
    for action in actions:
        if not action:
            raise ValueError('empty action')
        kind = action[0]
        if kind == 'pass':
            if len(action) != 1:
                raise ValueError('malformed pass')
            continue
        if kind == 'barrier':
            if mode != 'barrier' or len(action) != 2 or special_used:
                raise ValueError('invalid or duplicate BARRIER')
            lane = action[1]
            if type(lane) is not int or lane not in (0, 1, 2) or power[lane] < 1:
                raise ValueError('BARRIER requires stored power in targeted lane')
            power[lane] -= 1
            shields[lane] = 2
            special_used = True
            continue
        if kind not in ('shift', 'hold', 'damp', 'relay'):
            raise ValueError('unknown edit')
        if len(action) != (3 if kind == 'shift' else 2):
            raise ValueError('malformed edit')
        token_id = action[1]
        if type(token_id) is not int or token_id in used:
            raise ValueError('bad or duplicate token id')
        used.add(token_id)
        index = next((i for i, t in enumerate(charges) if t.id == token_id), None)
        if index is None:
            raise ValueError('missing token')
        token = charges[index]
        if kind == 'shift':
            direction = action[2]
            if type(direction) is not int or direction not in (-1, 1) or not 0 <= token.lane + direction <= 2:
                raise ValueError('invalid shift')
            charges[index] = replace(token, lane=token.lane + direction)
        elif kind == 'hold':
            if token.held:
                raise ValueError('token already held')
            charges[index] = replace(token, held=1, size=min(3, token.size + 1))
            held.add(token_id)
        elif kind == 'damp':
            if coolant <= 0:
                raise ValueError('not enough coolant')
            coolant -= 1
            charges[index] = replace(token, size=token.size - 1)
        elif kind == 'relay':
            if mode != 'relay' or special_used or token.lane not in (0, 2) or power[token.lane] < 1:
                raise ValueError('RELAY requires powered outer source lane, once per round')
            power[token.lane] -= 1
            charges[index] = replace(token, lane=2 - token.lane)
            special_used = True
    charges = [t for t in charges if t.size > 0]
    moved = [t if t.id in held else replace(t, row=t.row - 1) for t in charges]
    breached = [t for t in moved if t.row < 0]
    kept = [t for t in moved if t.row >= 0]
    hull = state.hp
    for lane in range(3):
        pos = sum(t.size for t in breached if t.lane == lane and t.sign == 1)
        neg = sum(t.size for t in breached if t.lane == lane and t.sign == -1)
        power[lane] = min(3, power[lane] + min(pos, neg))
        incoming = abs(pos - neg)
        absorbed = min(incoming, shields[lane])
        shields[lane] -= absorbed
        hull -= incoming - absorbed
    if round_number == 9:
        for lane in range(3):
            unpaired = sum(t.size for t in kept if t.lane == lane)
            hull -= max(0, unpaired - shields[lane])
        kept = []
    outcome = ''
    if hull <= 0:
        outcome = 'loss: breach'
    elif round_number == 9:
        outcome = 'win' if min(power) >= 2 and sum(power) >= 8 else 'loss: target'
    return State(round_number, hull, tuple(power), coolant, tuple(sorted(kept)),
                 state.next_id + len(arrivals(state.seed, round_number)), state.seed, outcome)


def evaluate(state: State) -> float:
    """Cheap, intentionally myopic diagnostic utility (NOT an optimal solver)."""
    if state.over == 'win':
        return 10000.0
    if state.over.startswith('loss: breach'):
        return -10000.0
    if state.over == 'loss: target':
        return -7000.0 + 25 * sum(state.progress)
    # Resource is scored less when nearly capped, to prevent a single rule
    # from looking good only because of arbitrary immediate point-counting.
    return (6 * state.hp + 9 * sum(state.progress) + 7 * min(state.progress)
            + 2 * state.coolant)


def choose_greedy(state: State, mode: str) -> tuple:
    """Sequential one-round edit hill climber, identical budget in all modes."""
    actions = []
    used = set()
    specials = False
    best = evaluate(step_experimental(state, actions, mode=mode))
    for _ in range(4):
        winner = None
        for action in options(state, mode):
            kind = action[0]
            if kind in ('barrier', 'relay') and specials:
                continue
            if kind not in ('barrier',) and action[1] in used:
                continue
            try:
                trial = step_experimental(state, [*actions, action], mode=mode)
            except ValueError:
                continue
            candidate = evaluate(trial)
            if candidate > best + 1e-9:
                best = candidate
                winner = action
        if winner is None:
            break
        actions.append(winner)
        if winner[0] != 'barrier':
            used.add(winner[1])
        if winner[0] in ('barrier', 'relay'):
            specials = True
    return tuple(actions)


def benchmark(seeds: Iterable[int], modes: tuple[str, ...] = MODES) -> dict:
    results = {}
    for mode in modes:
        outcomes = []
        effects = 0
        actions_count = 0
        for seed in seeds:
            s = State(seed=seed)
            while not s.over:
                planned = choose_greedy(s, mode)
                effects += sum(a[0] in ('barrier', 'relay') for a in planned)
                actions_count += len(planned)
                s = step_experimental(s, planned, mode=mode)
            outcomes.append(s)
        results[mode] = {
            'games': len(outcomes), 'wins': sum(s.over == 'win' for s in outcomes),
            'survived': sum(s.hp > 0 for s in outcomes),
            'mean_final_hull': round(sum(s.hp for s in outcomes) / len(outcomes), 3),
            'mean_stored_power': round(sum(sum(s.progress) for s in outcomes) / len(outcomes), 3),
            'power_activations': effects, 'edits': actions_count,
        }
    return results


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Diagnostic power economy (NOT shipping game rules)')
    parser.add_argument('--seeds', type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 1000:
        parser.error('--seeds must be between 1 and 1000')
    print(json.dumps(benchmark(range(args.seeds)), indent=2, sort_keys=True))
