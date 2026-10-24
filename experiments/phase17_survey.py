"""Reproducible limited-lookahead Storm Weave diagnostic (not a fun metric)."""
from __future__ import annotations
import argparse,json,random
from collections import Counter
from experiments.phase15_survey import base_board,wave
from experiments.phase15_forecast_council import make_world,score,candidate_edits
from experiments.phase06_lab import step
from experiments.phase17_storm_weave import apply_weave


def follow(game,first,edit,horizon=4):
    actions=() if edit==('pass',) else (edit,)
    g=step(game,actions,draft=first)
    for i in range(horizon-1):
        if g.state.over:break
        g=step(g,(),draft=0)
    return g


def evaluate(game,horizon=4,action_limit=12):
    """Same legal initial actions offered to woven and original versions.

    Actions chosen by oracle one-round lookahead, then PASS policy. This gives
    a narrow diagnostic for when a costly reconfiguration matters, NOT a game
    win-rate or a realistic four-human planning strategy.
    """
    actions=list(candidate_edits(game))[:action_limit]
    original=[];woven=[]
    changed=apply_weave(game) if game.state.coolant else None
    for edit in actions:
        for first in (0,1):
            original.append((score(follow(game,first,edit,horizon)),first,edit))
            if changed:
                woven.append((score(follow(changed,first,edit,horizon)),first,edit))
    return max(original), max(woven) if woven else None


def survey(count=60,start=270100,horizon=4,action_limit=10):
    rng=random.Random(start);c=Counter();example=None
    for seed in range(start,start+count):
        base=base_board(seed)
        if base.state.coolant<1:
            c['unaffordable']+=1;continue
        w=make_world(base,wave(rng,2),wave(rng,2))
        b,a=evaluate(w,horizon,action_limit)
        if a is None:continue
        c['boards']+=1
        c['baseline_score']+=b[0];c['woven_score']+=a[0]
        if a[0]>b[0]+1e-8:
            c['weave_better']+=1
            if example is None:
                example={'seed':seed,'original':[w.game.deck[i] for i in w.game.available],
                         'baseline':b,'woven':a}
        elif a[0]<b[0]-1e-8:c['weave_worse']+=1
        else:c['same']+=1
    n=c['boards']
    return {'version':'pass-17/storm-weave-research',
            'sample':count,'start':start,'horizon':horizon,'initial_action_limit':action_limit,
            'evaluated':n,'weave_better':c['weave_better'],
            'weave_worse':c['weave_worse'],'same':c['same'],
            'unaffordable':c['unaffordable'],
            'mean_delta':round((c['woven_score']-c['baseline_score'])/n,4) if n else None,
            'witness':example,
            'limitations':['Synthetic replacement offers; not shipping procedural distribution',
                'Same restricted candidate action list, optimized with full knowledge of both cards',
                'All subsequent edits pass; no multi-player co-authorship tested',
                'Uses heuristic score, not verified full-game win probability',
                'Cooldown/cost modeled as one coolant; the simultaneous edit cost is not modeled']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=60)
    p.add_argument('--start',type=int,default=270100);p.add_argument('--horizon',type=int,default=4)
    args=p.parse_args()
    print(json.dumps(survey(args.count,args.start,args.horizon),indent=2,default=list))
