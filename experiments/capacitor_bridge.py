"""CAPACITOR BRIDGE candidate: a TWO-resolution investment, not shipping rules.

An activation takes one of the team's four edits and spends one *existing*
charge from the source capacitor to connect adjacent lanes. For the current
resolution and the next, if at least one positive/negative pair collides in the
source lane, the destination gains ONE extra capacitor power (subject to cap 3).
The source also receives its ordinary collision yield. At most one bridge may
be active; it cannot be replaced or stacked. No payment with same-round yield.

Contrast with BARRIER and RELAY: this creates a temporary two-beat production
engine rather than a once-only emergency defence or traversal discount.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from reference.charge_loom_v01 import State, step
from experiments.power_economy import planning_tokens, options as simple_options


@dataclass(frozen=True)
class Link:
    source: int
    target: int
    remaining: int  # 1 only once round resolved; 2 at first resolution


@dataclass(frozen=True)
class BridgeGame:
    state: State
    link: Link | None = None


def collision_lanes(state: State, edits: tuple[tuple, ...]) -> tuple[bool, bool, bool]:
    """Calculate actual normal breaches, including edits, even at capped capacitors."""
    tokens = {t.id: t for t in planning_tokens(state)}
    held = set()
    for a in edits:
        kind, token_id = a[:2]
        t = tokens[token_id]
        if kind == 'shift':
            tokens[token_id] = replace(t, lane=t.lane + a[2])
        elif kind == 'hold':
            tokens[token_id] = replace(t, size=min(3, t.size + 1), held=1)
            held.add(token_id)
        elif kind == 'damp':
            tokens[token_id] = replace(t, size=t.size - 1)
    breached = [t for t in tokens.values() if t.id not in held and t.row == 0 and t.size > 0]
    matches = []
    for lane in range(3):
        positive = sum(t.size for t in breached if t.lane == lane and t.sign == 1)
        negative = sum(t.size for t in breached if t.lane == lane and t.sign == -1)
        matches.append(min(positive, negative) > 0)
    return tuple(matches)


def options(game: BridgeGame) -> list[tuple]:
    opts = simple_options(game.state, 'baseline')
    if game.link is None:
        for source, stored in enumerate(game.state.progress):
            if stored >= 1:
                for target in (source - 1, source + 1):
                    if 0 <= target < 3:
                        opts.append(('link', source, target))
    return opts


def step_bridge(game: BridgeGame, actions: tuple[tuple, ...] = ()) -> BridgeGame:
    s = game.state
    if s.over:
        raise ValueError('game ended')
    actions = tuple(tuple(a) for a in actions)
    if len(actions) > 4:
        raise ValueError('maximum four edits including LINK')
    links = [a for a in actions if a and a[0] == 'link']
    edits = tuple(a for a in actions if not (a and a[0] == 'link'))
    if len(links) > 1:
        raise ValueError('maximum one LINK activation')
    active = game.link
    if links:
        if active is not None or len(links[0]) != 3:
            raise ValueError('cannot buy while a bridge is active')
        _, src, dst = links[0]
        if (type(src) is not int or type(dst) is not int or
                not 0 <= src < 3 or not 0 <= dst < 3 or abs(src - dst) != 1 or
                s.progress[src] < 1):
            raise ValueError('LINK needs 1 source power and adjacent destination')
        progress = list(s.progress)
        progress[src] -= 1
        s = replace(s, progress=tuple(progress))
        active = Link(src, dst, 2)
    # Reference engine validates all original edits. The original state is
    # immutable and payments cannot be made from yet-unearned charge.
    result = step(s, edits)
    if active is not None:
        matched = collision_lanes(s, edits)[active.source]
        if matched:
            progress = list(result.progress)
            progress[active.target] = min(3, progress[active.target] + 1)
            result = replace(result, progress=tuple(progress))
            # Charging happens before checking target victory on round nine.
            if result.round == 9 and result.hp > 0:
                goal = min(progress) >= 2 and sum(progress) >= 8
                result = replace(result, over='win' if goal else 'loss: target')
        active = Link(active.source, active.target, active.remaining - 1)
        if active.remaining == 0:
            active = None
    if result.over:
        active = None
    return BridgeGame(result, active)
