"""Three public storm climates testing strategic diversity, not approved rules.

All scenarios use the same 8-round Storm Engine reducer, resource opening,
wave count and victory condition. Only the stochastic *shape* of waves changes.
All seeds and storm waves are public in the web research exhibit. There is no
scenario win modifier, prescribed upgrade, hidden benefit or prohibited action.
"""
from __future__ import annotations
import random
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.survey import engine_policy

PROFILES = {
    'harvest': {'title':'Resonant Harvest','pitch':'Opposite charges often arrive together. Can the team develop production before overinvesting in defense?', 'note':'Collision-rich, fewer isolated fragments.'},
    'fracture': {'title':'Fractured Currents','pitch':'Opposite charges are displaced into neighboring lanes. How much protection is worth buying versus energy growth?', 'note':'Cross-lane polarity pairs.'},
    'siege': {'title':'Shatter Siege','pitch':'Extra fragments strain the hull. Can the team develop two systems without falling behind on survival?', 'note':'Frequent third threats and stronger leaks.'},
}
STRATEGIES = {
    'dynamo_aegis': 'Dynamo + Aegis',
    'aegis_switchyard': 'Aegis + Switchyard',
    'dynamo_switchyard': 'Dynamo + Switchyard',
}


def waves(profile: str, seed: int):
    if profile not in PROFILES or type(seed) is not int or seed<0:
        raise ValueError('Unknown climate or bad seed')
    rng=random.Random(f'gaim-phase8:{profile}:{seed}')
    result=[]
    for round_number in range(8):
        if round_number==7:
            result.append([])
            continue
        lane=rng.randrange(3)
        plus=rng.choice([1,1,2]);minus=rng.choice([1,1,2])
        if profile=='harvest':
            others=lane if rng.random()<.83 else rng.randrange(3)
            wave=[dict(lane=lane,sign=1,strength=plus),dict(lane=others,sign=-1,strength=minus)]
            if rng.random()<.2:
                wave.append(dict(lane=rng.randrange(3),sign=rng.choice((-1,1)),strength=1))
        elif profile=='fracture':
            wave=[dict(lane=lane,sign=1,strength=plus),
                  dict(lane=(lane+1+rng.randrange(2))%3,sign=-1,strength=minus)]
            if rng.random()<.4:
                wave.append(dict(lane=rng.randrange(3),sign=rng.choice((-1,1)),strength=1))
        else:
            others=lane if rng.random()<.55 else rng.randrange(3)
            wave=[dict(lane=lane,sign=1,strength=rng.choice((1,2))),
                  dict(lane=others,sign=-1,strength=rng.choice((1,2)))]
            if rng.random()<.7:
                wave.append(dict(lane=rng.randrange(3),sign=rng.choice((-1,1)),strength=rng.choice((1,2))))
        result.append(wave)
    return result


def run(profile: str, seed: int, strategy: str, include_states=False):
    if strategy not in STRATEGIES:
        raise ValueError('Unknown strategy')
    w=waves(profile,seed)
    state=engine.new_game(w)
    snapshots=[]
    while state['finished'] is None:
        plan=engine_policy(state,strategy)
        state=engine.step(state,plan)
        if include_states:
            e=state['history'][-1]
            snapshots.append(dict(round=e['round'],plan=plan,board=state['board'],
                                  hull=state['hull'],power=state['power'],coolant=state['coolant'],
                                  levels=state['levels'],pending=state['pending'],
                                  outages=state['outages'], matched=e['matched'],
                                  damage=e['damage'],deadline=e['deadline'],
                                  outcome=state['finished']))
    result={'outcome':state['finished'],'hull':state['hull'],'power':state['power'],
            'levels':state['levels'],'rounds':len(state['history'])}
    if include_states:
        result['waves']=w
        result['snapshots']=snapshots
    return result


def summary(starts=(81000,82000),n=40):
    if not starts or n<1:raise ValueError('Empty benchmark')
    result={'ruleset':'redesign/phase8-scenario-climates','control':'Storm Engine Phase 3 reducer (unchanged)',
            'policy':'Same fixed upgrade-target order and one-ply tactical search for every profile; no Switchyard free-shift search. Results are policy diagnostics, not optimal play.',
            'resources':{'hull':6,'power':2,'coolant':2},'sets':{}}
    for name,start in (('development',starts[0]),('holdout',starts[-1])):
        profiles={}
        for profile in PROFILES:
            outcomes={strategy:[run(profile,start+i,strategy) for i in range(n)] for strategy in STRATEGIES}
            profiles[profile]={'wins':{strategy:sum(x['outcome']=='WIN' for x in rows) for strategy,rows in outcomes.items()},
                'different_winning_paths':sum(sum(outcomes[st][i]['outcome']=='WIN' for st in STRATEGIES)>=2 for i in range(n)),
                'only_one_winning_path':sum(sum(outcomes[st][i]['outcome']=='WIN' for st in STRATEGIES)==1 for i in range(n)),
                'all_lose':sum(all(outcomes[st][i]['outcome']!='WIN' for st in STRATEGIES) for i in range(n)),
                'avg_hull':{strategy:round(sum(x['hull'] for x in rows)/n,2) for strategy,rows in outcomes.items()}}
        result['sets'][name]={'start':start,'n':n,'profiles':profiles}
    return result
