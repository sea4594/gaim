"""Pass 06: independent co-op operator, storm-market and resource-conversion laboratory.

Nothing in this module is imported into production. Rules remain explicit, deterministic,
immutable, and replayable. Operators are four *virtual* planning consoles, not rigid
player roles; 1-4 humans split those consoles without changing team capabilities.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from reference.charge_loom_v01 import Token
from experiments.phase05_lab import Design, step as design_step, options as design_options
from experiments.rules_tournament import planning_tokens

MODES = ('open','market','paid_market','operator','market_operator','recycle','regulator','market_recycle','paid_market_recycle')
VERBS = ('shift','hold','damp','flip','accelerate','bridge')
# The same four virtual consoles exist at every player count. Randomly rotated
# specialties are visible before actions are chosen: no hidden-information gotchas.
PAIRS = (('shift','hold'),('shift','damp'),('flip','accelerate'),('bridge','hold'))


def hand(seed: int, round_index: int):
    """Deterministic public 2-card menus; consistent under client reconnect/replay."""
    offset=(seed*7 + round_index*5) % 4
    return tuple(PAIRS[(i+offset)%4] for i in range(4))


def owners(players:int,round_index:int):
    """Rotates 4 virtual consoles evenly. One player always receives all four."""
    if type(players) is not int or players not in range(1,5):
        raise ValueError('player count must be 1-4')
    return tuple((round_index+i)%players for i in range(4))


@dataclass(frozen=True)
class Experiment:
    game: Design
    mode: str
    last_edits: tuple[tuple,...]=()
    last_operators: tuple[int,...]=()

    @classmethod
    def new(cls,mode='open',seed=0,state=None,waves=None,mission='standard'):
        if mode not in MODES:raise ValueError('unknown mode')
        underlying='draft_accelerate' if 'market' in mode else 'accelerate'
        return cls(Design.new(underlying,seed,state,waves,mission),mode)

    @property
    def state(self):return self.game.state


def public_forecast(g:Experiment):
    """Up to three public wave cards; the two eligible offers and one preview.

    This is the intended public information model for future-facing planning.
    Other cards remain sealed even though this reference lab stores full decks.
    """
    deck=g.game.deck
    if 'market' in g.mode:
        indices=list(g.game.available)
        if g.game.cursor<len(deck):indices.append(g.game.cursor)
    else:
        indices=list(range(g.state.round,min(len(deck),g.state.round+3)))
    return tuple((ix,deck[ix]) for ix in indices)


def opportunities(g:Experiment,choice=0):
    from experiments.phase05_survey import available_actions
    out=available_actions(g.game,choice)
    if g.mode=='regulator':
        ids={t.id:t for t in planning_tokens(g.game.core.trial)}
        out=[a for a in out if a[0]!='flip' or ids[a[1]].size<2 or g.state.coolant>0]
    if 'recycle' in g.mode:
        for lane,p in enumerate(g.state.progress):
            if p>0 and g.state.coolant<3:out.append(('recycle',lane))
    return out


def step(g:Experiment,actions=(),draft=None,operators=None):
    """Apply one plan; draft is an independent public round decision, not an edit.

    `operators` indicates which virtual console plays each corresponding edit.
    In operator mode a console has one activation maximum and the selected verb
    must be present on its public two-card menu. Passing is always legal.
    """
    if g.state.over:raise ValueError('finished')
    actions=tuple(tuple(a) for a in actions)
    if len(actions)>4:raise ValueError('maximum four edits')
    if draft is not None and 'market' not in g.mode:raise ValueError('no market')
    if g.mode.startswith('paid_market') and draft==1 and len(actions)>=4:
        raise ValueError('choosing later storm costs one of four edits')
    if draft is not None and (type(draft) is not int or draft<0 or draft>=len(g.game.available)):
        raise ValueError('invalid market offer')
    if operators is None:operators=tuple(range(len(actions)))
    operators=tuple(operators)
    if len(operators)!=len(actions):raise ValueError('one console for each action')
    if 'operator' in g.mode:
        cards=hand(g.state.seed,g.state.round)
        if len(set(operators))!=len(operators):raise ValueError('console cannot play twice')
        for a,o in zip(actions,operators):
            if type(o) is not int or o not in range(4):raise ValueError('invalid console')
            if not a or a[0] not in cards[o]:raise ValueError('card absent from console')
    # Do not charge power for an action that fails core validation. Immutable design
    # means failure never mutates the source Game.
    game=g.game
    actual=[]
    reg_cost=0
    for a in actions:
        if a[0]=='recycle':
            if 'recycle' not in g.mode or len(a)!=2 or type(a[1]) is not int or a[1] not in range(3):
                raise ValueError('bad recycling')
            if g.state.progress[a[1]]<1 or g.state.coolant>=3:raise ValueError('recycling unavailable')
            if sum(x[0]=='recycle' for x in actions)>1:raise ValueError('only one recycling per round')
        else:actual.append(a)
        if a[0]=='flip' and g.mode=='regulator':
            ids={t.id:t for t in planning_tokens(game.core.trial)}
            if a[1] not in ids:raise ValueError('no such token')
            if ids[a[1]].size>=2:reg_cost+=1
    state=game.state
    progress=list(state.progress)
    coolant=state.coolant
    if reg_cost:
        if coolant<reg_cost:raise ValueError('not enough coolant for high strength flip')
        coolant-=reg_cost
    for a in actions:
        if a[0]=='recycle':
            progress[a[1]]-=1;coolant+=1
    if reg_cost or len(actual)!=len(actions):
        core=game.core
        trial=core.trial
        core=replace(core,trial=replace(trial,state=replace(state,coolant=coolant,progress=tuple(progress))))
        game=replace(game,core=core)
    edits=list(actual)
    if draft is not None:edits.insert(0,('draft',draft))
    done=design_step(game,edits)
    return Experiment(done,g.mode,actions,operators)
