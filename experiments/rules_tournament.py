"""Independent, opt-in mechanical experiments. Never imported by the production server.

Every experiment deliberately changes ONE core decision lever; all use the same
Charge Loom reference wavebook and the same deterministic round/terminal rules.
No player-count or human-fun claims are implied by the scripted tests.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Optional
from reference.charge_loom_v01 import State, Token, arrivals, TURNS

MODES = ('baseline', 'bridge', 'sweep', 'overcharge', 'contract', 'front', 'harmonic', 'bridge_sweep')

@dataclass(frozen=True)
class Bridge:
    source: int
    dest: int
    begins: int
    ends: int

@dataclass(frozen=True)
class Pledge:
    source: int
    dest: int
    due: int

@dataclass(frozen=True)
class Trial:
    state: State
    mode: str = 'baseline'
    bridge: Optional[Bridge] = None
    pledge: Optional[Pledge] = None
    front: int = 0    # Only modifies the NEXT arriving wave; -1 / +1 wrap
    waves: tuple | None = None  # Explicit nine-round schedules for research fixtures

    @classmethod
    def new(cls, mode: str, seed: int = 0) -> 'Trial':
        if mode not in MODES:
            raise ValueError('unknown mode')
        return cls(State(seed=seed), mode)


def incoming(t: Trial, r: int):
    return t.waves[r - 1] if t.waves is not None else arrivals(t.state.seed, r)

def planning_tokens(t: Trial) -> tuple[Token, ...]:
    s = t.state
    waves = incoming(t, s.round + 1)
    added = tuple(Token(s.next_id + ix, (lane + t.front) % 3, 2, sign, size)
                  for ix, (lane, sign, size) in enumerate(waves))
    return s.tokens + added


def actions(t: Trial) -> list[tuple]:
    """Individual candidate edits; combinations must obey per-round constraints."""
    s = t.state
    if s.over:
        return []
    out: list[tuple] = [('pass',)]
    for token in planning_tokens(t):
        if token.lane > 0:
            out.append(('shift', token.id, -1))
        if token.lane < 2:
            out.append(('shift', token.id, 1))
        if token.held == 0:
            out.append(('hold', token.id))
        if s.coolant > 0:
            out.append(('damp', token.id))
    if t.mode in ('bridge', 'bridge_sweep') and t.bridge is None:
        for src, power in enumerate(s.progress):
            if power:
                for dst in (src - 1, src + 1):
                    if 0 <= dst <= 2:
                        out.append(('bridge', src, dst))
    if t.mode in ('sweep', 'bridge_sweep') and s.coolant:
        for row in range(3):
            if any(tok.row == row for tok in planning_tokens(t)):
                out.extend([('sweep', row, -1), ('sweep', row, 1)])
    elif t.mode == 'overcharge':
        for lane, power in enumerate(s.progress):
            if power:
                out.append(('overcharge', lane))
    elif t.mode == 'contract' and t.pledge is None and s.round < TURNS - 1:
        for src in range(3):
            for dst in (src - 1, src + 1):
                if 0 <= dst <= 2:
                    out.append(('contract', src, dst))
    elif t.mode == 'front' and s.round < 7:
        out.extend([('front', -1), ('front', 1)])
    return out


def step_trial(t: Trial, planned: tuple[tuple, ...] | list[tuple] = ()) -> Trial:
    """Strict deterministic reducer, independent from the shipping v0.1 engine."""
    s = t.state
    if s.over:
        raise ValueError('game ended')
    planned = tuple(tuple(a) for a in planned)
    if len(planned) > 4:
        raise ValueError('maximum four shared edits')
    round_no = s.round + 1
    tokens = {token.id: token for token in planning_tokens(t)}
    orig_count = len(incoming(t, round_no))
    nid = s.next_id + orig_count
    spent = list(s.progress)
    coolant = s.coolant
    held = set()
    touched = set()
    special = None
    for a in planned:
        if not a:
            raise ValueError('empty action')
        kind = a[0]
        if kind == 'pass':
            if len(a) != 1:
                raise ValueError('bad pass')
            continue
        if kind in ('shift', 'hold', 'damp'):
            if len(a) != (3 if kind == 'shift' else 2) or type(a[1]) is not int:
                raise ValueError('bad token edit')
            ident = a[1]
            if ident not in tokens or ident in touched:
                raise ValueError('missing/double edited token')
            touched.add(ident)
            token = tokens[ident]
            if kind == 'shift':
                direction = a[2]
                if type(direction) is not int or direction not in (-1, 1) or not 0 <= token.lane + direction < 3:
                    raise ValueError('bad shift')
                token = replace(token, lane=token.lane + direction)
            elif kind == 'hold':
                if token.held:
                    raise ValueError('already held')
                token = replace(token, size=min(3, token.size + 1), held=1)
                held.add(ident)
            else:
                if coolant < 1:
                    raise ValueError('out of coolant')
                coolant -= 1
                token = replace(token, size=token.size - 1)
            tokens[ident] = token
            continue
        allowed = {t.mode} if t.mode != 'bridge_sweep' else {'bridge', 'sweep'}
        if special is not None or kind not in allowed:
            raise ValueError('wrong or duplicate special action')
        special = a
        if kind == 'bridge':
            if len(a) != 3 or t.bridge is not None or round_no >= TURNS:
                raise ValueError('invalid bridge')
            _, src, dst = a
            if type(src) is not int or type(dst) is not int or not (0 <= src < 3 and 0 <= dst < 3 and abs(src - dst) == 1) or spent[src] < 1:
                raise ValueError('bridge requires existing source energy and adjacent target')
            spent[src] -= 1
        elif kind == 'sweep':
            if len(a) != 3 or a[1] not in (0, 1, 2) or a[2] not in (-1, 1) or coolant < 1:
                raise ValueError('bad sweep')
            coolant -= 1
        elif kind == 'overcharge':
            if len(a) != 2 or a[1] not in (0, 1, 2) or spent[a[1]] < 1:
                raise ValueError('overcharge must spend preexisting energy')
            spent[a[1]] -= 1
        elif kind == 'contract':
            if len(a) != 3 or t.pledge is not None or round_no >= TURNS or not (a[1] in (0,1,2) and a[2] in (0,1,2) and abs(a[1] - a[2]) == 1):
                raise ValueError('bad public contract')
        elif kind == 'front':
            if len(a) != 2 or a[1] not in (-1, 1) or round_no >= 8:
                raise ValueError('bad front shift')
        else:
            raise ValueError('unknown edit')
    if special and special[0] == 'sweep':
        _, row, direction = special
        for ident, tok in list(tokens.items()):
            if tok.row == row and tok.size > 0:
                tokens[ident] = replace(tok, lane=(tok.lane + direction) % 3)
    good = [tok for tok in tokens.values() if tok.size > 0]
    moved = [tok if tok.id in held else replace(tok, row=tok.row - 1) for tok in good]
    breached = [tok for tok in moved if tok.row < 0]
    kept = tuple(sorted(tok for tok in moved if tok.row >= 0))
    hp = s.hp
    matched = [0,0,0]
    for lane in range(3):
        positive = sum(tok.size for tok in breached if tok.lane == lane and tok.sign == 1)
        negative = sum(tok.size for tok in breached if tok.lane == lane and tok.sign == -1)
        matched[lane] = min(positive, negative)
        hp -= abs(positive - negative)
        spent[lane] = min(3, spent[lane] + matched[lane])
    bridge = t.bridge
    if special and special[0] == 'bridge':
        bridge = Bridge(special[1], special[2], round_no + 1, round_no + 2)
    if bridge and bridge.begins <= round_no <= bridge.ends and matched[bridge.source] > 0:
        spent[bridge.dest] = min(3, spent[bridge.dest] + 1)
    if bridge and round_no >= bridge.ends:
        bridge = None
    pledge = t.pledge
    if pledge and pledge.due == round_no:
        if matched[pledge.source] > 0:
            spent[pledge.dest] = min(3, spent[pledge.dest] + 2)
        else:
            hp -= 1
        pledge = None
    if special and special[0] == 'contract':
        pledge = Pledge(special[1], special[2], round_no + 1)
    if special and special[0] == 'overcharge':
        lane = special[1]
        if matched[lane] >= 2:
            spent[lane] = min(3, spent[lane] + 2)
        else:
            hp -= 2
    if t.mode == 'harmonic' and sum(bool(x) for x in matched) >= 2:
        for lane, amount in enumerate(matched):
            if amount:
                spent[lane] = min(3, spent[lane] + 1)
    front = special[1] if special and special[0] == 'front' else 0
    if round_no == TURNS:
        hp -= sum(tok.size for tok in kept)
        kept = ()
        bridge = None
        pledge = None
    over = ''
    if hp <= 0:
        over = 'loss: breach'
    elif round_no == TURNS:
        over = 'win' if min(spent) >= 2 and sum(spent) >= 8 else 'loss: target'
    return Trial(State(round_no, hp, tuple(spent), coolant, kept, nid, s.seed, over), t.mode, bridge, pledge, front, t.waves)


def score(t: Trial) -> float:
    """Generic diagnostics only; not asserted to model human enjoyment."""
    s = t.state
    if s.over == 'win':
        return 1000 + max(s.hp, 0)
    if s.over.startswith('loss: breach'):
        return -1000
    # lost target is less bad than dead, but bad
    if s.over:
        return -100
    # Directly rewarded by arbitrary weights: cannot fairly compare win rates across modes.
    return 4 * max(s.hp, 0) + 7 * sum(s.progress) + 5 * min(s.progress) + s.coolant * 2
