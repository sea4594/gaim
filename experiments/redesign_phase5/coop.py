"""Three competing, *separate* multiplayer structures over Storm Engine.

A. Owned Interventions: at most two charge edits, at most one per seat, and
   lane-qualified personal interventions.  This intentionally tests whether
   limited edits can sustain four-player action ownership, not new heroes.
B. Joint Investment: a proposing player picks infrastructure; a funding
   player picks standard (2 stored power, next-round activation) or rush
   (3 stored power, immediate activation).  Ownership changes by round.
C. Guarded Order: a second player declares a threshold-based backup DAMP;
   evaluate the guard after a primary edit but before charge movement.
   Both branches are committed simultaneously.  No invented uncertainty:
   evaluate the value of the guard *against sequential informed play*.

Each wrapper takes an independent engine state and returns a new state.
Validation is atomic (caller state never mutates), even on invalid plans.
"""
from __future__ import annotations
from copy import deepcopy
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.common import (apply_edit, enter, move_and_breach,
                                                 resolve, token_by_id, validate_token_edit)


def edit_board(state):
    """Public board just after deterministic current-round arrivals."""
    board = deepcopy(state['board'])
    enter(board, state['waves'][state['round']-1], state['round'])
    if state['pending'] is not None:
        # Pending upgrade affects engine's systems, not the charge board.
        pass
    return board


def owners(players, round_number):
    """Seat i has lane (i + round - 1) modulo 3; solo ignores restriction."""
    if not 1 <= players <= 4: raise ValueError('1-4 players only')
    if players == 4:
        # A duplicated lane is unavoidable: rotate which two seats share it.
        return tuple(((i-(round_number-1))%4)%3 for i in range(4))
    return tuple((i + round_number - 1) % 3 for i in range(players))


def owned_step(state, players, orders, *, ordinary_build=None):
    """Seat-owned action trial, max two *total* edits.

    `orders` maps zero-based seat indices to optional single edit. In solo,
    a list of up to two edits is allowed. All edits must be on a token in the
    personal seat's currently assigned lane (except solo).
    """
    lanes=owners(players,state['round'])
    if not isinstance(orders,dict): raise ValueError('Orders must be seat-indexed')
    if set(orders)-set(range(players)):raise ValueError('Invalid seat')
    actions=[]; board=edit_board(state)
    for seat, order in sorted(orders.items()):
        if order is None: continue
        picks=order if players==1 and isinstance(order,list) else [order]
        if len(picks)>(2 if players==1 else 1): raise ValueError('Too many personal actions')
        for a in picks:
            if not isinstance(a,dict):raise ValueError('Invalid action')
            token=token_by_id(board,a.get('token'))
            if token is None:raise ValueError('Unknown target')
            if players>1 and token['lane']!=lanes[seat]:
                raise ValueError('Intervention does not belong to personal lane')
            actions.append(a)
    if len(actions)>2:raise ValueError('Shared edit budget is two')
    result=engine.step(state,dict(edits=actions,build=ordinary_build))
    result['history'][-1]['owned_seats']=sorted(seat for seat,o in orders.items() if o)
    return result


def construction_seats(players, round_number):
    """Rotate who proposes and who funds; solo performs both roles."""
    if not 1<=players<=4:raise ValueError('1-4 players only')
    proposer=(round_number-1)%players
    financier=(proposer+1)%players if players>1 else proposer
    return proposer,financier


def joint_step(state, players, proposal, allocation, *, edits=(), free=None):
    """Build is jointly authored. Proposal is lane or None; allocation is
    `standard`, `rush` or None; missing one side means no build.

    Rush costs 3 pre-round stored power, immediately activates one system
    level before storm resolution. Standard costs 2 and activates next turn.
    Rush does not also incur the standard 2-power build; it is a substitute.
    All costs are paid before the round's collision power is generated.
    """
    proposer,financier=construction_seats(players,state['round'])
    if proposal is None and allocation is None:
        result=engine.step(state,dict(edits=list(edits),free=free))
        result['history'][-1]['joint']=None
        return result
    if proposal is None or allocation is None:raise ValueError('Both decisions required')
    if type(proposal) is not int or proposal not in (0,1,2):raise ValueError('Bad proposal')
    if allocation not in ('standard','rush'):raise ValueError('Bad allocation')
    # Enforce eligibility against the *current* round after pending upgrade.
    present=state['levels'][proposal]+int(state['pending']==proposal)
    if present>=2 or state['outages'][proposal]:raise ValueError('System unavailable')
    cost=2 if allocation=='standard' else 3
    if state['power']<cost:raise ValueError('Insufficient stored power')
    if allocation=='standard':
        result=engine.step(state,dict(edits=list(edits),free=free,build=proposal))
    else:
        s=deepcopy(state)
        s['power']-=3
        # Engine increments pending at round opening; rushed upgrade stacks.
        s['levels'][proposal]+=1
        result=engine.step(s,dict(edits=list(edits),free=free))
        result['history'][-1]['build']=proposal
        result['history'][-1]['rush_cost']=3
    result['history'][-1]['joint']={'proposer':proposer,'financier':financier,
                                   'target':proposal,'allocation':allocation}
    return result


def imminent_after_primary(state, primary):
    """Public incoming board after one committed edit, before movement."""
    board=edit_board(state)
    stopped=set()
    if primary is not None:
        validate_token_edit(board,primary)
        apply_edit(board,primary,stopped)
    _, breach=move_and_breach(board,stopped)
    return resolve(breach)


def guarded_step(state, players, primary, backup, condition, *, build=None):
    """Two seats commit before either decision is resolved.

    Backup is executed iff the threshold is reached in provisional resolution
    after primary edit: {'lane':0..2,'min_leak':1..3} OR
    {'lane':0..2,'min_match':1..3}. It costs one of the two edit slots only
    when triggered, and DAMP coolant is paid only if executed. Backup must
    be an ordinary valid charge edit and target a different token.

    A condition can be publicly calculated from both committed actions,
    making the mechanism particularly vulnerable to quarterbacking; compare
    against a second, fully informed human picking the action directly.
    """
    if not 2<=players<=4:raise ValueError('Guarded two-seat plan requires 2-4 players')
    if not isinstance(condition,dict) or set(condition)-{'lane','min_leak','min_match'}:
        raise ValueError('Invalid condition')
    lane=condition.get('lane')
    if type(lane) is not int or lane not in (0,1,2):raise ValueError('Invalid lane')
    modes=[k for k in ('min_leak','min_match') if k in condition]
    if len(modes)!=1 or type(condition[modes[0]]) is not int or not 1<=condition[modes[0]]<=3:
        raise ValueError('Exactly one legal threshold required')
    if backup is None or not isinstance(backup,dict):raise ValueError('Missing backup')
    board=edit_board(state)
    validate_token_edit(board,backup)
    if primary is not None:
        validate_token_edit(board,primary)
        if primary['token']==backup['token']:raise ValueError('Both edits target same charge')
    provisional=imminent_after_primary(state,primary)
    truth=(provisional['leaks'][lane] if modes[0]=='min_leak'
           else provisional['matches'][lane])>=condition[modes[0]]
    edits=([primary] if primary else [])+([backup] if truth else [])
    result=engine.step(state,dict(edits=edits,build=build))
    result['history'][-1]['guard']={'triggered':truth,'predicate':deepcopy(condition),
                                    'backup':deepcopy(backup)}
    return result
