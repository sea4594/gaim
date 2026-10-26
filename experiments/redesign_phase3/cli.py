"""Run both draft board games from a terminal, with no server/UI dependencies.

Usage:
  python -m experiments.redesign_phase3.cli --game engine --seed 5001
  python -m experiments.redesign_phase3.cli --game operations --players 3 --seed 7000
  python -m experiments.redesign_phase3.cli --game operations --players 4 --auto
Input is one JSON object per round (empty input = PASS). Errors let you retry.
"""
from __future__ import annotations
import argparse
import json
from . import engine, operations, survey


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',choices=('engine','operations'),required=True)
    p.add_argument('--seed',type=int)
    p.add_argument('--players',type=int,default=2)
    p.add_argument('--auto',action='store_true')
    p.add_argument('--style',choices=('dynamo_aegis','aegis_switchyard','dynamo_switchyard','no_build'),default='dynamo_aegis')
    args=p.parse_args()
    seed=args.seed if args.seed is not None else (5001 if args.game=='engine' else 7000)
    if args.game=='engine':
        waves=survey.engine_waves(seed)
        s=engine.new_game(waves)
        print('Storm Engine: input JSON {"edits":[],"build":0} or {} to pass')
    else:
        waves=survey.operations_waves(seed,args.players)
        s=operations.new_game(waves,args.players,
            ('deep_capture','precision_route','double_pulse'), seed)
        print('Storm Operations: input JSON array per player; e.g. [[{"kind":"LEFT","token":"r1t0"}],[]]')
    while s['finished'] is None:
        r=s['round']; arriving=waves[r-1]; forecast=waves[r] if r<8 else []
        print(f'\nROUND {r}/8, hull={s["hull"]}, incoming={arriving}, next={forecast}')
        print('Board:',[(t['id'],t['lane'],t['sign'],t['strength'],t['depth']) for t in s['board']])
        if args.game=='engine':
            print('Power:',s['power'],'Coolant:',s['coolant'],'Systems:',s['levels'],'Offline:',s['outages'])
            proposed=survey.engine_policy(s,args.style) if args.auto else {}
        else:
            print('Missions:',s['missions'],'Progress:',s['progress'])
            for seat,h in enumerate(s['hands']):print(f'Player {seat+1} hand:',h)
            proposed=survey.operations_policy(s) if args.auto else [[] for _ in range(args.players)]
        while True:
            if args.auto:
                decision=proposed
                print('AUTO decision:',json.dumps(decision))
            else:
                try:
                    raw=input('Submit JSON (blank = pass; quit to exit): ').strip()
                except EOFError:
                    return
                if raw.lower() in ('quit','exit'):return
                try:decision=json.loads(raw) if raw else proposed
                except json.JSONDecodeError as error:
                    print('Invalid JSON:',error);continue
            try:
                s=engine.step(s,decision) if args.game=='engine' else operations.step(s,decision)
                break
            except ValueError as error:
                print('Invalid plan:',error)
                if args.auto: raise
        e=s['history'][-1]
        print('Matched:',e['matched'],'Hull:',e['hull'],'Outcome:',e['outcome'] or 'CONTINUE')
    print('FINAL:',s['finished'],'Round:',s['round'],'Hull:',s['hull'])
    if args.game=='engine':print('Systems:',s['levels'],'Power:',s['power'])
    else:print('Missions:',operations.completed(s),'Individual actions:',s['played_by'])

if __name__=='__main__':main()
