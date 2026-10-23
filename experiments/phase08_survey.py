"""Pass 08 diagnostic tournament. Mechanical outcomes are NOT playtest fun scores.

Each mode uses its own legal-action, public-forecast aware greedy search. This
prevents the earlier error of benchmarking delayed rules with a planner that
cannot see them at all. Still a short-horizon heuristic, not a strong solver.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from dataclasses import replace
from experiments.phase08_lab import Trial, step, MODES
from experiments.phase06_lab import opportunities
from experiments.phase07_lab import demand_options


def utility(g):
    s=g.state
    if s.over=='win':return 1200+s.hp*3
    if s.over=='loss: breach':return -1200
    if s.over:return -300+sum(s.progress)*3
    score=8*s.hp+8*sum(s.progress)+5*min(s.progress)+2*s.coolant
    # Public-board formation heuristic: forecast-independent, no secret deck.
    # Rewards same-time, same-lane opposite charge; penalizes visible leaks.
    for band in range(3):
        for lane in range(3):
            positive=sum(t.size for t in s.tokens if t.row==band and t.lane==lane and t.sign==1)
            negative=sum(t.size for t in s.tokens if t.row==band and t.lane==lane and t.sign==-1)
            score+=(3-band)*(.9*min(positive,negative)-.15*abs(positive-negative))
    if g.council:
        score+=g.council.serviced*4
        # Public obligations alter the *marginal* value of preserving energy.
        # They are not hidden randomness.
        r=s.round+1
        if r<=3:lanes=(0,1)
        elif r<=6:lanes=(1,2)
        else:lanes=(2,0)
        score+=3*min(1,s.progress[lanes[0]]+s.progress[lanes[1]])
    return score


def demands(g):
    if not g.council:return (None,)
    opts=demand_options(g.council)
    return opts or (None,)


def choices(g, draft, edits, surge=False):
    for d in demands(g):
        try:yield d,step(g,edits,draft=draft,demand=d,surge=surge)
        except (ValueError,IndexError,TypeError):pass


def best_of(g,draft,edits,surge=False):
    return max(((utility(out),d,out) for d,out in choices(g,draft,edits,surge)),default=None,key=lambda x:x[0])


def plan(g):
    drafts=tuple(range(len(g.exp.game.available))) if g.exp.mode=='market' and g.state.round<7 else (None,)
    best=None
    situations=[(draft,False) for draft in drafts]
    if g.mode=='surge' and not g.surged and g.state.coolant and g.state.round<7 and len(g.exp.game.available)==2 and all(i<7 for i in g.exp.game.available):
        situations.append((0,True))
    for draft,surging in situations:
        found=best_of(g,draft,(),surging)
        if found is None:continue
        edits=[];score=found[0]
        for i in range(4):
            current=(score,None)
            exp=g.exp
            if surging:
                ids=exp.game.available
                deck=list(exp.game.deck)
                deck[ids[0]]=deck[ids[0]]+deck[ids[1]]
                exp=replace(exp,game=replace(exp.game,deck=tuple(deck)))
            pool=opportunities(exp,draft if draft is not None else 0)
            if g.mode=='repair' and not g.repaired and g.state.hp<7:
                pool+=[('repair',src) for src in range(3) if g.state.progress[src]>=2]
            for a in pool:
                if a in edits:continue
                result=best_of(g,draft,edits+[a],surging)
                if result and result[0]>current[0]+1e-8:current=(result[0],a)
            if current[1] is None:break
            edits.append(current[1]);score=current[0]
        result=best_of(g,draft,edits,surging)
        if result is None:continue
        candidate=(result[0],draft,tuple(edits),result[1],result[2],surging)
        if best is None or candidate[0]>best[0]+1e-8:best=candidate
    if best is None:raise RuntimeError('no valid action or draft')
    return best


def simulate(n=12,start=16000):
    answer={}
    for mode in MODES:
        c=Counter();verbs=Counter()
        for seed in range(start,start+n):
            g=Trial.new(mode,seed=seed)
            while not g.state.over:
                _,draft,edits,demand,out,surging=plan(g)
                c['rounds']+=1
                c['edits']+=len(edits)
                c['unused']+=4-len(edits)
                c['second_offer']+=draft==1
                verbs.update(a[0] for a in edits)
                g=out
            c['wins']+=g.state.over=='win';c['alive']+=g.state.hp>0
            c['final_hp']+=max(0,g.state.hp)
            c['final_power']+=sum(g.state.progress)
            c['paid_drafts']+=g.paid_drafts
            c['surges']+=g.surged
            if g.council:
                c['service']+=g.council.serviced;c['blackouts']+=g.council.blackouts
        answer[mode]={'totals':dict(c),'verbs':dict(verbs)}
    return {'games_per_mode':n,'seed_range':[start,start+n-1],
            'heuristic':'Greedy per-edit same-round utility; Council-aware; no 2+ turn search',
            'variants':answer}


def draft_tradeoff_probe(n=800,seed=115):
    """Synthetic public forecast states, compare free/newer vs paid/newer *same plan*.

    Designed to catch whether prices are always free advantages or actually
    impact downstream resource pools, not to rank fun or endgame solvability.
    """
    import random
    from reference.charge_loom_v01 import State,Token
    rng=random.Random(seed);results=Counter();examples=[]
    deck=(((0,-1,2),(1,1,1)),((1,-1,1),(2,1,2)),((0,1,1),(2,-1,2)),(),(),(),(),(),())
    for i in range(n):
        s=State(hp=rng.randint(1,7),progress=tuple(rng.randint(0,3) for _ in range(3)),
                coolant=rng.randint(0,3),seed=seed+i)
        tests={}
        for mode in ('control','coolant_bid','power_bid'):
            g=Trial.new(mode,state=s,waves=deck)
            try:
                a=step(g,draft=0)
                b=step(g,draft=1)
            except ValueError:
                results[mode+'_unavailable']+=1
                continue
            tests[mode]=(a,b)
            results[mode+'_compared']+=1
            delta=utility(b)-utility(a)
            results[mode+'_newer_better']+=delta>0
            results[mode+'_newer_worse']+=delta<0
            results[mode+'_newer_equal']+=delta==0
        if 'coolant_bid' in tests and 'control' in tests:
            ca,cb=tests['coolant_bid'];fa,fb=tests['control']
            if utility(fb)>utility(fa) and utility(cb)<utility(ca):
                results['coolant_cost_reverses_preference']+=1
                if len(examples)<2:
                    examples.append({'progress':s.progress,'coolant':s.coolant,
                                     'hp':s.hp,'free_scores':[utility(fa),utility(fb)],
                                     'paid_scores':[utility(ca),utility(cb)]})
    return {'sample':n,'counts':dict(results),'examples':examples,
            'caveat':'Round-one synthetic states and no edits. Public offered waves only; outcome score is a heuristic.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--games',type=int,default=12);p.add_argument('--start',type=int,default=16000)
    a=p.parse_args()
    print(json.dumps({'full_games':simulate(a.games,a.start),'tradeoff':draft_tradeoff_probe()},indent=2))
