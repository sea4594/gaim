"""Pass 09: opt-in variable objective laboratory for Forecast Market.

Objective drafting borrows public mission selection from cooperative board games.
The *same* wave schedule and core verbs apply; no production imports this lab.
Tracks actual strength matching, not capacitor deltas, so Bridge bonus does not
falsely count as a physical collision in a destination lane.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from experiments.phase06_lab import Experiment, step as market_step
from experiments.phase05_lab import _preflight_matches
from experiments.rules_tournament import planning_tokens
from reference.charge_loom_v01 import State

MISSIONS = ('grid', 'fortress', 'voltage', 'concord', 'circuit')


def victory(mission, state, large_mask=0, synchronized=0, lane_mask=0):
    """Precise final win predicates; every mission still requires all 3 lanes."""
    p = state.progress
    if state.hp <= 0:
        return False
    if mission == 'grid':
        return min(p) >= 2 and sum(p) >= 8
    if mission == 'fortress':
        return state.hp >= 6 and min(p) >= 1 and sum(p) >= 6
    if mission == 'voltage':
        return large_mask.bit_count() >= 2 and min(p) >= 1 and sum(p) >= 7
    if mission == 'concord':
        return synchronized >= 2 and min(p) >= 1 and sum(p) >= 6
    if mission == 'circuit':
        return lane_mask == 7 and min(p) >= 1 and sum(p) >= 7
    raise ValueError('unrecognized mission')


@dataclass(frozen=True)
class Trial:
    exp: Experiment
    mission: str
    lane_mask: int = 0
    # Mirrors counters from the underlying game, so exact history matters.

    @classmethod
    def new(cls, mission='grid', seed=0, state: State | None = None,
            waves=None, *, lane_mask=0, large_mask=0, synchronized=0):
        if mission not in MISSIONS:
            raise ValueError('unrecognized mission')
        exp = Experiment.new('market' if state is None or state.round == 0 else 'open',
                             seed=seed, state=state, waves=waves)
        game = replace(exp.game, large=large_mask, synchronized=synchronized)
        return cls(replace(exp, game=game), mission, lane_mask)

    @property
    def state(self):
        return self.exp.state

    @property
    def synchronized(self):
        return self.exp.game.synchronized

    @property
    def large_mask(self):
        return self.exp.game.large


def step(g: Trial, actions=(), *, draft=None):
    if g.state.over:
        raise ValueError('game already ended')
    edits = tuple(tuple(a) for a in actions)
    if len(edits) > 4:
        raise ValueError('too many edits')
    # Match counting uses the actual offered wave selected this round, not a
    # hidden future card. The underlying reducer validates every submitted edit.
    core_trial = g.exp.game.core.trial
    if g.exp.mode == 'market' and g.state.round < 7:
        choice = 0 if draft is None else draft
        if type(choice) is not int or choice not in range(len(g.exp.game.available)):
            raise ValueError('invalid public storm offer')
        schedule = list(core_trial.waves)
        schedule[g.state.round] = g.exp.game.deck[g.exp.game.available[choice]]
        core_trial = replace(core_trial, waves=tuple(schedule))
    matched = _preflight_matches(g.exp.game, edits, core_trial)
    out = market_step(g.exp, edits, draft=draft)
    mask = g.lane_mask
    for lane, amount in enumerate(matched):
        if amount:
            mask |= 1 << lane
    s = out.state
    if s.over:
        won = victory(g.mission, s, out.game.large, out.game.synchronized, mask)
        status = 'loss: breach' if s.hp <= 0 else ('win' if won else 'loss: target')
        core = out.game.core
        core = replace(core, trial=replace(core.trial, state=replace(s, over=status)))
        out = replace(out, game=replace(out.game, core=core))
    return Trial(out, g.mission, mask)


def mission_offers(seed: int):
    """Public, reproducible two-mission offer; both revealed before round 1."""
    first = seed % len(MISSIONS)
    second = (first + 1 + ((seed // len(MISSIONS)) % (len(MISSIONS) - 1))) % len(MISSIONS)
    return (MISSIONS[first], MISSIONS[second])
