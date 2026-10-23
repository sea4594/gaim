"""Count real action complementarities; diagnostic, NOT proof of multiplayer fun.

An independent player can do both edits in solo mode. Pair synergy measures
mechanical interaction only, not independent human agency or quarterbacking.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from itertools import combinations
from experiments.phase09_market import new,choose
from experiments.phase06_lab import opportunities
from experiments.phase08_survey import utility as trial_utility
from experiments.phase08_lab import Trial as Wrapper


def score(g):
    return trial_utility(Wrapper(g,'control'))


def probe(n=80,start=44000):
    c=Counter();example={};categories=Counter()
    for seed in range(start,start+n):
        g=new(seed,2)
        for draft in range(len(g.game.available)):
            default=choose(g,draft)
            baseline=score(default)
            pool=opportunities(g,draft)
            # Small, deterministic bounded pool. Both token and economy actions.
            seen=set();pool=[a for a in pool if a[0]!='pass' and not (a in seen or seen.add(a))]
            points={}
            for a in pool:
                try:points[a]=score(choose(g,draft,(a,)))
                except (ValueError,TypeError,IndexError,KeyError):pass
            c['single_actions']+=len(points)
            for a,b in combinations(points,2):
                try:two=choose(g,draft,(a,b))
                except (ValueError,TypeError,IndexError,KeyError):continue
                c['legal_pairs']+=1
                value=score(two)
                if points[a]<=baseline+1e-8 and points[b]<=baseline+1e-8 and value>baseline+1e-8:
                    c['strict_complements']+=1
                    c['states_with_complement_'+str(seed)]=1
                    kind='+'.join(sorted((a[0],b[0])))
                    categories[kind]+=1
                    if not example:
                        example={'seed':seed,'draft':draft,'actions':[a,b],
                                 'scores':{'pass':baseline,'first':points[a],
                                           'second':points[b],'both':value}}
    states_with=sum(1 for key in c if key.startswith('states_with_complement_'))
    clean={k:v for k,v in c.items() if not k.startswith('states_with_complement_')}
    clean['seeds_with_at_least_one_strict_complement']=states_with
    return {'seed_range':[start,start+n-1],'count':clean,'pair_categories':dict(categories),
            'example':example,'caveat':'Same-round heuristic only; a co-op pair can be executed by one solo player.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=80)
    x=p.parse_args();print(json.dumps(probe(x.cases),indent=2))
