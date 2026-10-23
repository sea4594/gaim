"""Reproducible, bounded counterfactual survey of experimental Phase 13 rules.

All states synthetic with empty remaining storm waves, to isolate the mechanisms.
They are NOT human playtests, nor representative randomly generated missions.
"""
from __future__ import annotations
import argparse, json, random
from collections import Counter
from reference.charge_loom_v01 import State, Token
from experiments.phase13_structural import Structural, step, shunt_choices

EMPTY=((),)*9


def _state(rng, round_index, seed):
    count=rng.randrange(2,9)
    tokens=tuple(Token(i+1, rng.randrange(3), rng.randrange(3), rng.choice((-1,1)),
                       rng.choice((1,1,2,3)), rng.choice((0,0,0,1))) for i in range(count))
    return State(round=round_index,hp=rng.randrange(1,8),
                 progress=tuple(rng.randrange(4) for _ in range(3)),
                 coolant=rng.randrange(4),tokens=tokens,next_id=count+1,seed=seed)


def finish(game):
    while not game.state.over:
        game=step(game)
    return game


def echo_survey(cases=500,seed=13491):
    rng=random.Random(seed)
    c=Counter();example_good=None;example_bad=None
    for ix in range(cases):
        state=_state(rng,6,seed+ix)
        baseline=finish(Structural.new('control',state=state,waves=EMPTY))
        echo=finish(Structural.new('echo_breach',state=state,waves=EMPTY))
        c['cases']+=1
        c['generated_echoes']+=echo.echoes
        c['base_wins']+=baseline.state.over=='win'
        c['echo_wins']+=echo.state.over=='win'
        c['rescued_wins']+=baseline.state.over!='win' and echo.state.over=='win'
        c['lost_wins']+=baseline.state.over=='win' and echo.state.over!='win'
        c['greater_hp']+=echo.state.hp>baseline.state.hp
        c['lower_hp']+=echo.state.hp<baseline.state.hp
        c['same_hp']+=echo.state.hp==baseline.state.hp
        ex={'idx':ix,'tokens':[(t.lane,t.row,t.sign,t.size,t.held) for t in state.tokens],
            'power':state.progress,'hp':state.hp,
            'baseline':[baseline.state.over,baseline.state.hp,baseline.state.progress],
            'aftershock':[echo.state.over,echo.state.hp,echo.state.progress]}
        if c['rescued_wins'] and not example_good and baseline.state.over!='win' and echo.state.over=='win':example_good=ex
        if c['lost_wins'] and not example_bad and baseline.state.over=='win' and echo.state.over!='win':example_bad=ex
    return {'counts':dict(c),'first_win_rescue':example_good,'first_win_lost':example_bad}


def shunt_survey(cases=500,seed=13572):
    rng=random.Random(seed)
    c=Counter(); examples={}
    for ix in range(cases):
        state=_state(rng,8,seed+ix)
        g=Structural.new('shunt',state=state,waves=EMPTY)
        base=step(g)
        lanes=shunt_choices(g)
        c['cases']+=1
        c['shunt_available']+=bool(lanes)
        c['shunt_choices']+=len(lanes)
        if not lanes:continue
        candidates=[step(g,shunt_lane=lane) for lane in lanes]
        c['shunt_changes_hp']+=any(h.state.hp!=base.state.hp for h in candidates)
        c['rescues_win']+=base.state.over!='win' and any(h.state.over=='win' for h in candidates)
        c['destroys_win']+=base.state.over=='win' and any(h.state.over!='win' for h in candidates)
        c['survival_rescue']+=base.state.hp<=0 and any(h.state.hp>0 for h in candidates)
        c['capital_spent']+=len(lanes)
        if len(examples)<2 and base.state.over!='win' and any(h.state.over=='win' for h in candidates):
            examples[str(ix)]={'tokens':[(t.lane,t.row,t.sign,t.size) for t in state.tokens],
                               'hp':state.hp,'power':state.progress,'base':base.state.over,
                               'shunt':[(lane,h.state.over,h.state.hp,h.state.progress) for lane,h in zip(lanes,candidates)]}
    return {'counts':dict(c),'examples':examples}


def survey(n=500):
    return {'method':'Exact no-edit terminal counterfactuals in reproducible synthetic states. '
                     'No assumption of equal difficulty, no human-cooperation inference.',
            'echo':echo_survey(n), 'shunt':shunt_survey(n)}


def paired_games(cases=48, seed=13400):
    """Same one-step edit planner for every variant; it does NOT plan for echoes.

    Shunt policy only uses shunt if the existing immediate utility score rises.
    This is a very weak test of meaningful future planning, not game balance.
    """
    from experiments.phase06_survey import plan, value
    out={}
    for mode in ('control', 'echo_breach', 'shunt'):
        c=Counter()
        for game_seed in range(seed,seed+cases):
            g=Structural.new(mode,seed=game_seed)
            while not g.state.over:
                acts,draft,_,_=plan(g.exp)
                shunt=None
                if mode=='shunt':
                    current=value(step(g,acts,draft=draft).exp)
                    for lane in shunt_choices(g,acts,draft):
                        result=step(g,acts,draft=draft,shunt_lane=lane)
                        score=value(result.exp)
                        if score>current+1e-9:
                            current=score;shunt=lane
                g=step(g,acts,draft=draft,shunt_lane=shunt)
                c['edits']+=len(acts)
                c['shunt_purchases']+=shunt is not None
            c['games']+=1
            c['wins']+=g.state.over=='win'
            c['survival_hp']+=max(0,g.state.hp)
            c['echoes']+=g.echoes
            c['shunt_saved_hp']+=g.shielded
        out[mode]=dict(c)
    return {'seeds':[seed,seed+cases-1], 'lookahead':'one-step independent edits',
            'limitations':'No agent explicitly values future echoes or resource spending beyond its immediate heuristic.',
            'variants':out}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--states',type=int,default=500);p.add_argument('--games',type=int,default=48);args=p.parse_args()
    result=survey(args.states)
    result['paired_games']=paired_games(args.games)
    print(json.dumps(result,indent=2))
