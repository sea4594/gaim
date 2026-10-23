"""Pass07 pre-registered mechanical diagnostics. Not human-playtest measurements."""
from __future__ import annotations
import json,random
from collections import Counter
from reference.charge_loom_v01 import State,Token
from experiments.phase07_lab import Audit,step,demand_options
from experiments.phase06_survey import plan

MODES=('market','demand','flex_demand','pledge','tide','demand_pledge','milestones','council')

def policy(g:Audit,lookahead=1):
    acts,draft,owners,_=plan(g.experiment,lookahead=lookahead)
    demand=None
    if g.mode in ('flex_demand','council'):
        choices=demand_options(g)
        if choices:
            # Simulate both consumption choices, prefer most feasible state.
            scored=[]
            for choice in choices:
                h=step(g,acts,draft=draft,demand=choice)
                s=h.state
                metric=1000*(s.over=='win')-1000*(s.over=='loss: breach')+8*s.hp+sum(s.progress)*2+3*h.serviced
                scored.append((metric,choice))
            demand=max(scored)[1]
    # Optimistic one-step wager selection is an upper bound on how much a
    # simple informed player can exploit free-to-declare contracts.
    pledge=None
    if 'pledge' in g.mode and g.state.round in (0,2,4,6):
        baseline=step(g,acts,draft=draft)
        best=(sum(baseline.state.progress)*3+baseline.state.hp*7, None)
        for src in range(3):
            if g.state.progress[src]<1:continue
            for kind in ('safe','sync','surge'):
                try:r=step(g,acts,draft=draft,pledge=(kind,src))
                except (ValueError,TypeError):continue
                score=sum(r.state.progress)*3+r.state.hp*7
                if score>best[0]:best=(score,(kind,src))
        pledge=best[1]
    return acts,draft,demand,pledge


def games(n=24,start=14000,lookahead=1):
    results={}
    for mode in MODES:
        cnt=Counter(); action_counts=Counter()
        for seed in range(start,start+n):
            g=Audit.new(mode,seed=seed)
            while not g.state.over:
                actions,draft,demand,pledge=policy(g,lookahead)
                cnt['actions']+=len(actions);cnt['slots']+=4
                cnt['draft_new']+=draft==1
                action_counts.update(a[0] for a in actions)
                g=step(g,actions,draft=draft,pledge=pledge,demand=demand)
            cnt['games']+=1;cnt['wins']+=g.state.over=='win'
            cnt['alive']+=g.state.hp>0
            cnt['hp_total']+=max(0,g.state.hp)
            cnt['power_total']+=sum(g.state.progress)
            cnt['serviced']+=g.serviced;cnt['blackouts']+=g.blackouts
            cnt['wagers']+=g.wagers;cnt['wagers_won']+=g.wagers_won
        results[mode]={'totals':dict(cnt),'action_distribution':dict(action_counts)}
    return {'seeds':[start,start+n-1], 'lookahead':lookahead, 'variants':results,
            'interpretation':'Same forecast-aware action heuristic; unaware of grid demand. Wager selection chooses best immediate return. Not a fair contest of optimized agents.'}


def pledge_probe(n=240,seed=7713):
    """One-round counterfactuals with NO edits, near-end states, empty waves.
    Test whether the advertised risky pledge is simply an obvious free bonus
    whenever pre-existing pairs are already resolving.
    """
    rng=random.Random(seed);c=Counter();example={}
    empty=tuple(() for _ in range(9))
    for ix in range(n):
        progress=tuple(rng.randint(0,3) for _ in range(3))
        toks=[]
        for i in range(rng.randint(1,6)):
            toks.append(Token(i+1,rng.randrange(3),0,rng.choice((-1,1)),rng.choice((1,2))))
        state=State(round=6,hp=rng.randrange(2,8),progress=progress,tokens=tuple(toks),next_id=len(toks)+1)
        a=Audit.new('pledge',state=state,waves=empty)
        baseline=step(a)
        c['states']+=1
        for source,p in enumerate(progress):
            if p==0:continue
            for kind in ('safe','sync','surge'):
                outcome=step(a,pledge=(kind,source))
                difference=sum(outcome.state.progress)-sum(baseline.state.progress)
                c['offers']+=1
                c['better']+=difference>0
                c['worse']+=difference<0
                c['equal']+=difference==0
                c['paid']+=outcome.wagers_won
                if difference>0 and not example:
                    example={'power':progress,'tokens':[(t.lane,t.sign,t.size) for t in toks],
                             'pledge':(kind,source),'baseline':baseline.state.progress,'wager':outcome.state.progress}
    return {'sample_size':n,'counts':dict(c),'example':example,
            'caveat':'No edits; condition selected knowing visible current board, not secret future waves.'}


def objective_divergence(n=400,seed=543):
    """Mechanics of mission-specific final-round rewards. No optimizing bot."""
    from experiments.phase05_lab import Design,step as design_step
    rng=random.Random(seed)
    cnt=Counter();exam=[];empty=tuple(() for _ in range(9))
    for ix in range(n):
        tok=tuple(Token(i+1,rng.randrange(3),0,rng.choice((-1,1)),rng.choice((1,2))) for i in range(rng.randint(2,6)))
        state=State(round=8,hp=rng.randrange(1,8),progress=tuple(rng.randrange(4) for _ in range(3)),
                    tokens=tok,next_id=len(tok)+1)
        outcomes={}
        for mission in ('standard','shield','choreography','voltage'):
            # Draft only from round zero; mission fixture uses accelerate variant
            d=Design.new('accelerate',state=state,waves=empty,mission=mission)
            outcomes[mission]=design_step(d).state.over=='win'
        cnt['cases']+=1
        for mission,v in outcomes.items():cnt[f'{mission}_wins']+=v
        cnt['mission_results_diverge']+=len(set(outcomes.values()))>1
        if len(set(outcomes.values()))>1 and len(exam)<2:exam.append({'power':state.progress,'hp':state.hp,'results':outcomes})
    return {'counts':dict(cnt),'examples':exam,'caveat':'One no-edit final round; missions are existing prototype rules and cannot establish varied optimal strategies.'}


def mission_action_divergence(n=300,seed=667):
    """Enumerate pass + one legal edit for each objective on same final state.

    Contrast *which actions* could deliver wins, not raw mission win rates.
    When winners for multiple missions exist, evaluate identical action sets.
    """
    from experiments.phase05_lab import Design, step as ds, options as opts
    rng=random.Random(seed);total=Counter();examples=[];empty=tuple(() for _ in range(9))
    missions=('standard','shield','choreography','voltage')
    for ix in range(n):
        tokens=tuple(Token(i+1,rng.randrange(3),0,rng.choice((-1,1)),rng.choice((1,2)))
                     for i in range(rng.randint(2,6)))
        state=State(round=8,hp=rng.randrange(1,8),progress=tuple(rng.randrange(4) for _ in range(3)),
                    tokens=tokens,next_id=len(tokens)+1)
        base=Design.new('accelerate',state=state,waves=empty)
        edits=[()]+[(a,) for a in opts(base) if a[0] not in ('draft','pass')]
        winning={}
        for m in missions:
            g=Design.new('accelerate',state=state,waves=empty,mission=m)
            outcomes=[]
            for a in edits:
                try:win=ds(g,a).state.over=='win'
                except (ValueError,IndexError,TypeError):continue
                if win:outcomes.append(a)
            winning[m]=set(outcomes)
        total['states']+=1
        total['missions_with_win']+=sum(bool(v) for v in winning.values())
        masks=[m for m in missions if winning[m]]
        if len(masks)>1:
            total['multi_winnable']+=1
            if any(not winning[a].intersection(winning[b]) for i,a in enumerate(masks) for b in masks[i+1:]):
                total['disjoint_winning_actions']+=1
                if len(examples)<2:
                    examples.append({'progress':state.progress,'hp':state.hp,
                                     'tokens':[(t.lane,t.sign,t.size) for t in tokens],
                                     'sets':{m:[list(a) for a in sorted(winning[m],key=str)] for m in masks}})
    return {'cases':n,'counts':dict(total),'examples':examples,
            'caveat':'Only pass/single-edit final rounds; not evidence of session-wide strategic diversity'}


def council_choice_probe(n=600,seed=9921):
    """Exact final-checkpoint choice effects in reproducible synthetic states."""
    rng=random.Random(seed);c=Counter();examples=[];empty=tuple(() for _ in range(9))
    for i in range(n):
        s=State(round=8,hp=rng.randrange(1,8),progress=tuple(rng.randrange(4) for _ in range(3)))
        base=Audit.new('council',state=s,waves=empty)
        # Complete two of three payments, so this is a real endgame decision.
        game=Audit(base.experiment,'council',serviced=2)
        results=[step(game,demand=x) for x in (2,0)]
        c['states']+=1
        c['different_final_power']+=results[0].state.progress!=results[1].state.progress
        c['different_win_outcome']+=(results[0].state.over=='win')!=(results[1].state.over=='win')
        c['different_hull']+=results[0].state.hp!=results[1].state.hp
        c['both_win']+=all(g.state.over=='win' for g in results)
        c['both_lose']+=all(g.state.over!='win' for g in results)
        if results[0].state.over!=results[1].state.over and len(examples)<3:
            examples.append({'before':s.progress,'hp':s.hp,'right_result':results[0].state.over,
                             'left_result':results[1].state.over,
                             'right_power':results[0].state.progress,
                             'left_power':results[1].state.progress})
    return {'cases':n,'counts':dict(c),'examples':examples,
            'caveat':'Synthetic final states sampled uniformly, not naturally visited by players. No action edits.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--games',type=int,default=16);p.add_argument('--lookahead',type=int,default=1)
    args=p.parse_args()
    print(json.dumps({'games':games(args.games,lookahead=args.lookahead),
                      'pledge':pledge_probe(),'objectives':objective_divergence(), 'mission_actions':mission_action_divergence(),'council':council_choice_probe()},indent=2))
