"""Pass 16: opt-in hidden-storm conditional commitments, not shipping rules.

A sealed pair reserves TWO edit slots to execute just ONE action, chosen by a
publicly verifiable rule after the currently hidden storm is revealed. The
existing Market makes the offered storms public, so this proposal only makes
sense if paired with a *different* future-information schedule. Never claim
this system solves quarterbacking or adds value to today's public Market.
"""
from __future__ import annotations
from dataclasses import dataclass
from experiments.phase15_forecast_council import candidate_edits,resolve

TRIGGERS=('left','negative','large')


def triggers(wave):
    """Single-card truthful trigger, independent of outcomes and player identity."""
    return {
        'left':sum(1 for t in wave if t[0]==0)>=2,
        'negative':sum(1 for t in wave if t[1]==-1)>=2,
        'large':sum(1 for t in wave if t[2]>=2)>=2,
    }


@dataclass(frozen=True)
class GuardedOrder:
    kind: str
    when_true: tuple
    when_false: tuple


def validate(game,order):
    if order.kind not in TRIGGERS:raise ValueError('invalid guard')
    choices=candidate_edits(game)
    if order.when_true not in choices or order.when_false not in choices:
        raise ValueError('invalid sealed branch')
    if order.when_true==order.when_false:raise ValueError('identical branches waste reserved edit')
    return order


def execute(game,storm_index,order):
    """Resolves exactly one existing legal action, after a hidden offer is opened.

    In a real variant the commitment would be submitted in advance and reserve
    TWO of four shared edit slots; this prototype models resolution only.
    The trigger is evaluated on the *selected* offered storm, not entire deck.
    """
    validate(game,order)
    if type(storm_index) is not int or storm_index not in range(len(game.game.available)):
        raise ValueError('unknown storm selection')
    wave=game.game.deck[game.game.available[storm_index]]
    selected=order.when_true if triggers(wave)[order.kind] else order.when_false
    return resolve(game,storm_index,selected)


def offer_score(table,action,offer):return table[action][offer]


def best_fixed(tables):
    """One fixed action, scout can choose the better offer in each hidden world."""
    actions=tuple(tables[0])
    return max(sum(max(t[action]) for t in tables)/len(tables) for action in actions)


def best_guarded(tables,worlds,kinds=TRIGGERS):
    """Upper bound when both branches are selected with knowledge of all worlds.

    The per-world scout still chooses the better of the two offered storms.
    The score does NOT subtract an opportunity cost for reserving two edit slots
    rather than one. Therefore a strict improvement is necessary but not
    sufficient to promote the rule.
    """
    if len(tables)!=len(worlds) or not tables:raise ValueError('mismatched boards')
    actions=tuple(tables[0])
    if any(tuple(t)!=actions for t in tables):raise ValueError('different legal actions')
    champion=(best_fixed(tables),None)
    for kind in kinds:
        bits=[tuple(triggers(w.game.deck[i])[kind] for i in w.game.available) for w in worlds]
        for yes in actions:
            for no in actions:
                if yes==no:continue
                value=sum(max(t[yes if b else no][j] for j,b in enumerate(pair))
                          for t,pair in zip(tables,bits))/len(tables)
                if value>champion[0]+1e-9:champion=(value,GuardedOrder(kind,yes,no))
    return champion
