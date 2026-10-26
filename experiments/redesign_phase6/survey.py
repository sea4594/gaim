"""Deterministic complete-session station-allocation stress test.

Agent has common public information and compares staffing patterns; it does
NOT simulate independent human preferences, private information, or enjoyment.
"""
from __future__ import annotations
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.common import enter, apply_edit, move_and_breach, resolve
from experiments.redesign_phase3.survey import engine_waves,engine_policy
from .crew import (STATIONS, FIXED, crew_step, staffed_step, fixed_assignment,
                   deterministic_assignment)

STRATEGIES=('dynamo_aegis','aegis_switchyard','dynamo_switchyard')


def roster_options():
    return tuple(x for x in itertools.product(range(3),repeat=4) if sum(x)==4)


def estimate_event(state,actions):
    board=[dict(t) for t in state['board']]
    enter(board,state['waves'][state['round']-1],state['round'])
    stopped=set()
    for a in actions: apply_edit(board,a,stopped)
    _,breached=move_and_breach(board,stopped)
    return resolve(breached)


def policy(state,staff,mode='dynamo_aegis'):
    """One simple predictable policy for BOTH control and flexible duties.

    Only current public board/wave is consulted; no future wave leakage.
    Attempts the existing tactical heuristic edits, with station constraints.
    """
    base=engine_policy(state,mode)
    nav=[];control=[];used=set()
    for a in base['edits']:
        if a['kind'] in ('SHIFT','HOLD') and len(nav)<staff[0]:
            nav.append(a);used.add(a['token'])
        elif a['kind'] in ('DAMP','HOLD') and len(control)<staff[1] and a['token'] not in used:
            control.append(a);used.add(a['token'])
    plan={}
    if nav:plan['nav']=nav
    if control:plan['control']=control
    total_cost=0
    if staff[2]>0:
        # Build goal is taken from the established Engine policy, but extra
        # engineer allows the same build at a discounted stored-power cost.
        goals={'dynamo_aegis':[0,0,1,1], 'aegis_switchyard':[1,1,2,2],
               'dynamo_switchyard':[0,0,2,2]}
        for target in goals[mode]:
            if state['levels'][target]+(state['pending']==target)<2:
                cost=1 if staff[2]==2 else 2
                if not state['outages'][target] and state['power']>=cost:
                    plan['engineer']={'build':target};total_cost=cost
                break
        if 'engineer' not in plan and state['power']>=1 and state['coolant']<=1:
            plan['engineer']={'service':True};total_cost=1
    left=state['power']-total_cost
    if staff[3]>0 and left>=1:
        event=estimate_event(state,nav+control)
        raw=event['leaks'];match=event['matches']
        offline=state['outages'][1]
        defense=state['levels'][1] if not offline else 0
        if sum(raw)>defense:
            pick=max(range(3),key=lambda i:raw[i])
            if raw[pick]>0:plan['dispatch']={'kind':'cover','lane':pick}
        elif state['coolant']<=1 and max(match)>0:
            pick=max(range(3),key=lambda i:match[i])
            plan['dispatch']={'kind':'recharge','lane':pick}
    return plan


def value(state):
    if state['finished']=='WIN':return 10000+state['hull']
    if state['finished']=='LOSS_HULL':return -10000+state['hull']
    if state['finished']=='LOSS_SYSTEMS':return -5000+state['hull']
    return (state['hull']*4 + state['power']*.9 + state['coolant']*.4
            +sum(state['levels'])*4 + int(state['pending'] is not None)*1.7
            -sum(state['outages'])*1.5)


def pick(state, mode, variant):
    if variant=='fixed':
        counts=FIXED
        return counts,policy(state,counts,mode)
    if variant!='flexible':raise ValueError('Unknown variant')
    # One-ply search compares all 19 staffing vectors; not an optimal planner.
    options=[]
    for counts in roster_options():
        plan=policy(state,counts,mode)
        try:result=crew_step(state,counts,plan)
        except ValueError:continue
        # Prefer spreading workers when state values tie, avoiding meaningless
        # crowding. This preference isn't added to the reported outcome.
        spread=sum(n>0 for n in counts)
        options.append((value(result),spread,counts,plan))
    if not options:raise RuntimeError('No valid staffing')
    _score,_spread,counts,plan=max(options,key=lambda x:(x[0],x[1],x[2]))
    return counts,plan


def play(seed,mode,variant,players=4,record=False):
    waves=engine_waves(seed);state=engine.new_game(waves)
    participation=[0]*players;active_rounds=[0]*players;role_counts=Counter();fully_active=0
    decisions=[]
    while state['finished'] is None:
        counts,plan=pick(state,mode,variant)
        assignment=(fixed_assignment(players,state['round']) if variant=='fixed'
                    else deterministic_assignment(counts,players,state['round']))
        # All seats submit work unit(s), even if a station passes this round.
        seat_activity=[any(s in plan for s in picks) for picks in assignment]
        fully_active+=int(all(seat_activity))
        for seat,picks in enumerate(assignment):
            participation[seat]+=sum(bool(plan.get(s)) for s in picks)
            active_rounds[seat]+=int(seat_activity[seat])
        for name,n in zip(STATIONS,counts):role_counts[name]+=n
        next_state=staffed_step(state,players,assignment,plan)
        if record:decisions.append({'staffing':counts,'assignment':assignment,'plan':plan})
        state=next_state
    return {'outcome':state['finished'],'hull':state['hull'], 'power':state['power'],
            'levels':state['levels'],'rounds':len(state['history']),
            'participation':participation,'active_seat_rounds':active_rounds,
            'all_seats_active_rounds':fully_active,
            'role_counts':dict(role_counts), 'waves':waves if record else None,
            'decisions':decisions if record else None}


def replay(waves,decisions,players):
    state=engine.new_game(waves)
    for record in decisions:
        if state['finished'] is not None:raise ValueError('Decisions after game finished')
        state=staffed_step(state,players,record['assignment'],record['plan'])
    if state['finished'] is None:raise ValueError('Incomplete replay')
    return state


def survey(start=231000,n=24):
    output={'start':start,'n':n,'method':('Paired 8-round public-wave games, same '
             'build targets; one-ply staffing planner. No independent human '
             'play, no unknown future or subjective satisfaction.')}
    for variant in ('baseline','fixed','flexible'):
        rows=[]
        for i in range(n):
            seed=start+i;mode=STRATEGIES[i%3]
            if variant=='baseline':
                state=engine.new_game(engine_waves(seed))
                while state['finished'] is None:
                    state=engine.step(state,engine_policy(state,mode))
                rows.append({'outcome':state['finished'],'hull':state['hull']})
            else:
                rows.append(play(seed,mode,variant))
        wins=sum(x['outcome']=='WIN' for x in rows)
        result={'wins':wins,'avg_hull':round(sum(x['hull'] for x in rows)/n,2)}
        if variant!='baseline':
            result['per_seat_active_rounds']=[sum(x['active_seat_rounds'][j] for x in rows) for j in range(4)]
            result['all_seats_active_rounds']=sum(x['all_seats_active_rounds'] for x in rows)
            result['played_rounds']=sum(x['rounds'] for x in rows)
            result['per_seat_staffed_actions']=[sum(x['participation'][j] for x in rows) for j in range(4)]
            result['total_roles']={s:sum(x['role_counts'].get(s,0) for x in rows) for s in STATIONS}
            result['wins_changed_vs_baseline']=sum((x['outcome']=='WIN') !=
                (engine_winner(start+i,STRATEGIES[i%3])) for i,x in enumerate(rows))
        output[variant]=result
    return output


def engine_winner(seed,mode):
    state=engine.new_game(engine_waves(seed))
    while state['finished'] is None:state=engine.step(state,engine_policy(state,mode))
    return state['finished']=='WIN'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--start',type=int,default=231000)
    parser.add_argument('--n',type=int,default=24);parser.add_argument('--output',type=Path)
    args=parser.parse_args();output=json.dumps(survey(args.start,args.n),indent=2)+'\n'
    if args.output:args.output.write_text(output)
    else:print(output)
