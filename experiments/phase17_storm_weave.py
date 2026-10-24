"""Pass 17 research: route/payload exchange between two offered storm cards.

A WEAVE keeps both offers' total token identities, signs, strengths, and route
patterns, but exchanges which payload travels along which route. Only valid if
both cards have the same number of charges. Costs one coolant before resolution.
Both rewritten offers remain in the two-offer market; nothing is erased.
This is a standalone research variant, NOT shipping gameplay.
"""
from dataclasses import replace
from experiments.phase15_forecast_council import make_world


def weave_pair(card_a, card_b):
    if not card_a or len(card_a) != len(card_b):
        raise ValueError('equal, nonempty storm sizes required')
    for card in (card_a,card_b):
        for token in card:
            if (len(token)!=3 or type(token[0]) is not int or token[0] not in range(3)
                or type(token[1]) is not int or token[1] not in (-1,1)
                or type(token[2]) is not int or token[2] not in (1,2,3)):
                raise ValueError('invalid storm token')
    new_a=tuple((route[0],payload[1],payload[2]) for route,payload in zip(card_a,card_b))
    new_b=tuple((route[0],payload[1],payload[2]) for route,payload in zip(card_b,card_a))
    return new_a,new_b


def apply_weave(game):
    if game.state.coolant<1:raise ValueError('weave requires one coolant')
    if len(game.game.available)!=2:raise ValueError('weave requires exactly two offers')
    a,b=(game.game.deck[i] for i in game.game.available)
    wa,wb=weave_pair(a,b)
    result=make_world(game,wa,wb)
    core=result.game.core
    trial=core.trial
    new_state=replace(trial.state,coolant=trial.state.coolant-1)
    new_core=replace(core,trial=replace(trial,state=new_state))
    return replace(result,game=replace(result.game,core=new_core))


def payload_histogram(cards):
    from collections import Counter
    return Counter((t[1],t[2]) for c in cards for t in c)


def route_histogram(cards):
    from collections import Counter
    return Counter(t[0] for c in cards for t in c)
