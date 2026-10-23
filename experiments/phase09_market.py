"""Ablation: one-, two- or three-offer visible storm market.

No change to incoming cards, action verbs, resources or victory targets.
Tests decision breadth versus the extra cognitive load on a portrait phone.
"""
from __future__ import annotations
from dataclasses import replace
from experiments.phase06_lab import Experiment,step,public_forecast


def new(seed=0,offers=2,*,waves=None):
    if type(offers) is not int or offers not in (1,2,3):
        raise ValueError('offers must be 1,2,3')
    g=Experiment.new('market',seed,waves=waves)
    game=replace(g.game,available=tuple(range(offers)),cursor=offers)
    return replace(g,game=game)


def available(g):
    return tuple(g.game.deck[ix] for ix in g.game.available)


def choose(g,index,actions=()):
    if index is not None and (type(index) is not int or index<0 or index>=len(g.game.available)):
        raise ValueError('invalid storm choice')
    return step(g,actions,draft=index)
