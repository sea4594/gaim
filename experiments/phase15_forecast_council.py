"""Pass 15 research only: limited-information storm forecasts and sealed edit proposals.

This does NOT alter shipping rules. We explicitly test the information value of
one truthful public signal and the possibility of conditional advance orders.
No UI-enforceable signal system can prevent external voice/chat side channels.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product
from typing import NamedTuple

from experiments.phase06_lab import Experiment, opportunities, step
from experiments.phase08_lab import Trial
from experiments.phase08_survey import utility


class PublicForecast(NamedTuple):
    round: int
    # Visible storm-card silhouettes, but not exact lanes, signs or magnitudes.
    offered_counts: tuple[int, ...]
    live_tokens: tuple
    hull: int
    power: tuple
    coolant: int


@dataclass(frozen=True)
class PrivateSignal:
    # A private sensor exposes ONE fact about all offered cards; never the whole deck.
    kind: str
    values: tuple


def public_view(game: Experiment) -> PublicForecast:
    return PublicForecast(game.state.round,
                          tuple(len(game.game.deck[i]) for i in game.game.available),
                          game.state.tokens, game.state.hp,
                          game.state.progress, game.state.coolant)


def private_view(game: Experiment, sensor: str) -> PrivateSignal:
    offers = tuple(game.game.deck[i] for i in game.game.available)
    if sensor == 'routes':
        return PrivateSignal(sensor, tuple(tuple(x[0] for x in wave) for wave in offers))
    if sensor == 'polarity':
        return PrivateSignal(sensor, tuple(tuple(x[1] for x in wave) for wave in offers))
    if sensor == 'strength':
        return PrivateSignal(sensor, tuple(tuple(x[2] for x in wave) for wave in offers))
    raise ValueError('unknown sensor')


def candidate_edits(game: Experiment):
    """Advance orders can target visible existing tokens, NEVER secret arrivals.

    We restrict this prototype to one edit and keep pass always legal. The
    actual mechanics reducer applies exactly the original action validation.
    """
    ids = {t.id for t in game.state.tokens}
    out = [('pass',)]
    seen = set(out)
    for action in opportunities(game):
        if len(action) > 1 and isinstance(action[1], int) and action[1] in ids:
            if action not in seen:
                out.append(action)
                seen.add(action)
    return tuple(out)


def resolve(game: Experiment, storm: int, edit=('pass',)) -> Experiment:
    if type(storm) is not int or storm not in range(len(game.game.available)):
        raise ValueError('invalid forecast selection')
    if edit not in candidate_edits(game):
        raise ValueError('illegal sealed edit')
    # The action is locked before the incoming card is revealed; a pass is
    # represented by zero edits. Forecast choice is separate from the edit.
    edits = () if edit == ('pass',) else (edit,)
    return step(game, edits, draft=storm)


def score(game: Experiment):
    return utility(Trial(game, 'control'))


def payoff_table(game: Experiment, horizon=2, metric="heuristic"):
    """For each advance edit, evaluate both offers after a fixed public continuation.

    Follow-up is deliberately a deterministic PASS policy. This is a short
    planning diagnostic, not optimal gameplay or a fair win-rate comparison.
    """
    if horizon not in (1,2,3):raise ValueError('unsupported planning horizon')
    if metric not in ('heuristic','survival'):raise ValueError('unsupported metric')
    result={}
    for a in candidate_edits(game):
        values=[]
        for i in range(len(game.game.available)):
            g=resolve(game,i,a)
            for _ in range(horizon-1):
                if not g.state.over:g=step(g,(),draft=0)
            values.append(score(g) if metric=="heuristic" else float(g.state.hp>0))
        result[a]=tuple(values)
    return result


def information_value(tables: list[dict]):
    """Finite-world decision-analysis with private waves and shared public board.

    Baseline: operator must commit SAME action in every world; scout chooses
    best offer for that action after seeing both hidden storm cards.
    Perfect briefing: operator can condition its action on the actual world.
    1-bit bound: arbitrary truthful binary signal partitions worlds into 2
    groups; this is an OPTIMISTIC upper bound, not an achievable protocol.

    Values use the existing one-round heuristic (NOT game win probability).
    """
    if not tables: raise ValueError('at least one hidden world required')
    actions = tuple(tables[0])
    if any(tuple(t) != actions for t in tables):
        raise ValueError('same public board must imply same eligible edits')
    m = len(tables)
    best_by_world = [max(max(row) for row in table.values()) for table in tables]
    perfect = sum(best_by_world) / m
    def best_for_world_indices(indices):
        return max(sum(max(tables[i][a]) for i in indices) for a in actions)
    baseline = best_for_world_indices(range(m)) / m
    best_bit = baseline
    for assignment in product((0,1), repeat=m):
        if not (0 in assignment and 1 in assignment):continue
        subtotal = sum(best_for_world_indices([i for i,b in enumerate(assignment) if b == value])
                       for value in (0,1))
        best_bit = max(best_bit, subtotal/m)
    return {'blind':baseline,'one_bit_upper':best_bit,'perfect_upper':perfect,
            'signal_value':best_bit-baseline,'perfect_value':perfect-baseline,
            'worlds':m,'edits':len(actions)}


def truthful_signal(game: Experiment, kind: str) -> int:
    """A one-bit deterministic fact. No outcome-aware coded oracle messages."""
    a,b=(game.game.deck[i] for i in game.game.available)
    if kind == 'left_route':
        return int(sum(t[0]==0 for t in a)>sum(t[0]==0 for t in b))
    if kind == 'negative':
        return int(sum(t[1]==-1 for t in a)>sum(t[1]==-1 for t in b))
    if kind == 'large':
        return int(sum(t[2]>=2 for t in a)>sum(t[2]>=2 for t in b))
    raise ValueError('unknown truthfully reportable fact')


def signal_value(tables: list[dict], bits: list[int]):
    """Best committed action under each truthful message (oracle receiver policy).

    Receiver's hypothetical mapping from signal to action uses all four
    worlds' payoffs: this is an upper bound on learnable decisions, not a
    self-contained human communication protocol.
    """
    if len(bits)!=len(tables) or any(b not in (0,1) for b in bits):
        raise ValueError('binary signal per world')
    actions=tuple(tables[0])
    def sub(indices):
        return max(sum(max(tables[i][a]) for i in indices) for a in actions)
    return sum(sub([i for i,b in enumerate(bits) if b==k]) for k in (0,1) if k in bits)/len(bits)


def two_signal_value(tables: list[dict], bits_a: list[int], bits_b: list[int]):
    """Upper bound on using two independent factual reports."""
    if len(bits_a)!=len(tables) or len(bits_b)!=len(tables):
        raise ValueError('signal count mismatch')
    actions=tuple(tables[0])
    partitions={(bits_a[i],bits_b[i]) for i in range(len(tables))}
    return sum(max(sum(max(tables[i][a]) for i in range(len(tables))
                       if (bits_a[i],bits_b[i])==code) for a in actions)
               for code in partitions)/len(tables)


def make_world(game: Experiment, card_a: tuple, card_b: tuple) -> Experiment:
    if len(game.game.available)!=2:raise ValueError('requires two-offer storm market')
    deck = list(game.game.deck)
    deck[game.game.available[0]] = card_a
    deck[game.game.available[1]] = card_b
    return replace(game,game=replace(game.game,deck=tuple(deck)))


def run_witness(game:Experiment, edit, choice):
    """Return a replayable witness with actual Charge Loom reducer results."""
    end=resolve(game,choice,edit)
    return {'round':game.state.round, 'edit':edit,'choice':choice,
            'forecast':public_view(game)._asdict(),
            'result':{'power':end.state.progress,'hull':end.state.hp,
                      'coolant':end.state.coolant,'over':end.state.over,
                      'heuristic':score(end)}}
