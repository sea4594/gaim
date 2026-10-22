"""Paired-state counterfactual tests; record diagnostics, not claimed fun scores."""
from collections import Counter
from dataclasses import replace
from itertools import product
import json
import random
from reference.charge_loom_v01 import State, Token
from experiments.phase04_lab import Lab, step, options
from experiments.rules_tournament import Trial, score

MODES_FINAL=('baseline','split','flip','transfer','bridge_split','bridge_flip')


def cases(n=100,seed=4606):
    rng=random.Random(seed)
    for ix in range(n):
        amount=rng.choice((3,4))
        toks=tuple(Token(i+1,rng.randrange(3),0,rng.choice((-1,1)),rng.choice((1,1,2)))
                   for i in range(amount))
        yield State(round=8,hp=rng.randint(1,6),progress=tuple(rng.choice((0,1,2,2,3)) for _ in range(3)),
                    coolant=rng.randint(0,3),tokens=toks,next_id=amount+1)


def plans(g):
    acts=options(g)
    tokens=tuple(t.id for t in g.trial.state.tokens)
    grouped=[]
    for tid in tokens:
        grouped.append([()] + [(a,) for a in acts if a[0] in ('shift','hold','damp','split','flip') and a[1]==tid])
    extra=[()]+[(a,) for a in acts if a[0] in ('transfer','bridge','resonator')]
    for seq in product(*grouped):
        normal=tuple(x for item in seq for x in item)
        if len(normal)>4:continue
        for e in extra:
            if len(normal)+len(e)<=4:yield normal+e


def final_survey(n=100,seed=4606):
    counts={m:Counter() for m in MODES_FINAL}
    examples={}
    for idx,s in enumerate(cases(n,seed)):
        for mode in MODES_FINAL:
            g=Lab.new(mode,state=s,waves=tuple(() for _ in range(9)))
            any_win=False; any_special_win=False; any_special_loss=False; any_loss=False
            one_win=None; special_win=None
            total=0
            for actions in plans(g):
                try: done=step(g,actions).trial.state
                except (ValueError,TypeError):continue
                total+=1
                special=any(a[0] in ('split','flip','transfer') for a in actions)
                if done.over=='win':
                    any_win=True
                    if one_win is None:one_win=actions
                    if special:
                        any_special_win=True
                        if special_win is None:special_win=actions
                else:
                    any_loss=True
                    if special:any_special_loss=True
            c=counts[mode]
            c['winnable']+=any_win
            c['both_winning_and_losing_plans']+=any_win and any_loss
            c['states_where_special_can_win']+=any_special_win
            c['states_where_special_can_lose']+=any_special_loss
            c['tested_legal_plans']+=total
            if mode not in examples and special_win:
                examples[mode]={'case':idx,'power':s.progress,'hp':s.hp,'tokens':[(x.lane,x.sign,x.size) for x in s.tokens], 'plan':special_win}
    return {'cases':n,'seed':seed,'objective':'single NOW-band turn, enumerate up to four edits','results':{m:dict(v) for m,v in counts.items()},'special_win_examples':examples}


def investment_cases():
    from itertools import product
    for src,dst in ((0,1),(1,0),(1,2),(2,1)):
        for matches in (0,1,2):
            for size in (1,2):
                for power in product(range(4),repeat=3):
                    if not power[src]:continue
                    toks=[]
                    if matches:
                        toks.extend([Token(1,src,1,1,size),Token(2,src,1,-1,size)])
                    if matches==2:
                        toks.extend([Token(3,src,2,1,size),Token(4,src,2,-1,size)])
                    yield src,dst,matches,size,State(round=6,hp=5,progress=power,
                                       tokens=tuple(toks),next_id=len(toks)+1)


def roi_survey():
    result={m:Counter() for m in ('baseline','bridge','resonator')}
    examples={m:{} for m in result}
    for src,dst,matches,size,s in investment_cases():
        for mode in result:
            start=Lab.new(mode,state=s,waves=tuple(() for _ in range(9)))
            baseline=step(step(step(start))).trial.state
            buy=step(step(step(start,[(mode,src,dst)]))).trial.state if mode!='baseline' else baseline
            kind=('help' if buy.over=='win' and baseline.over!='win' else
                  'hurt' if baseline.over=='win' and buy.over!='win' else 'neutral')
            result[mode][kind]+=1
            result[mode][f'size{size}_{matches}pairs_{kind}']+=1
            if kind!='neutral' and kind not in examples[mode]:
                examples[mode][kind]={'src':src,'dst':dst,'pair_count':matches,'pair_strength':size,
                                      'before_power':s.progress,'pass_end':baseline.progress,'buy_end':buy.progress,
                                      'pass_outcome':baseline.over,'buy_outcome':buy.over}
    return {'cases':sum(result['bridge'][k] for k in ('help','hurt','neutral')),
            'results':{m:dict(c) for m,c in result.items()},'examples':examples}


def greedy_game(mode, seed):
    game=Lab.new(mode,seed)
    tally=Counter()
    while not game.trial.state.over:
        chosen=[]; val=score(step(game).trial)
        for _ in range(4):
            best=None
            for action in options(game):
                if action[0]=='pass' or action in chosen:continue
                try: result=step(game,chosen+[action])
                except (ValueError,TypeError):continue
                value=score(result.trial)
                if value>val+1e-8:
                    val=value;best=action
            if best is None:break
            chosen.append(best)
        for action in chosen:tally[action[0]]+=1
        game=step(game,chosen)
    return game.trial.state,tally


def greedy_survey(n=20):
    result={}
    for mode in ('baseline','bridge','split','flip','transfer','resonator','bridge_split','bridge_flip'):
        wins=0;alive=0;power=0;actions=Counter()
        for seed in range(n):
            s,a=greedy_game(mode,seed)
            wins+=s.over=='win';alive+=s.hp>0;power+=sum(s.progress);actions.update(a)
        result[mode]={'wins':wins,'alive':alive,'mean_power':round(power/n,2),'actions':dict(actions)}
    return {'seeds':n,'caveat':'one-step greed intentionally misses delayed investments','results':result}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--final-cases',type=int,default=80)
    parser.add_argument('--greedy-seeds',type=int,default=20)
    args=parser.parse_args()
    print(json.dumps({'final':final_survey(args.final_cases),'investment':roi_survey(),
                      'greedy':greedy_survey(args.greedy_seeds)},indent=2))
