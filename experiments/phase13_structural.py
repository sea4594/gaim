"""Pass 13: two systemic challenges to Forecast Market, research-only.

ECHO BREACH: a strength >=2 unmatched breach returns, next round, as a smaller
opposite charge. No new action. Its future deadline liability is real.

SHUNT: if a real breach collision and hull leak both occur in a round,
spend one STORED capacitor power from a matching lane to prevent up to two
points of same-round leak. Does not consume an edit, but sacrifices the
victory resource. No damage can be blocked without a legitimate collision.

Both opt-in wrappers preserve the Phase 7 production rules.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from experiments.phase06_lab import Experiment, step as forecast_step
from experiments.rules_tournament import planning_tokens
from reference.charge_loom_v01 import Token, TURNS

MODES = ('control', 'echo_breach', 'shunt')


def modify(exp: Experiment, **updates):
    core = exp.game.core
    state = replace(exp.state, **updates)
    return replace(exp, game=replace(exp.game, core=replace(core, trial=replace(core.trial, state=state))))

@dataclass(frozen=True)
class Structural:
    exp: Experiment
    mode: str = 'control'
    echoes: int = 0
    shielded: int = 0
    spent: int = 0

    @classmethod
    def new(cls, mode='control', seed=0, state=None, waves=None):
        if mode not in MODES:
            raise ValueError('invalid research mode')
        return cls(Experiment.new('market' if state is None or state.round == 0 else 'open',
                                  seed=seed, state=state, waves=waves), mode)

    @property
    def state(self):
        return self.exp.state


def _breach_balance(exp: Experiment, actions=(), draft=None):
    """Per-lane signed unresolved NOW strength, after CURRENT edits and movement.

    Independent calculation; checks the base engine's same-round HP loss before
    adding echo mechanics. This deliberately excludes round-nine deadline debt.
    """
    t = exp.game.core.trial
    if exp.mode == 'market' and exp.state.round < 7:
        choice = 0 if draft is None else draft
        if type(choice) is not int or choice not in range(len(exp.game.available)):
            raise ValueError('bad offer')
        waves = list(t.waves)
        waves[exp.state.round] = exp.game.deck[exp.game.available[choice]]
        t = replace(t, waves=tuple(waves))
    tokens = {x.id: x for x in planning_tokens(t)}
    held = set()
    for a in actions:
        typ = a[0]
        if typ in ('shift', 'hold', 'damp', 'flip', 'accelerate'):
            if a[1] not in tokens:
                raise ValueError('bad token')
            tok = tokens[a[1]]
            if typ == 'shift': tok = replace(tok, lane=tok.lane + a[2])
            elif typ == 'hold':
                tok = replace(tok, size=min(3, tok.size + 1), held=1)
                held.add(tok.id)
            elif typ == 'damp': tok = replace(tok, size=tok.size - 1)
            elif typ == 'flip': tok = replace(tok, sign=-tok.sign)
            elif typ == 'accelerate': tok = replace(tok, row=tok.row - 1)
            tokens[tok.id] = tok
    signed = [0, 0, 0]
    matched = [0, 0, 0]
    for lane in range(3):
        arrivals = [tok for tok in tokens.values()
                    if tok.lane == lane and tok.size > 0 and tok.id not in held and tok.row == 0]
        pos = sum(tok.size for tok in arrivals if tok.sign > 0)
        neg = sum(tok.size for tok in arrivals if tok.sign < 0)
        signed[lane] = pos - neg
        matched[lane] = min(pos, neg)
    return tuple(signed), tuple(matched)


def shunt_choices(g: Structural, actions=(), draft=None):
    if g.mode != 'shunt': return ()
    signed, match = _breach_balance(g.exp, actions, draft)
    if not sum(abs(v) for v in signed): return ()
    after = forecast_step(g.exp, actions, draft=draft)
    return tuple(lane for lane in range(3) if match[lane] > 0 and after.state.progress[lane] >= 1)


def step(g: Structural, actions=(), *, draft=None, shunt_lane=None):
    if g.state.over: raise ValueError('finished')
    actions = tuple(tuple(x) for x in actions)
    if shunt_lane is not None and g.mode != 'shunt': raise ValueError('no shunt allowed')
    if shunt_lane is not None and (type(shunt_lane) is not int or shunt_lane not in range(3)):
        raise ValueError('invalid source lane')
    signed, matches = _breach_balance(g.exp, actions, draft)
    after = forecast_step(g.exp, actions, draft=draft)
    after_hp = after.state.hp
    ordinary_leak = sum(abs(x) for x in signed)
    # Validate physical model with base reducer, excluding terminal outstanding
    # charge debt (which is collected separately on round nine).
    if g.state.round + 1 < TURNS:
        assert g.state.hp - after_hp == ordinary_leak, 'breach parity failure'
    echoes = g.echoes
    shielded = g.shielded
    spent = g.spent
    if g.mode == 'echo_breach' and after.state.hp > 0 and after.state.round < TURNS:
        new = []
        for lane, delta in enumerate(signed):
            if abs(delta) >= 2:
                new.append(Token(after.state.next_id + len(new), lane, 1,
                                 -1 if delta > 0 else 1, min(2, abs(delta) // 2), 1))
        if new:
            after = modify(after, tokens=tuple(sorted(after.state.tokens + tuple(new))),
                           next_id=after.state.next_id + len(new))
            echoes += len(new)
    elif g.mode == 'shunt' and shunt_lane is not None:
        if not (ordinary_leak > 0 and matches[shunt_lane] > 0 and after.state.progress[shunt_lane] >= 1):
            raise ValueError('shunt needs real collision, stored power, and same-round leak')
        progress = list(after.state.progress)
        progress[shunt_lane] -= 1
        saved = min(2, ordinary_leak)
        hp = after_hp + saved
        if hp <= 0: outcome = 'loss: breach'
        elif after.state.round == TURNS:
            outcome = 'win' if min(progress) >= 2 and sum(progress) >= 8 else 'loss: target'
        else: outcome = ''
        after = modify(after, hp=hp, progress=tuple(progress), over=outcome)
        shielded += saved
        spent += 1
    return Structural(after, g.mode, echoes, shielded, spent)
