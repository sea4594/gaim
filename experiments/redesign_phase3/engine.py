"""Full 8-round experimental Storm Engine reducer (not production gameplay)."""
from __future__ import annotations
from copy import deepcopy
from .common import (enter, move_and_breach, resolve, token_by_id,
                     validate_token_edit, apply_edit, validate_waves)


def new_game(waves):
    validate_waves(waves)
    return dict(round=1, waves=deepcopy(waves), board=[], hull=6, power=2,
                coolant=2, levels=[0,0,0], pending=None, outages=[False]*3,
                finished=None, history=[])


def step(state, plan=None):
    """Atomic validation, then complete round resolution. Each step starts with arrival.

    Plan: {'edits': [{kind:SHIFT|HOLD|DAMP,token:'r1t0',delta:-1}],
           'build': lane number or None, 'free': {token,delta} or None}.
    """
    if state['finished'] is not None:
        raise ValueError('Game already ended')
    s = deepcopy(state); r = s['round']; plan = plan or {}
    offline = s['outages'][:]
    if s['pending'] is not None:
        s['levels'][s['pending']] += 1
        s['pending'] = None
    enter(s['board'], s['waves'][r-1], r)
    edits = plan.get('edits', []); build = plan.get('build')
    free = plan.get('free')
    if len(edits) > 2: raise ValueError('More than two paid edits')
    used = set(); damp_count = 0
    for a in edits:
        if a['kind'] not in ('SHIFT','HOLD','DAMP'): raise ValueError('Invalid Engine edit')
        validate_token_edit(s['board'], a)
        if a['token'] in used: raise ValueError('Duplicate paid-edit target')
        used.add(a['token']); damp_count += a['kind'] == 'DAMP'
    if s['coolant'] < damp_count: raise ValueError('Insufficient coolant')
    if build is not None:
        if type(build) is not int or build not in (0,1,2): raise ValueError('Invalid build')
        if s['power'] < 2 or s['levels'][build] >= 2 or offline[build]:
            raise ValueError('Build unavailable')
    if free is not None:
        if s['levels'][2] == 0 or offline[2]: raise ValueError('Switchyard unavailable')
        target = token_by_id(s['board'], free['token'])
        if target is None or target['depth'] != (2 if s['levels'][2] == 1 else target['depth']):
            raise ValueError('Switchyard target depth unavailable')
        if free.get('delta') not in (-1,1): raise ValueError('Invalid free shift direction')
        # Free shift validates at execution as paid edits may move the same token.
    if build is not None:
        s['power'] -= 2
        s['pending'] = build
    stopped = set()
    for a in edits:
        apply_edit(s['board'], a, stopped)
    if free is not None:
        target = token_by_id(s['board'], free['token'])
        if target is None: raise ValueError('Free shift target removed by edits')
        # Re-evaluate allowed depth and bound after paid edits.
        if s['levels'][2] == 1 and target['depth'] != 2: raise ValueError('Free shift requires FAR')
        apply_edit(s['board'], dict(free,kind='SHIFT'), stopped)
    s['coolant'] -= damp_count
    s['board'], breached = move_and_breach(s['board'], stopped)
    event = resolve(breached)
    raw = event['raw_damage']
    bonus = int(s['levels'][0] > 0 and not offline[0] and
                ((s['levels'][0] == 1 and event['matches'][0] > 0) or
                 (s['levels'][0] == 2 and event['total_match'] > 0)))
    defense = s['levels'][1] if not offline[1] else 0
    damage = max(0, raw - defense)
    s['power'] = min(8, s['power'] + event['total_match'] + bonus)
    s['hull'] -= damage
    s['outages'] = [v >= 2 for v in event['leaks']]
    deadline = 0
    if r == 8:
        deadline = sum(t['strength'] for t in s['board'])
        s['hull'] -= deadline
    if s['hull'] <= 0:
        s['finished'] = 'LOSS_HULL'
    elif r == 8:
        s['finished'] = 'WIN' if sum(l == 2 and not offline[i]
                        for i,l in enumerate(s['levels'])) >= 2 else 'LOSS_SYSTEMS'
    s['history'].append(dict(round=r, edits=deepcopy(edits), build=build,
             free=deepcopy(free), matched=event['matches'], raw=event['leaks'],
             bonus=bonus, shield=defense, damage=damage, deadline=deadline,
             offline=offline, next_outages=s['outages'][:], hull=s['hull'],
             power=s['power'], levels=s['levels'][:], outcome=s['finished']))
    if s['finished'] is None: s['round'] += 1
    return s


def play(waves, decisions):
    s = new_game(waves)
    while s['finished'] is None:
        s = step(s, decisions.get(s['round']))
    return s
