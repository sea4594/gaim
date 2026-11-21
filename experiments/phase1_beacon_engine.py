"""Independent Python reference for Gaim's improvement Phase 1 Beacon solo prototype.

The historical redesign_phase3.reducer is intentionally unchanged.
"""
from __future__ import annotations
from copy import deepcopy
from experiments.redesign_phase3.common import (enter, move_and_breach, resolve,
    token_by_id, validate_token_edit, apply_edit, validate_waves)


def new_game(waves):
    validate_waves(waves)
    return dict(round=1, waves=deepcopy(waves), board=[], hull=6, power=2,
                coolant=2, levels=[0, 0, 0], pending=None, outages=[False]*3,
                beacon=0, finished=None, history=[])


def step(state, plan=None):
    if state['finished'] is not None:
        raise ValueError('This match has already ended')
    s = deepcopy(state)
    r = s['round']; p = plan or {}; offline = s['outages'][:]
    if s['pending'] is not None:
        s['levels'][s['pending']] += 1
        s['pending'] = None
    enter(s['board'], s['waves'][r-1], r)
    edits = p.get('edits', []); build = p.get('build'); free = p.get('free')
    charge = p.get('charge', False); shield = p.get('shield', 0)
    if type(charge) is not bool: raise ValueError('Invalid Beacon flag')
    if type(shield) is not int or shield < 0 or shield > 2: raise ValueError('Invalid shield')
    if charge and build is not None: raise ValueError('Beacon and build are mutually exclusive')
    if charge and s['beacon'] >= 3: raise ValueError('Beacon is already charged')
    if charge and s['power'] < 2: raise ValueError('Not enough Power to charge Beacon')
    if s['power']-(2 if charge or build is not None else 0) < shield:
        raise ValueError('Not enough Power for the shield')
    if len(edits) > 2: raise ValueError('Too many edits')
    used = set(); damp_count = 0
    for a in edits:
        validate_token_edit(s['board'], a)
        if a['token'] in used: raise ValueError('Duplicate edit')
        used.add(a['token'])
        damp_count += a['kind'] == 'DAMP'
    if damp_count > s['coolant']: raise ValueError('Not enough coolant')
    if build is not None and (r == 8 or type(build) is not int or build not in (0,1,2)
        or s['power'] < 2 or s['levels'][build] >= 2 or offline[build]):
        raise ValueError('Construction unavailable')
    if free is not None:
        if s['levels'][2] == 0 or offline[2]: raise ValueError('Switchyard is unavailable')
        t = token_by_id(s['board'], free['token'])
        if t is None or (s['levels'][2] == 1 and t['depth'] != 2) or free.get('delta') not in (-1,1):
            raise ValueError('Invalid Switchyard move')
    if build is not None:
        s['power'] -= 2
        s['pending'] = build
    if charge:
        s['power'] -= 2
        s['beacon'] += 1
    s['power'] -= shield
    stopped = set()
    for a in edits:
        apply_edit(s['board'], a, stopped)
    if free is not None:
        t = token_by_id(s['board'], free['token'])
        if t is None or (s['levels'][2] == 1 and t['depth'] != 2):
            raise ValueError('Switchyard target no longer available')
        apply_edit(s['board'], dict(free, kind='SHIFT'), stopped)
    s['coolant'] -= damp_count
    s['board'], breached = move_and_breach(s['board'], stopped)
    event = resolve(breached)
    total_match = event['total_match']
    raw = event['raw_damage']
    bonus = s['levels'][0] if (s['levels'][0] > 0 and not offline[0] and
        ((s['levels'][0] == 1 and event['matches'][0] > 0) or
         (s['levels'][0] == 2 and total_match > 0))) else 0
    defense = shield * (1 if offline[1] else 1+s['levels'][1])
    damage = max(0, raw-defense)
    s['power'] = min(8, s['power']+total_match+bonus)
    s['hull'] -= damage
    s['outages'] = [v >= 2 for v in event['leaks']]
    deadline = 0
    if r == 8:
        deadline = sum(t['strength'] for t in s['board'])
        s['hull'] -= deadline
    if s['hull'] <= 0:
        s['finished'] = 'LOSS_HULL'
    elif r == 8:
        s['finished'] = 'WIN' if s['beacon'] == 3 and any(
            lv > 0 and not offline[i] for i, lv in enumerate(s['levels'])
        ) else 'LOSS_OBJECTIVE'
    s['history'].append(dict(round=r, edits=deepcopy(edits), build=build,
        charge=charge, shieldSpent=shield, free=deepcopy(free),
        matched=event['matches'], raw=event['leaks'], bonus=bonus,
        shield=defense, damage=damage, deadline=deadline, offline=offline,
        next_outages=s['outages'][:], hull=s['hull'], power=s['power'],
        beacon=s['beacon'], levels=s['levels'][:], outcome=s['finished']))
    if s['finished'] is None: s['round'] += 1
    return s
