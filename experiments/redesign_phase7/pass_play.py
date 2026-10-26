"""Minimal full-eight-round pass-and-play CLI for HUMAN phase-7 playtests.

Uses exact experimental Phase 6 rules. No online functionality, no new powers.
Record is a replayable JSON file; do not treat scripted agents as humans.
Usage: python3 -m experiments.redesign_phase7.pass_play --players 4 --seed 7001 --out /tmp/crew-session.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.common import enter,validate_token_edit
from experiments.redesign_phase3.survey import engine_waves
from experiments.redesign_phase6.crew import STATIONS,work_units,staffed_step


def incoming_board(state):
    board=[dict(t) for t in state['board']]
    enter(board,state['waves'][state['round']-1],state['round'])
    return board


def edit_options(board,station,used,coolant,round_number):
    choices=[]
    for token in board:
        if token['id'] in used:continue
        tid=token['id']; kinds=['SHIFT','HOLD'] if station=='nav' else ['DAMP','HOLD']
        for kind in kinds:
            if kind=='DAMP' and coolant<=0:continue
            if kind=='HOLD' and round_number>=8:continue
            for delta in ((-1,1) if kind=='SHIFT' else (None,)):
                action={'kind':kind,'token':tid}
                if delta is not None:action['delta']=delta
                try:validate_token_edit(board,action)
                except ValueError:continue
                choices.append(action)
    return choices


def ask(message, options, read=input, write=print):
    """One indexed selection, including explicit PASS when in the menu."""
    if not options:raise ValueError('No choices')
    while True:
        write(message)
        for i,(_,label) in enumerate(options):write(f'  {i}. {label}')
        raw=read('Choice: ').strip()
        if raw.lower() in ('q','quit'):raise KeyboardInterrupt('Playtest quit')
        if raw.isdigit() and int(raw)<len(options):return options[int(raw)][0]
        write('Enter a displayed number, or q to stop.')


def choose_staff(state,players,read=input,write=print):
    assignment=[];counts={s:0 for s in STATIONS}
    for seat,units in enumerate(work_units(players,state['round'])):
        picks=[]
        for unit in range(units):
            allowed=[(s,s.title()) for s in STATIONS if counts[s]<2]
            station=ask(f'Player {seat+1}, work unit {unit+1}/{units}: choose one duty.',allowed,read,write)
            picks.append(station);counts[station]+=1
        assignment.append(tuple(picks))
    return tuple(assignment)


def choose_orders(state,assignment,read=input,write=print):
    """Stations have only their Phase 6 actions; no invented browser powers."""
    counts={s:sum(picks.count(s) for picks in assignment) for s in STATIONS}
    board=incoming_board(state)
    write('Visible charges (includes current arriving wave):')
    for t in board:write(f'  {t["id"]}: lane {t["lane"]} depth {t["depth"]} {"+" if t["sign"]==1 else "-"}{t["strength"]}')
    plan={};used=set();damps=0
    # Each tactical worker may make one edit, but at most TWO paid edits total.
    for seat,picks in enumerate(assignment):
        for station in picks:
            if station not in ('nav','control'):continue
            if len(used)>=2:write('Tactical engine limit: two edits; this worker must pass.');continue
            choices=edit_options(board,station,used,state['coolant']-damps,state['round'])
            items=[(None,'PASS')] + [(a,str(a)) for a in choices]
            action=ask(f'Player {seat+1}, {station.title()} action:',items,read,write)
            if action:
                plan.setdefault(station,[]).append(action);used.add(action['token'])
                damps+=int(action['kind']=='DAMP')
    eng_seat=next((seat for seat,picks in enumerate(assignment) if 'engineer' in picks),None)
    dispatch_seat=next((seat for seat,picks in enumerate(assignment) if 'dispatch' in picks),None)
    cost=0
    if eng_seat is not None:
        cost=1 if counts['engineer']==2 else 2
        choices=[(None,'PASS')]
        for i,name in enumerate(('Dynamo','Aegis','Switchyard')):
            if state['levels'][i]+(state['pending']==i)<2 and not state['outages'][i] and state['power']>=cost:
                choices.append(({'build':i},f'BUILD {name}, {cost} power'))
        if state['coolant']<3 and state['power']>=1:
            choices.append(({'service':True},'SERVICE: 1 power → 1 coolant'))
        order=ask(f'Player {eng_seat+1}, Engineer choice (another engineer supports if present):',choices,read,write)
        if order:
            plan['engineer']=order
            cost=1 if order.get('service') else cost
        else:cost=0
    if dispatch_seat is not None:
        items=[(None,'PASS')]
        if state['power']-cost>=1:
            items += [({'kind':'cover','lane':i},f'COVER {name}, 1 power') for i,name in enumerate(('Left','Center','Right'))]
            items += [({'kind':'recharge','lane':i},f'RECHARGE on {name} collision, 1 power') for i,name in enumerate(('Left','Center','Right'))]
        order=ask(f'Player {dispatch_seat+1}, Dispatch choice (another dispatcher supports if present):',items,read,write)
        if order:plan['dispatch']=order
    return plan


def run(players=4,seed=7001,read=input,write=print):
    state=engine.new_game(engine_waves(seed)); transcript=[]
    while state['finished'] is None:
        write(f'\nROUND {state["round"]}  |  HULL {state["hull"]}  POWER {state["power"]}  COOLANT {state["coolant"]}  UPGRADES {state["levels"]}')
        write('Upcoming public storm: '+repr(state['waves'][state['round']-1]))
        assignment=choose_staff(state,players,read,write)
        plan=choose_orders(state,assignment,read,write)
        previous_round=state['round']
        state=staffed_step(state,players,assignment,plan)
        event=state['history'][-1]
        transcript.append({'round':previous_round,'assignment':[list(x) for x in assignment],
                           'orders':plan, 'hull':state['hull'],'power':state['power'],
                           'result':state['finished']})
        write(f'RESULT: matched {event["matched"]}, hull {state["hull"]}, power {state["power"]}, pending {state["pending"]}')
    write(f'FINAL RESULT: {state["finished"]} after {len(transcript)} rounds')
    return {'prototype':'redesign/phase7-pass-play','seed':seed,'players':players,
            'waves':engine_waves(seed),'decisions':transcript,'outcome':state['finished']}


def replay(record):
    state=engine.new_game(record['waves'])
    for row in record['decisions']:
        if state['round']!=row['round']:raise ValueError('Replay round mismatch')
        state=staffed_step(state,record['players'],row['assignment'],row['orders'])
        if (state['hull'],state['power'],state['finished'])!=(row['hull'],row['power'],row['result']):
            raise ValueError('Replay mismatch')
    if state['finished']!=record['outcome']:raise ValueError('Outcome mismatch')
    return state


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--players',type=int,default=4,choices=range(1,5))
    parser.add_argument('--seed',type=int,default=7001)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--verify',type=Path,help='Verify exact saved decisions instead of playing')
    args=parser.parse_args()
    if args.verify:
        game=replay(json.loads(args.verify.read_text()))
        print('Verified full/partial session:',game['finished'],len(game['history']));return
    try:record=run(args.players,args.seed)
    except KeyboardInterrupt:print('\nStopped; no game saved.');return
    if args.out:
        args.out.write_text(json.dumps(record,indent=2)+'\n');print('Recorded session:',args.out)

if __name__=='__main__':main()
