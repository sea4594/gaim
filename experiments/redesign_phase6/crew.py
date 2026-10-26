"""Redesign Phase 6: fixed crew duties versus voluntary, combinable work crews.

This is an experimental *whole-round* reducer built on the Phase 3 settlement
engine. It keeps the eight-round storms and win conditions identical; changes
are explicitly limited to team work allocation and station effects.

Staffing always consists of FOUR work units, independent of player count.
For 1/2/3/4 humans the work units are partitioned [4], [2,2], [2,1,1],
[1,1,1,1] among seats, rotating the double duty for three people. Thus
increasing players never creates additional actions or resources.

Stations: NAV (SHIFT/HOLD), CONTROL (DAMP/HOLD), ENGINEER (build or
power->coolant service), and DISPATCH (pay stored power to cover damage or
recapture coolant from a collision). A station needs a staffed worker. A
second worker supports NAV/CONTROL by enabling a second edit, ENGINEER by
reducing a single build's cost by one, or DISPATCH by improving its capacity.
All orders and staffing are public; this is not a hidden-information test.
"""
from __future__ import annotations
from copy import deepcopy
from experiments.redesign_phase3 import engine

STATIONS=('nav','control','engineer','dispatch')
FIXED=(1,1,1,1)


def work_units(players, round_number):
    if type(players) is not int or not 1<=players<=4:raise ValueError('1..4 players required')
    if type(round_number) is not int or not 1<=round_number<=8:raise ValueError('Invalid round')
    if players==1:return (4,)
    if players==2:return (2,2)
    if players==3:
        assigned=[1,1,1];assigned[(round_number-1)%3]=2
        return tuple(assigned)
    return (1,1,1,1)


def staff_counts(assignment, players, round_number):
    """Explicit work orders by seat; repeated stations mean real support.

    `assignment` is a tuple of per-seat tuples. Each player's authorized
    work units must be accounted for; each station has capacity two.
    """
    capacities=work_units(players,round_number)
    if not isinstance(assignment,(tuple,list)) or len(assignment)!=players:
        raise ValueError('Staffing must include every seat')
    counts={k:0 for k in STATIONS}
    for seat,picks in enumerate(assignment):
        if not isinstance(picks,(tuple,list)) or len(picks)!=capacities[seat]:
            raise ValueError('Seat has incorrect work-unit allocation')
        for station in picks:
            if station not in counts:raise ValueError('Unknown station')
            counts[station]+=1
            if counts[station]>2:raise ValueError('No station supports more than two workers')
    return tuple(counts[k] for k in STATIONS)


def fixed_assignment(players,round_number):
    """Four duties distributed cyclically, not hard-coded to seat order."""
    caps=work_units(players,round_number)
    positions=STATIONS[(round_number-1)%4:]+STATIONS[:(round_number-1)%4]
    result=[];offset=0
    for n in caps:result.append(tuple(positions[offset:offset+n]));offset+=n
    return tuple(result)


def crew_step(state, staff, plan):
    """Resolve a complete public round with an explicit station staffing vector.

    `staff` counts by STATIONS, total 4; a source/game state never mutates.
    Omitted station orders are PASS. An engineer build and a dispatcher order
    must both afford their costs from *stored pre-round power*.
    """
    if state['finished'] is not None:raise ValueError('Game already ended')
    if len(staff)!=4 or any(type(n) is not int or n<0 or n>2 for n in staff) or sum(staff)!=4:
        raise ValueError('Exactly four workers, at most two per station')
    if not isinstance(plan,dict) or set(plan)-set(STATIONS):raise ValueError('Bad station orders')
    if any(k in plan and not isinstance(plan[k],list) for k in ('nav','control')):
        raise ValueError('Station edits must be lists')
    nav=list(plan.get('nav') or []);control=list(plan.get('control') or [])
    if any(not isinstance(a,dict) for a in nav+control):
        raise ValueError('Station edits must be action dictionaries')
    if len(nav)>staff[0] or len(control)>staff[1]:raise ValueError('Unstaffed tactical order')
    if any(a.get('kind') not in ('SHIFT','HOLD') for a in nav):raise ValueError('NAV only shifts or holds')
    if any(a.get('kind') not in ('DAMP','HOLD') for a in control):raise ValueError('CONTROL only damps or holds')
    actions=nav+control
    if len(actions)>2:raise ValueError('Two-edit engine capacity remains')
    if len({a['token'] for a in actions})!=len(actions):raise ValueError('Duplicate edit target')
    econ=plan.get('engineer');dispatch=plan.get('dispatch')
    if econ is not None and not staff[2]:raise ValueError('Engineer unstaffed')
    if dispatch is not None and not staff[3]:raise ValueError('Dispatch unstaffed')
    if econ is not None and (not isinstance(econ,dict) or set(econ)-{'build','service'}):
        raise ValueError('Invalid engineer order')
    if dispatch is not None and (not isinstance(dispatch,dict) or set(dispatch)!={'kind','lane'}):
        raise ValueError('Invalid dispatch order')
    original=deepcopy(state)
    build=None; cost=0;service=False
    if econ is not None:
        if set(econ)=={'build'}:
            build=econ['build']
            if type(build) is not int or build not in (0,1,2):raise ValueError('Invalid build lane')
            cost=1 if staff[2]==2 else 2
        elif econ=={'service':True}:
            cost=1;service=True
        else:raise ValueError('Invalid engineer operation')
    kind=None;lane=None; dispatch_cost=0
    if dispatch is not None:
        kind=dispatch['kind'];lane=dispatch['lane']
        if kind not in ('cover','recharge') or type(lane) is not int or lane not in (0,1,2):
            raise ValueError('Invalid dispatch choice')
        dispatch_cost=1
    if original['power']<cost+dispatch_cost:raise ValueError('Not enough pre-round stored power')
    if build is not None:
        if original['levels'][build]+int(original['pending']==build)>=2 or original['outages'][build]:
            raise ValueError('System ineligible for build')
    if service and original['coolant']>=3:raise ValueError('Coolant is full')
    # Normal build still costs 2 in the underlying reference reducer.
    # The extra engineer's build discount is represented by a one-power
    # credit before calling it, equivalent to spending only one real power.
    if build is not None and staff[2]==2:original['power']+=1
    original['power']-=dispatch_cost
    if service:
        original['power']-=1
        original['coolant']+=1
    out=engine.step(original,{'edits':actions,'build':build})
    event=out['history'][-1]
    if kind=='cover':
        blocked=min(event['raw'][lane],2+int(staff[3]==2))
        new_damage=max(0,sum(event['raw'])-blocked-event['shield'])
        saved=event['damage']-new_damage
        assert saved>=0
        out['hull']+=saved;event['damage']=new_damage;event['cover_saved']=saved
    elif kind=='recharge':
        recovered=(1+int(staff[3]==2)) if event['matched'][lane]>0 else 0
        old=out['coolant'];out['coolant']=min(3,out['coolant']+recovered)
        event['recharged']=out['coolant']-old
    # Recalculate terminal condition after reactive defense, accounting for
    # the already-applied end-of-round unresolved-charge deadline damage.
    if out['hull']<=0:out['finished']='LOSS_HULL'
    elif state['round']==8:
        offline=event['offline']
        out['finished']='WIN' if sum(level==2 and not offline[i] for i,level in enumerate(out['levels']))>=2 else 'LOSS_SYSTEMS'
    else:
        out['finished']=None
        # The underlying reducer may have terminated before cover saved the
        # hull. Restore the round advance it skipped on that provisional loss.
        out['round']=state['round']+1
    event['hull']=out['hull'];event['power']=out['power'];event['outcome']=out['finished']
    event['crew']={'staff':list(staff),'nav':deepcopy(nav),'control':deepcopy(control),
                   'engineer':deepcopy(econ),'dispatch':deepcopy(dispatch),
                   'cost':cost+dispatch_cost}
    return out


def staffed_step(state,players,assignment,orders):
    """Enforce per-seat work allocation independently of resolution."""
    staffing=staff_counts(assignment,players,state['round'])
    result=crew_step(state,staffing,orders)
    result['history'][-1]['crew']['assignment']=[list(x) for x in assignment]
    return result


def deterministic_assignment(staff, players, round_number):
    """Reproducible rotating allocation for a staffing vector (simulated team).

    Real participants choose their orders; this is an allocation *witness*,
    not a claim that a central solver reproduces their independent choices.
    """
    if sum(staff)!=4:raise ValueError('Four workers required')
    pool=[]
    for station,n in zip(STATIONS,staff):pool.extend([station]*n)
    pool=pool[(round_number-1)%4:]+pool[:(round_number-1)%4]
    caps=work_units(players,round_number)
    out=[];offset=0
    for count in caps:out.append(tuple(pool[offset:offset+count]));offset+=count
    assert staff_counts(out,players,round_number)==tuple(staff)
    return tuple(out)
