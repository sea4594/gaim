"""Bounded, reproducible Pass 14 counterfactuals. NOT gameplay enjoyment data.

Choose build-or-pass at round 8; automatically resolve the final round. The
next round's hazards are drawn from visible synthetic tokens, not from a full
hidden deck. Each investment is compared to passing from the SAME starting
state. All links are paid and cannot operate until the next round.
"""
from __future__ import annotations
import argparse
import json
import random
from collections import Counter
from reference.charge_loom_v01 import State, Token
from experiments.phase14_network import Network, step, options

EMPTY=((),)*9


def state(rng,seed):
    num=rng.randrange(2,9)
    tokens=tuple(Token(i+1,rng.randrange(3),rng.choice((0,1)),rng.choice((-1,1)),
                       rng.choice((1,1,2,3)),rng.choice((0,0,1))) for i in range(num))
    return State(seed=seed,round=7,hp=rng.randint(1,7),
                 progress=tuple(rng.randint(0,3) for _ in range(3)),
                 coolant=rng.randint(0,3),tokens=tokens,next_id=num+1)


def terminal(g, action=()):
    g=step(g, [action] if action else ())
    if not g.state.over:
        g=step(g)
    return g


def survey(n=1000,seed=14700):
    rng=random.Random(seed)
    totals={mode:Counter() for mode in ('conduit','switch')}
    examples={}
    for i in range(n):
        initial=state(rng,seed+i)
        # The SAME no-action counterfactual must hold for both variants.
        base=terminal(Network.new('conduit',state=initial,waves=EMPTY))
        for mode in ('conduit','switch'):
            g=Network.new(mode,state=initial,waves=EMPTY)
            counts=totals[mode]
            counts['cases']+=1
            counts['base_wins']+=base.state.over=='win'
            configs=options(g)
            counts['available_choices']+=len(configs)
            rescue=0; harm=0; changed_distribution=0
            best=None
            for a in configs:
                end=terminal(g,a)
                counts['purchased_trials']+=1
                counts['transfers']+=end.transferred
                counts['changes_power']+=end.state.progress!=base.state.progress
                won=end.state.over=='win'
                rescue+=base.state.over!='win' and won
                harm+=base.state.over=='win' and not won
                changed_distribution+=end.state.progress!=base.state.progress
                if (base.state.over!='win' and won) or (base.state.over=='win' and not won):
                    key=f'{mode}_{"rescue" if won else "spoiled"}'
                    if key not in examples:
                        examples[key]={
                            'index':i,'power':initial.progress,'hp':initial.hp,
                            'tokens':[(t.id,t.lane,t.row,t.sign,t.size,t.held) for t in initial.tokens],
                            'action':a,'base':(base.state.over,base.state.hp,base.state.progress),
                            'variant':(end.state.over,end.state.hp,end.state.progress),
                            'transfers':end.transferred
                        }
                if best is None or (end.state.over=='win',end.state.hp,sum(end.state.progress))>(best.state.over=='win',best.state.hp,sum(best.state.progress)):
                    best=end
            counts['states_with_rescue']+=rescue>0
            counts['states_with_spoiled_win']+=harm>0
            counts['rescuing_choices']+=rescue
            counts['spoiling_choices']+=harm
            counts['states_with_changed_distribution']+=changed_distribution>0
    return {'method':'Paired two-round counterfactual, same starting states, all legal paid/one-edit wire purchases, no subsequent edits; synthetic visible-token states.',
            'sample_size':n, 'seed_start':seed,
            'limitations':'Not an optimal solver, not real scenario frequencies; does not evaluate four-player decision quality. SWITCH is deliberately free and changes difficulty.',
            'results':{mode:dict(v) for mode,v in totals.items()},'witnesses':examples}


def opportunity_probe(n=500,seed=14800):
    """Measure how often preexisting wires actually flow, versus merely existing.

    Active wires are GIVEN to each paired synthetic position (so it is a
    potential-flow upper bound, NOT an investment-return or win-rate estimate).
    """
    rng=random.Random(seed);stats=Counter()
    for i in range(n):
        s=state(rng,seed+i)
        for link in ((0,1),(1,0),(1,2),(2,1)):
            g=Network.new('conduit',state=s,waves=EMPTY,link=link)
            after=step(g)
            stats['link_rounds']+=1
            stats['flows']+=after.transferred
            stats['produced_extra_power']+=sum(after.state.progress)>sum(step(Network.new('control',state=s,waves=EMPTY)).state.progress)
    return dict(stats)

def longer_horizon(n=400,seed=15100):
    """Different planning horizon using the same explicit three future wave slots.

    One purchase on round FIVE; then pass for four rounds. This is deliberately
    a PASSIVE investment policy and is not an optimal policy comparison.
    """
    from reference.charge_loom_v01 import wavebook
    rng=random.Random(seed)
    outcomes={mode:Counter() for mode in ('conduit','switch')}
    for i in range(n):
        s=state(rng,seed+i)
        s=__import__('dataclasses').replace(s,round=4)
        waves=wavebook(seed+i)+((),())
        for mode in ('conduit','switch'):
            g=Network.new(mode,state=s,waves=waves)
            base=g
            while not base.state.over:base=step(base)
            cnt=outcomes[mode];cnt['states']+=1
            cnt['control_wins']+=base.state.over=='win'
            rescue=0;spoil=0;paid=0
            for a in options(g):
                h=step(g,(a,))
                while not h.state.over:h=step(h)
                paid+=1
                rescue+=base.state.over!='win' and h.state.over=='win'
                spoil+=base.state.over=='win' and h.state.over!='win'
                cnt['trial_flows']+=h.transferred
            cnt['purchases_tested']+=paid
            cnt['states_with_rescue']+=rescue>0
            cnt['states_with_spoiled_win']+=spoil>0
            cnt['rescue_choices']+=rescue
            cnt['spoiled_choices']+=spoil
    return {mode:dict(x) for mode,x in outcomes.items()}


def service_endgame(n=600,seed=15200):
    """One-round service objective probe (NOT comparable to standard mission)."""
    rng=random.Random(seed);c=Counter();ex=None
    for i in range(n):
        s=state(rng,seed+i)
        s=__import__('dataclasses').replace(s,round=8)
        lane=rng.randrange(3)
        served=tuple(j==lane for j in range(3))
        g=Network.new('service',state=s,waves=EMPTY,served=served)
        available=[a for a in options(g) if a[0]=='deliver']
        if len(available)<2:continue
        c['states_with_two_choices']+=1
        outputs=[(a,step(g,(a,))) for a in available]
        results={g1.state.over=='win' for _,g1 in outputs}
        c['different_win_result']+=len(results)>1
        c['all_win']+=results=={True}
        c['none_win']+=results=={False}
        if len(results)>1 and ex is None:
            ex={'index':i,'power':s.progress,'hp':s.hp,'already_served':served,
                'choices':[(a,h.state.over,h.state.progress) for a,h in outputs]}
    return {'counts':dict(c),'example':ex}



if __name__ == '__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--states',type=int,default=1000)
    a.add_argument('--seed',type=int,default=14700)
    args=a.parse_args()
    out=survey(args.states,args.seed)
    out['active_wire_upper_bound']=opportunity_probe(args.states//2,args.seed+100)
    out['long_horizon']=longer_horizon(max(50,args.states//2),args.seed+400)
    out['service_endgame']=service_endgame(max(100,args.states//2),args.seed+700)
    print(json.dumps(out,indent=2))
