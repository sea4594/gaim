"""Phase 4 adversarial selection: preregistered strategies and matched seeds.

This is a deterministic rules diagnostic, never a measurement of human fun.
The model measures strategy sensitivity, action engagement, passive mission
completion, and what happens when a teammate stops contributing.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import argparse
import json
from pathlib import Path
from experiments.redesign_phase3 import engine, operations
from experiments.redesign_phase3.survey import (
    engine_waves, operations_waves, engine_policy, operations_policy,
)
from experiments.redesign_phase3.common import enter

ENGINE_PATHS = ('dynamo_aegis', 'aegis_switchyard', 'dynamo_switchyard')
MISSIONS = ('deep_capture', 'precision_route', 'double_pulse')


def run_engine(seed, path, use_free=False):
    s = engine.new_game(engine_waves(seed))
    free_used = 0
    while not s['finished']:
        p = engine_policy(s, path)
        if use_free:
            p = with_best_free(s, p)
            free_used += int(p.get('free') is not None)
        s = engine.step(s, p)
    return s, free_used


def with_best_free(s, p):
    """Value a *legal* free Switchyard shift after the paid plan has been chosen.

    Only evaluate cases in which Switchyard is already built at round start.
    Immediate evaluation is deliberately imperfect; report it as an ablation,
    not as optimal use of Switchyard's future possibilities.
    """
    if s['levels'][2] == 0 or s['outages'][2]:
        return p
    board = deepcopy(s['board']); enter(board,s['waves'][s['round']-1],s['round'])
    # The draft's paid edits may remove or shift targets. Let the reducer decide.
    def val(out):
        h = out['history'][-1]
        return 10*out['hull'] + 1.5*sum(h['matched']) + .5*out['power'] - .03*len(out['board'])
    try:
        baseline = val(engine.step(s, p))
    except ValueError:
        return p
    winner = p
    # A free shift may SUBSTITUTE for a paid SHIFT rather than simply add to
    # an already well-protected plan. Compare exact legal continuations with
    # zero, one, or both proposed paid edits while holding the build choice.
    original_edits=p.get('edits',[])
    reduced=[[], *[[a] for a in original_edits],original_edits]
    best_utility=baseline - .025*len(original_edits)
    for t in board:
        if s['levels'][2] == 1 and t['depth'] != 2:
            continue
        for delta in (-1,1):
            if not 0<=t['lane']+delta<=2:
                continue
            for edits in reduced:
                trial={**p,'edits':edits,'free':{'token':t['id'],'delta':delta}}
                try: candidate=val(engine.step(s,trial)) - .025*len(edits)
                except ValueError:continue
                if candidate>best_utility+1e-9:
                    best_utility=candidate;winner=trial
    return winner


def run_ops(seed, n, skip=None, pass_all=False):
    s=operations.new_game(operations_waves(seed,n),n,MISSIONS,seed)
    rounds_of_idle=[0]*n
    while not s['finished']:
        p=operations_policy(s) if not pass_all else [[] for _ in range(n)]
        if skip is not None:p[skip]=[]
        for seat,act in enumerate(p):
            if not act: rounds_of_idle[seat] += 1
        s=operations.step(s,p)
    return s, rounds_of_idle


def run_tournament(n=40, start=91000):
    assert n>=1
    results={'methodology':{
      'seeds': f'{start}..{start+n-1}',
      'warning': 'Independent experimental scenario generators. Never compare raw wins between different games.',
      'policies': 'Engine reactive two-edit with/without greedy Switchyard free use; Operations sequential reactive hand-aware with per-seat dropouts.',
      'human_playtests': 0
    },'engine':{},'operations':{}}
    engine_runs={}
    for path in ENGINE_PATHS:
        base=[run_engine(i,path,False)[0] for i in range(start,start+n)]
        improved=[run_engine(i,path,True) for i in range(start,start+n)]
        engine_runs[path]=base
        results['engine'][path]={
          'baseline_wins':sum(s['finished']=='WIN' for s in base),
          'free_policy_wins':sum(s['finished']=='WIN' for s,k in improved),
          'free_shifts':sum(k for s,k in improved),
          'free_helped':sum(b['finished']!='WIN' and s['finished']=='WIN' for b,(s,k) in zip(base,improved)),
          'free_hurt':sum(b['finished']=='WIN' and s['finished']!='WIN' for b,(s,k) in zip(base,improved)),
          'average_final_hull':round(sum(s['hull'] for s in base)/n,2),
        }
    results['engine']['pairwise']={
        f'{a}_vs_{b}':{
          'both_win':sum(x['finished']==y['finished']=='WIN' for x,y in zip(engine_runs[a],engine_runs[b])),
          'only_first_wins':sum(x['finished']=='WIN' and y['finished']!='WIN' for x,y in zip(engine_runs[a],engine_runs[b])),
          'only_second_wins':sum(x['finished']!='WIN' and y['finished']=='WIN' for x,y in zip(engine_runs[a],engine_runs[b]))
        }
        for a,b in [('aegis_switchyard','dynamo_switchyard'),('dynamo_aegis','aegis_switchyard')]
    }
    for count in (1,2,3,4):
        active=[run_ops(i,count) for i in range(start,start+n)]
        passive=[run_ops(i,count,pass_all=True) for i in range(start,start+n)]
        drops={seat:[run_ops(i,count,skip=seat)[0] for i in range(start,start+n)] for seat in range(count)}
        results['operations'][str(count)]={
          'active_wins':sum(s['finished']=='WIN' for s,_ in active),
          'pass_wins':sum(s['finished']=='WIN' for s,_ in passive),
          'pass_completed_two_missions':sum(len(operations.completed(s))>=2 for s,_ in passive),
          'pass_completed_deep':sum(s['progress']['deep'] for s,_ in passive),
          'pass_completed_precision':sum(s['progress']['precision']>=2 for s,_ in passive),
          'active_player_actions':[sum(s['played_by'][seat] for s,_ in active) for seat in range(count)],
          'idle_seat_rounds':[sum(idle[seat] for s,idle in active) for seat in range(count)],
          'active_wins_with_any_zero_card_seat':sum(s['finished']=='WIN' and any(x==0 for x in s['played_by']) for s,_ in active),
          'drop_one_seat_wins':{str(seat):sum(s['finished']=='WIN' for s in states) for seat,states in drops.items()},
          'drop_one_seat_turned_win_to_loss':{str(seat):sum(orig[0]['finished']=='WIN' and other['finished']!='WIN' for orig,other in zip(active,states)) for seat,states in drops.items()},
          'drop_one_seat_turned_loss_to_win':{str(seat):sum(orig[0]['finished']!='WIN' and other['finished']=='WIN' for orig,other in zip(active,states)) for seat,states in drops.items()},
          'average_hull':round(sum(s['hull'] for s,_ in active)/n,2)
        }
    return results


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--n',type=int,default=40);a.add_argument('--start',type=int,default=91000);a.add_argument('--output',type=Path)
    args=a.parse_args(); output=json.dumps(run_tournament(args.n,args.start),indent=2)+'\n'
    if args.output:args.output.write_text(output)
    else:print(output)
