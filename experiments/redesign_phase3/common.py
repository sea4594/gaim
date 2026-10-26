"""Deterministic, transport-free primitives for the two *experimental* board games.

The two reducers are intentionally separate: sharing token accounting must not
silently force the games to share resource economies or cooperative structures.
"""
from __future__ import annotations
from copy import deepcopy

LANES = (0, 1, 2)


def validate_waves(waves, players=None):
    if len(waves) != 8:
        raise ValueError('Exactly eight rounds required')
    for round_index, wave in enumerate(waves):
        if players is not None and len(wave) != (players + 1 if round_index < 6 else 0):
            raise ValueError('Storm Operations wave count violates player scaling')
        for token in wave:
            if token['lane'] not in LANES or token['sign'] not in (-1, 1) or not 1 <= token['strength'] <= 3:
                raise ValueError('Invalid charge in incoming wave')


def enter(board, wave, r):
    for index, raw in enumerate(wave):
        board.append({**deepcopy(raw), 'id': f'r{r}t{index}', 'depth': 2, 'held': False})


def move_and_breach(board, stopped):
    breached, kept = [], []
    for original in board:
        t = dict(original)
        if t['id'] not in stopped:
            t['depth'] -= 1
        if t['depth'] == 0:
            breached.append(t)
        else:
            kept.append(t)
    return kept, breached


def resolve(breached):
    matches, leaks, ids = [0, 0, 0], [0, 0, 0], [[], [], []]
    for lane in LANES:
        tokens = [t for t in breached if t['lane'] == lane]
        positive = sum(t['strength'] for t in tokens if t['sign'] == 1)
        negative = sum(t['strength'] for t in tokens if t['sign'] == -1)
        matches[lane] = min(positive, negative)
        leaks[lane] = abs(positive - negative)
        if matches[lane]:
            ids[lane] = [t['id'] for t in tokens]
    return {'matches': matches, 'leaks': leaks, 'matched_ids': ids,
            'total_match': sum(matches), 'raw_damage': sum(leaks)}


def token_by_id(board, tid):
    return next((t for t in board if t['id'] == tid), None)


def validate_token_edit(board, action, allow_fizzle=False):
    kind = action['kind']; target = token_by_id(board, action['token'])
    if target is None:
        raise ValueError('Unknown token')
    if kind in ('LEFT', 'RIGHT', 'SHIFT'):
        dest = target['lane'] + (-1 if kind == 'LEFT' else 1 if kind == 'RIGHT' else int(action.get('delta', 0)))
        if dest not in LANES and not allow_fizzle:
            raise ValueError('Shift goes out of bounds')
    elif kind == 'HOLD':
        if target['held'] and not allow_fizzle:
            raise ValueError('Token already held')
    elif kind not in ('DAMP', 'FLIP'):
        raise ValueError('Unknown edit')


def apply_edit(board, action, stopped, allow_fizzle=False):
    token = token_by_id(board, action['token']); kind = action['kind']
    if token is None:
        return False if allow_fizzle else _error('Unknown target')
    if kind in ('LEFT', 'RIGHT', 'SHIFT'):
        dest = token['lane'] + (-1 if kind == 'LEFT' else 1 if kind == 'RIGHT' else int(action.get('delta', 0)))
        if dest not in LANES:
            return False if allow_fizzle else _error('Out of bounds')
        token['lane'] = dest
    elif kind == 'HOLD':
        if token['held']:
            return False if allow_fizzle else _error('Token already held')
        token['held'] = True
        token['strength'] = min(3, token['strength'] + 1)
        stopped.add(token['id'])
    elif kind == 'DAMP':
        token['strength'] -= 1
        if token['strength'] == 0:
            board.remove(token)
    elif kind == 'FLIP':
        token['sign'] *= -1
    else:
        _error('Unknown edit')
    return True


def _error(s):
    raise ValueError(s)
