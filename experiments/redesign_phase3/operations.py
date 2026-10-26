"""Full experimental Storm Operations: hands, owned orders, missions, recycling."""
from __future__ import annotations
import random
from copy import deepcopy
from .common import (enter, move_and_breach, resolve, token_by_id,
                     validate_token_edit, apply_edit, validate_waves)

ALL_MISSIONS = ('three_stations','double_pulse','deep_capture','clean_passage',
                'precision_route','last_moment_save')
DECK = ['LEFT']*2 + ['RIGHT']*2 + ['HOLD']*2 + ['FLIP'] + ['DAMP']*2


def new_game(waves, players, missions, seed=1, starting_hands=None):
    if not 1 <= players <= 4: raise ValueError('Players must be 1–4')
    validate_waves(waves, players)
    if len(set(missions)) != 3 or any(m not in ALL_MISSIONS for m in missions):
        raise ValueError('Exactly three unique missions required')
    hands=[]; decks=[]; discards=[]
    for seat in range(players):
        rng=random.Random(f'{seed}:{seat}')
        deck=DECK[:]; rng.shuffle(deck)
        if starting_hands is not None:
            wanted=starting_hands[seat]
            if len(wanted) != (4 if players==1 else 3): raise ValueError('Bad forced hand size')
            for card in wanted:
                if card not in deck: raise ValueError('Forced card not in deck')
                deck.remove(card)
            hands.append(wanted[:])
        else:
            take=4 if players==1 else 3
            hands.append([deck.pop() for _ in range(take)])
        decks.append(deck); discards.append([])
    return dict(round=1, waves=deepcopy(waves), players=players, seed=seed, board=[],
                hull=4+players, missions=list(missions), progress=dict(stations=[],
                pulses=0, deep=False, clean=0, precision=0, rescue=False),
                hands=hands, decks=decks, discards=discards, finished=None,
                history=[], played_by=[0]*players)


def _refill(s, seat, played):
    # Exactly as Phase 2: played cards join the discard only AFTER replacement draw.
    need = (4 if s['players']==1 else 3) - len(s['hands'][seat])
    rng = random.Random(f"{s['seed']}:{seat}:refill:{s['round']}")
    for _ in range(need):
        if not s['decks'][seat]:
            rng.shuffle(s['discards'][seat])
            s['decks'][seat], s['discards'][seat] = s['discards'][seat], []
        if not s['decks'][seat]: break
        s['hands'][seat].append(s['decks'][seat].pop())
    s['discards'][seat].extend(played)


def completed(s):
    p=s['progress']
    checks=dict(three_stations=len(p['stations'])==3,
                double_pulse=p['pulses']>=2, deep_capture=p['deep'],
                clean_passage=p['clean']>=3, precision_route=p['precision']>=2,
                last_moment_save=p['rescue'])
    return [m for m in s['missions'] if checks[m]]


def step(state, orders=None):
    """A round is simultaneously submitted by seat; orders is a list per seat.

    Each multiplayer seat submits [] or [ {kind,token} ]; solo may submit <=2.
    The engine validates the entire plan before processing; fizzle occurs only
    due to earlier legal actions on the same token.
    """
    if state['finished'] is not None: raise ValueError('Game ended')
    s=deepcopy(state); r=s['round']
    enter(s['board'], s['waves'][r-1], r)
    orders = orders if orders is not None else [[] for _ in range(s['players'])]
    if len(orders)!=s['players']: raise ValueError('Missing player orders')
    target_counts={}
    for seat, seat_orders in enumerate(orders):
        if len(seat_orders) > (2 if s['players']==1 else 1):
            raise ValueError('Too many orders per player')
        available=s['hands'][seat][:]
        for a in seat_orders:
            if a['kind'] not in DECK or a['kind'] not in available:
                raise ValueError('Missing card in hand')
            available.remove(a['kind'])
            validate_token_edit(s['board'], a)
            target_counts[a['token']]=target_counts.get(a['token'],0)+1
    if max(target_counts.values(),default=0)>2:
        raise ValueError('Max 2 orders per charge')
    before_near={t['id'] for t in s['board'] if t['depth']==1}
    modified=set(); fizzles=0
    seat_order = [(k+(r-1))%s['players'] for k in range(s['players'])]
    spent=[[] for _ in range(s['players'])]; stopped=set()
    for seat in seat_order:
        for action in orders[seat]:
            s['hands'][seat].remove(action['kind'])
            spent[seat].append(action['kind'])
            successful=apply_edit(s['board'],action,stopped,allow_fizzle=True)
            if successful: modified.add(action['token'])
            else: fizzles+=1
            s['played_by'][seat]+=1
    s['board'], breached=move_and_breach(s['board'],stopped)
    event=resolve(breached)
    p=s['progress']; matches=event['matches']; leaks=event['leaks']
    for lane in range(3):
        if matches[lane]>0 and lane not in p['stations']:
            p['stations'].append(lane)
    p['stations'].sort()
    if sum(m>0 for m in matches)>=2: p['pulses']+=1
    if max(matches)>=2: p['deep']=True
    if event['raw_damage']==0: p['clean']+=1
    else: p['clean']=0
    if matches[1]>0 and leaks[1]==0: p['precision']+=1
    if any(tid in modified and tid in before_near
           for ids in event['matched_ids'] for tid in ids):
        p['rescue']=True
    s['hull']-=event['raw_damage']
    deadline=0
    if r==8:
        deadline=sum(t['strength'] for t in s['board'])
        s['hull']-=deadline
    if s['hull']<=0: s['finished']='LOSS_HULL'
    elif r==8:
        s['finished']='WIN' if len(completed(s))>=2 else 'LOSS_MISSIONS'
    # Even the final round's played cards are discarded; no extra draw is needed.
    for seat in range(s['players']):
        if r < 8: _refill(s,seat,spent[seat])
        else: s['discards'][seat].extend(spent[seat])
    s['history'].append(dict(round=r,order=deepcopy(orders),seat_order=seat_order,
        matched=matches, leaks=leaks, hull=s['hull'], deadline=deadline,
        missions=completed(s), hands=[h[:] for h in s['hands']],
        fizzles=fizzles, played_by=s['played_by'][:], outcome=s['finished']))
    if s['finished'] is None: s['round']+=1
    return s


def play(waves,players,missions,decisions,seed=1,starting_hands=None):
    s=new_game(waves,players,missions,seed,starting_hands)
    while s['finished'] is None:
        s=step(s,decisions.get(s['round']))
    return s
