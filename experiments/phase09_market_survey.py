"""Same short-horizon policy for 1/2/3 storm offers; no human play claims."""
from __future__ import annotations
import argparse,json
from collections import Counter
from experiments.phase09_market import new,choose
from experiments.phase06_lab import opportunities
from experiments.phase08_survey import utility as trial_utility
from experiments.phase08_lab import Trial


def utility(g):
    return trial_utility(Trial(g,'control'))


def plan(g):
    best=None
    for d in (range(len(g.game.available)) if g.state.round<7 else (None,)):
        actions=[]
        curr=utility(choose(g,d))
        for _ in range(4):
            best_action=None;best_score=curr
            for a in opportunities(g,d if d is not None else 0):
                if a in actions or a[0]=='pass':continue
                try:candidate=choose(g,d,actions+[a])
                except (ValueError,IndexError,TypeError,KeyError):continue
                value=utility(candidate)
                if value>best_score+1e-9:best_action=a;best_score=value
            if best_action is None:break
            actions.append(best_action);curr=best_score
        result=(curr,d,tuple(actions))
        if best is None or result[0]>best[0]+1e-9:best=result
    return best[1],best[2]


def tournament(n=16,start=31000):
    results={}
    for width in (1,2,3):
        c=Counter();first=[]
        for seed in range(start,start+n):
            g=new(seed,width)
            while not g.state.over:
                d,actions=plan(g)
                if g.state.round==0:first.append((d,actions))
                c['draft_nonold']+=d is not None and d!=0;c['edits']+=len(actions);c['rounds']+=1
                g=choose(g,d,actions)
            c['wins']+=g.state.over=='win'
            c['alive']+=g.state.hp>0
            c['power']+=sum(g.state.progress)
            c['hp']+=max(0,g.state.hp)
        results[width]=dict(c)
    return {'seeds':[start,start+n-1], 'runs':results,
            'policy':'Identical one-round greedy objective, four sequential edits for each forecast choice',
            'warning':'More offers can simply make a game easier, while also increasing option-count and screen complexity.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--games',type=int,default=16)
    x=p.parse_args();print(json.dumps(tournament(x.games),indent=2))
