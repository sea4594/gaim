"""Pass 08: opportunity-cost economy and tempo tournament, research-only.

All modes retain six verbs and the two-offer storm market. Unlike prior free
bonuses, alternatives must compete for coolant, capacitor energy, or edit slots.
Uses the Phase 06 public-forecast reducer and existing Phase 07 Council rules.
Nothing imports this module into the shipping engine.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from experiments.phase06_lab import Experiment, step as market_step
from experiments.phase07_lab import Audit, step as council_step
from reference.charge_loom_v01 import State

MODES = ('control','coolant_bid','power_bid','repair','council','council_coolant','surge')


def modify(exp:Experiment, **state_updates) -> Experiment:
    """Deep-copy state only; preserves immutable design and full wavebook."""
    core=exp.game.core
    state=replace(exp.state,**state_updates)
    return replace(exp,game=replace(exp.game,core=replace(core,trial=replace(core.trial,state=state))))


@dataclass(frozen=True)
class Trial:
    exp: Experiment
    mode: str = 'control'
    council: Audit | None = None
    repaired: bool = False
    surged: bool = False
    paid_drafts: int = 0

    @classmethod
    def new(cls, mode='control',seed=0,state:State|None=None,waves=None):
        if mode not in MODES:raise ValueError('unrecognized experiment')
        exp=Experiment.new('market' if state is None or state.round==0 else 'open',seed=seed,state=state,waves=waves)
        if mode=='surge':
            # One empty public placeholder after seven real storms. No threat
            # removed: a two-storm turn makes one subsequent arrival empty.
            exp=replace(exp,game=replace(exp.game,deck=exp.game.deck+((),)))
        council=Audit(exp,'council') if 'council' in mode else None
        return cls(exp,mode,council)

    @property
    def state(self):return self.exp.state


def step(g:Trial, actions=(), draft=None, demand=None, surge=False):
    """Resolve one complete round, with strict prepayment and no mutation on failure.

    coolant_bid: second (newer) storm costs 1 coolant before any edits.
    power_bid: second storm costs 1 center power before any edits.
    repair: once per GAME, (repair,lane) spends 2 stored energy, restores 2 hull
      (capped at 7), uses one edit.
    council: after rounds 3,6,9 pay 1 from one of two public neighboring lanes;
      if both empty, lose 2 hull. Uses the existing Phase 7 prototype exactly.
    surge: Once/game spend 1 coolant to bring BOTH offered storms this round.
      Each storm still arrives once; one later storm round is now empty.
      Storms have to be public offers, not hidden future queue entries.
    """
    if g.state.over:raise ValueError('game over')
    if draft is not None and (type(draft) is not int or draft not in range(len(g.exp.game.available))):
        raise ValueError('invalid draft')
    if surge and (g.mode!='surge' or g.surged or g.state.coolant<1 or
                  g.state.round>=7 or len(g.exp.game.available)!=2 or
                  any(i>=7 for i in g.exp.game.available)):
        raise ValueError('storm surge unavailable')
    if surge and draft not in (None,0):raise ValueError('surge consumes both offers')
    edits=tuple(tuple(a) for a in actions)
    if not edits and actions:raise ValueError('bad edits')
    if len(edits)>4:raise ValueError('edit cap exceeded')
    repairs=[a for a in edits if a and a[0]=='repair']
    if repairs:
        if g.mode!='repair' or g.repaired or len(repairs)!=1 or len(repairs[0])!=2:
            raise ValueError('repair already used or unavailable')
        src=repairs[0][1]
        if type(src) is not int or src not in range(3) or g.state.progress[src]<2 or g.state.hp>=7:
            raise ValueError('repair requires 2 power and damaged hull')
    if any(not a or a[0] not in ('repair','shift','hold','damp','flip','accelerate','bridge','pass') for a in edits):
        raise ValueError('unrecognized edit')
    if len(repairs) and edits.count(repairs[0])!=1:raise ValueError('duplicate repair')
    exp=g.exp
    charged=0
    if surge:
        ids=exp.game.available
        deck=list(exp.game.deck)
        deck[ids[0]]=deck[ids[0]]+deck[ids[1]]
        exp=modify(exp,coolant=exp.state.coolant-1)
        exp=replace(exp,game=replace(exp.game,deck=tuple(deck)))
        draft=0
    if draft==1 and g.mode in ('coolant_bid','council_coolant'):
        if exp.state.coolant<1:raise ValueError('not enough coolant to reorder')
        exp=modify(exp,coolant=exp.state.coolant-1);charged=1
    if draft==1 and g.mode=='power_bid':
        if exp.state.progress[1]<1:raise ValueError('not enough center power to reorder')
        p=list(exp.state.progress);p[1]-=1
        exp=modify(exp,progress=tuple(p));charged=1
    if repairs:
        src=repairs[0][1]
        p=list(exp.state.progress);p[src]-=2
        exp=modify(exp,progress=tuple(p),hp=min(7,exp.state.hp+2))
        edits=tuple(a for a in edits if a[0]!='repair')
    if g.council is not None:
        baseline=replace(g.council,experiment=exp)
        # Council internally applies exact storm resolution and late demands.
        after=council_step(baseline,edits,draft=draft,demand=demand)
        out_exp=after.experiment
    else:
        if demand is not None:raise ValueError('not a council game')
        after=None
        out_exp=market_step(exp,edits,draft=draft)
    if surge:
        # Base draft removed offer[0] and added one queued card. Remove the
        # other consumed offer and replenish from the visible future deck.
        available=tuple(i for i in out_exp.game.available if i!=ids[1])
        cursor=out_exp.game.cursor
        if cursor<len(out_exp.game.deck):
            available=available+(cursor,)
            cursor+=1
        out_exp=replace(out_exp,game=replace(out_exp.game,available=available,cursor=cursor))
    return Trial(out_exp,g.mode,after,g.repaired or bool(repairs),
                 g.surged or surge,g.paid_drafts+charged)
