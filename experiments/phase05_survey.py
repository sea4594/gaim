"""Reproducible objective-blind design probes; NO human-fun inference."""
from __future__ import annotations
from collections import Counter
from dataclasses import replace
import json,random
from reference.charge_loom_v01 import State,Token
from experiments.phase05_lab import Design,step,options
from experiments.phase04_lab import options as core_options
from experiments.rules_tournament import score as core_score


def available_actions(g,choice=0):
    if 'draft' in g.variant and g.state.round<7:
        trial=g.core.trial
        w=list(trial.waves)
        w[trial.state.round]=g.deck[g.available[choice]]
        temp=replace(g.core,trial=replace(trial,waves=tuple(w)))
        ops=core_options(temp)
        if 'accelerate' in g.variant:
            from experiments.rules_tournament import planning_tokens
            ops += [('accelerate',t.id) for t in planning_tokens(temp.trial) if t.row>=1]
        return [x for x in ops if x[0]!='pass']
    return [x for x in options(g) if x[0] not in ('pass','draft')]


def utility(g):
    s=g.state
    v=core_score(g.core.trial)
    if not s.over:
        v+=1.0*g.synchronized+0.5*g.large.bit_count()
        if g.mission=='shield':v+=5*max(0,s.hp-4)
        if g.mission=='choreography':v+=12*bool(g.synchronized)
        if g.mission=='voltage':v+=7*g.large.bit_count()
        if g.variant=='heat':v-=6*g.heat
    return v


def plan(g):
    choices=range(len(g.available)) if 'draft' in g.variant and g.state.round<7 else (None,)
    solutions=[]
    for choice in choices:
        selected=[('draft',choice)] if choice is not None else []
        base=utility(step(g,selected))
        for _ in range(4):
            best=base;choice_action=None
            for a in available_actions(g,choice or 0):
                if a in selected:continue
                try: candidate=step(g,selected+[a]);v=utility(candidate)
                except (ValueError,TypeError,IndexError):continue
                if v>best+1e-9:
                    best=v;choice_action=a
            if choice_action is None:break
            selected.append(choice_action);base=best
        solutions.append((base,selected))
    solutions.sort(key=lambda v:v[0],reverse=True)
    return solutions[0][1]


def games(n=24,seed_base=7000):
    variants=('control','draft','accelerate','draft_accelerate','heat','accelerate_no_damp','accelerate_no_hold','accelerate_no_flip')
    results={}
    for mode in variants:
        c=Counter()
        for seed in range(seed_base,seed_base+n):
            g=Design.new(mode,seed)
            while not g.state.over:
                acts=plan(g)
                c.update(a[0] for a in acts)
                c['draft_newer']+=('draft',1) in acts
                g=step(g,acts)
            c['wins']+=g.state.over=='win'
            c['survivals']+=g.state.hp>0
            c['hp_total']+=max(0,g.state.hp)
            c['power_total']+=sum(g.state.progress)
            c['games']+=1
        results[mode]=dict(c)
    return {'seed_range':[seed_base,seed_base+n-1],'planner':'one-round greedy utility; draft comparison is myopic','data':results}


def finale(n=240,seed=1509):
    rng=random.Random(seed)
    stats=Counter();examples={}
    for _ in range(n):
        nt=rng.randint(2,4)
        tok=tuple(Token(i+1,rng.randrange(3),rng.choice((0,1)),rng.choice((-1,1)),rng.choice((1,1,2))) for i in range(nt))
        s=State(round=8,hp=rng.randint(1,6),progress=tuple(rng.choice((0,1,2,2,3)) for _ in range(3)),
                tokens=tok,next_id=nt+1)
        base=Design.new('control',state=s,waves=tuple(() for _ in range(9)))
        accel=Design.new('accelerate',state=s,waves=tuple(() for _ in range(9)))
        best0=step(base).state.over=='win'
        best1=step(accel).state.over=='win'
        # up to one action per token, not four-edit exhaustive: same limited benchmark for both.
        base_opts=[a for a in options(base) if a[0]!='pass']
        acc_opts=[a for a in options(accel) if a[0]!='pass']
        base_win=best0
        acc_win=best1
        accel_positive=0;accel_negative=0
        for a in base_opts:
            try:base_win |= step(base,[a]).state.over=='win'
            except ValueError:pass
        for a in acc_opts:
            try:
                ending=step(accel,[a]).state
            except ValueError:continue
            acc_win |= ending.over=='win'
            if a[0]=='accelerate':
                neutral=step(accel).state
                if ending.hp>neutral.hp or (ending.over=='win' and neutral.over!='win'):accel_positive+=1
                if ending.hp<neutral.hp or (ending.over!='win' and neutral.over=='win'):accel_negative+=1
        stats['total']+=1
        stats['control_one_action_win']+=base_win
        stats['accelerate_one_action_win']+=acc_win
        stats['accel_candidate_better_than_pass']+=accel_positive
        stats['accel_candidate_worse_than_pass']+=accel_negative
        if not base_win and acc_win and 'rescue' not in examples:
            examples['rescue']={'power':s.progress,'hp':s.hp,'tokens':[(x.lane,x.row,x.sign,x.size) for x in tok]}
    return {'sample_size':n,'seed':seed,'scope':'final round, pass or ONE edit per round only','counts':dict(stats),'examples':examples}


def mission_comparison(n=24,seed_base=7000):
    outcomes={}
    for mission in ('standard','shield','choreography','voltage'):
        cnt=Counter()
        for seed in range(seed_base,seed_base+n):
            g=Design.new('mission',seed,mission=mission)
            while not g.state.over:
                g=step(g,plan(g))
            cnt['wins']+=g.state.over=='win'
            cnt['alive']+=g.state.hp>0
            cnt['avg_power_numer']+=sum(g.state.progress)
            cnt['sync_rounds_total']+=g.synchronized
            cnt['distinct_large_lanes_total']+=g.large.bit_count()
        outcomes[mission]=dict(cnt)
    return {'seeds':n,'missions':outcomes,'warning':'Different goals, win counts NOT direct evidence of enjoyment'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--games',type=int,default=24);p.add_argument('--finales',type=int,default=240)
    args=p.parse_args()
    print(json.dumps({'full_games':games(args.games),'finale':finale(args.finales),'missions':mission_comparison(args.games)},indent=2))
