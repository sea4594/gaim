"""Mission tournament. Explicitly distinguishes mechanical possibility from fun.

Most comparisons enumerate final-round actions, not full-game optimal solutions.
A one-round lookahead must not be sold as a replayability or multiplayer proof.
"""
from __future__ import annotations
import argparse, json, random
from collections import Counter
from itertools import combinations
from reference.charge_loom_v01 import State,Token
from experiments.phase09_lab import MISSIONS,Trial,step,mission_offers
from experiments.phase06_lab import opportunities
from experiments.phase08_survey import utility as control_utility


def _end(g, plan):
    try:
        return step(g, plan)
    except (ValueError, TypeError, IndexError, KeyError):
        return None


def small_plans(g, max_actions=1):
    """All legal plans up to one edit, or bounded two edits; no false win inference."""
    pool = [a for a in opportunities(g.exp) if a[0] != 'pass']
    plans = [()]
    plans.extend((a,) for a in pool)
    if max_actions >= 2:
        plans.extend(combinations(pool,2))
    result = {}
    for p in plans:
        outcome = _end(g,p)
        if outcome is not None:
            result[p] = outcome
    return result


def finish_probe(cases=260,seed=90172,max_actions=1):
    rng=random.Random(seed)
    results=Counter(); examples={}
    for index in range(cases):
        count=rng.randrange(2,5)
        tok=tuple(Token(i+1,rng.randrange(3),rng.choice((0,0,1)),
                        rng.choice((-1,1)),rng.choice((1,1,2))) for i in range(count))
        s=State(round=8,hp=rng.randrange(2,8),progress=tuple(rng.randrange(4) for _ in range(3)),
                coolant=rng.randrange(4), tokens=tok,next_id=count+1,seed=seed+index)
        history={'large_mask':rng.randrange(8), 'lane_mask':rng.randrange(8),
                 'synchronized':rng.randrange(3)}
        waves=((),)*9
        goals={m:Trial.new(m,seed=seed+index,state=s,waves=waves,**history) for m in MISSIONS}
        # All missions see the same legal moves and physical resolution;
        # only explicit history and terminal predicates differ.
        outcomes={m:small_plans(g,max_actions) for m,g in goals.items()}
        wins={m:{p for p,v in opts.items() if v.state.over=='win'} for m,opts in outcomes.items()}
        results['states']+=1
        for m in MISSIONS:
            results[m+'_winnable']+=bool(wins[m])
        for m in MISSIONS[1:]:
            a,b=wins['grid'],wins[m]
            results[m+'_both_winnable']+=bool(a and b)
            results[m+'_disjoint_winning_plans']+=bool(a and b and not (a&b))
            results[m+'_only_mission_winnable']+=bool(b and not a)
            results[m+'_only_grid_winnable']+=bool(a and not b)
            if a and b and not (a&b) and m not in examples:
                examples[m]={'power':s.progress,'hp':s.hp,'coolant':s.coolant,
                             'tokens':[(t.lane,t.row,t.sign,t.size) for t in tok],
                             'history':history,'grid_plan':next(iter(sorted(a))),
                             'mission_plan':next(iter(sorted(b)))}
    return {'cases':cases,'seed':seed,'max_edits':max_actions,
            'counts':dict(results),'exact_disjoint_examples':examples,
            'limitations':'Synthetic final states and invented plausible prior achievement history. No estimate of human fun or 9-round solvability.'}


def _score(g):
    """Same core utility, with explicit mission pressure; evaluates partial missions."""
    s=g.state
    if s.over=='win':return 2500+10*s.hp
    if s.over=='loss: breach':return -2500
    if s.over:return -900+4*s.hp+sum(s.progress)*4
    value=control_utility(type('ForUtility',(),{'state':s,'council':None})())
    if g.mission=='fortress':value+=12*min(s.hp,6)
    elif g.mission=='voltage':value+=18*g.large_mask.bit_count()
    elif g.mission=='concord':value+=15*min(g.synchronized,2)
    elif g.mission=='circuit':value+=12*g.lane_mask.bit_count()
    return value


def _choice(g):
    best=None
    drafts=range(len(g.exp.game.available)) if g.exp.mode=='market' and g.state.round<7 else (None,)
    for d in drafts:
        baseline=step(g,draft=d)
        chosen=[]; curr=_score(baseline)
        for _ in range(4):
            a_best=None;v_best=curr
            for a in opportunities(g.exp,d if d is not None else 0):
                if a in chosen or a[0]=='pass':continue
                try: nxt=step(g,chosen+[a],draft=d)
                except (ValueError,TypeError,IndexError):continue
                val=_score(nxt)
                if val>v_best+1e-8:a_best=a;v_best=val
            if a_best is None:break
            chosen.append(a_best);curr=v_best
        candidate=(curr,d,tuple(chosen))
        if best is None or candidate[0]>best[0]+1e-8:best=candidate
    if best is None:raise RuntimeError('no plan')
    return best[1],best[2]


def games(n=16,start=27100):
    out={}
    for mission in MISSIONS:
        c=Counter(); opening=[]
        for seed in range(start,start+n):
            g=Trial.new(mission,seed=seed)
            while not g.state.over:
                draft,actions=_choice(g)
                if g.state.round==0:opening.append((draft, actions))
                c['edits']+=len(actions);c['rounds']+=1
                c.update(('use_'+a[0] for a in actions))
                g=step(g,actions,draft=draft)
            c['wins']+=g.state.over=='win';c['survival']+=g.state.hp>0
            c['power']+=sum(g.state.progress);c['hp']+=max(0,g.state.hp)
        out[mission]={'counts':dict(c),'first_round_plans':opening}
    different={}
    for mission in MISSIONS[1:]:
        different[mission]=sum(out['grid']['first_round_plans'][i]!=out[mission]['first_round_plans'][i] for i in range(n))
    for v in out.values():del v['first_round_plans']
    return {'per_mission':n,'seed_range':[start,start+n-1],
            'variants':out,'opening_plan_changes_vs_grid':different,
            'warning':'Planner explicitly rewards mission-specific statistics; different action choices can be a result of heuristic design and are not independent evidence of depth.'}


def offer_probe(n=200,seed=27100):
    pair_counts=Counter()
    for s in range(seed,seed+n):
        pair_counts['+'.join(mission_offers(s))]+=1
    return dict(pair_counts)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=260)
    p.add_argument('--games',type=int,default=16);p.add_argument('--two-edit',action='store_true')
    opts=p.parse_args()
    print(json.dumps({'finale':finish_probe(opts.cases,max_actions=2 if opts.two_edit else 1),
                      'sessions':games(opts.games),'offers':offer_probe()},indent=2))
