"""Four-seat commitment laboratory for Storm Engine (RESEARCH ONLY).

Each seat independently selects one of four duties; the underlying Phase 6
crew reducer resolves *exactly* those four workers and fixed scenario orders.
Neither a scripted choice nor a browser selection establishes human agency.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
from experiments.redesign_phase3 import engine
from experiments.redesign_phase6.crew import STATIONS, crew_step

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=('crisis','junction')


def scenario(name):
    if name not in SCENARIOS:raise ValueError('Unknown scenario')
    s=engine.new_game([[] for _ in range(8)])
    if name=='crisis':
        s.update(round=7,hull=1,power=2,coolant=1,levels=[2,1,0],
                 board=[dict(id='threat',lane=2,sign=1,strength=2,depth=1,held=False),
                        dict(id='drifter',lane=0,sign=1,strength=1,depth=2,held=False)])
    else:
        s.update(round=4,hull=3,power=3,coolant=2,levels=[1,1,0],
                 board=[dict(id='plus',lane=0,sign=1,strength=1,depth=1,held=False),
                        dict(id='minus',lane=0,sign=-1,strength=1,depth=1,held=False),
                        dict(id='threat',lane=2,sign=1,strength=2,depth=1,held=False),
                        dict(id='drifter',lane=0,sign=1,strength=1,depth=2,held=False)])
    return s


def make_plan(name,counts):
    """One fixed disclosed order per staffed duty, not an optimizing solver."""
    nav,control,engineer,dispatch=counts
    orders={}
    if nav:orders['nav']=[dict(kind='SHIFT',token='drifter',delta=1)]
    if control:orders['control']=[dict(kind='DAMP',token='threat')]
    if engineer:orders['engineer']={'build':1 if name=='crisis' else 0}
    if dispatch:orders['dispatch']={'kind':'cover','lane':2}
    return orders


def outcome(name,assignments):
    if len(assignments)!=4 or any(duty not in STATIONS for duty in assignments):
        raise ValueError('Four known seat commitments required')
    counts=tuple(assignments.count(duty) for duty in STATIONS)
    state=scenario(name)
    initial={'hull':state['hull'],'power':state['power'],'coolant':state['coolant'],
             'levels':state['levels'][:], 'round':state['round']}
    if max(counts)>2:
        return {'valid':False,'reason':'At most two workers can staff the same duty.',
                'staff':counts}
    plan=make_plan(name,counts)
    try:
        out=crew_step(state,counts,plan)
    except ValueError as exc:
        return {'valid':False,'reason':str(exc),'staff':counts}
    event=out['history'][-1]
    # Crisis includes the deliberately non-tactical eighth-round deadline, so
    # this is a real win/loss counterfactual rather than a speculative rating.
    if name=='crisis' and out['finished'] is None:
        after=crew_step(out,(1,1,1,1),{})
        final=after['finished']
    else:final=out['finished']
    return {'valid':True,'staff':counts,'orders':plan,'hull':out['hull'],
            'power':out['power'],'coolant':out['coolant'],'levels':out['levels'],
            'pending':out['pending'],'matched':event['matched'],
            'leaks':event['raw'],'blocked':event.get('cover_saved',0),
            'finish':out['finished'],'following_finish':final,
            'round':out['round'],'initial':initial}


def all_outcomes():
    results={}
    for name in SCENARIOS:
        states={}
        for assignments in itertools.product(STATIONS,repeat=4):
            states['|'.join(assignments)]=outcome(name,assignments)
        results[name]={'intro': 'One hull remains. Complete Aegis, survive the breach, then hold to the final bell.'
                     if name=='crisis' else
                     'A productive collision competes with an upgrade and the right-lane breach.',
                       'state':scenario(name),'outcomes':states}
    return {'ruleset':'redesign/phase7-commitment-lab','duty_order':list(STATIONS),
            'disclaimer':'Counterfactual one-turn states from the Phase 6 research reducer. Not production gameplay, multiplayer, or human-playtest evidence.',
            'scenarios':results}


def analyze(data):
    """Count how often changing a seat's single duty alters the actual result.

    State-distinct is not synonymous with valuable or enjoyable: this is an
    upper bound on potentially consequential decisions, not an engagement KPI.
    """
    summary={}
    for name,item in data['scenarios'].items():
        entries=item['outcomes'];legal={key:v for key,v in entries.items() if v['valid']}
        winning=[key for key,v in legal.items() if v['following_finish']=='WIN']
        signature=lambda v: (v['hull'],v['power'],v['coolant'],tuple(v['levels']),v['pending'],v['finish'],v['following_finish'])
        variations=0;winning_edges=0;legal_edges=0
        for key,v in legal.items():
            stations=key.split('|')
            for i in range(4):
                for alternative in STATIONS:
                    if alternative==stations[i]:continue
                    changed=stations[:];changed[i]=alternative
                    other=entries['|'.join(changed)]
                    if not other['valid']:continue
                    legal_edges+=1
                    variations+=int(signature(other)!=signature(v))
                    winning_edges+=int((other['following_finish']=='WIN')!=(v['following_finish']=='WIN'))
        summary[name]={'total_seat_combinations':len(entries),'legal':len(legal),
                       'illegal':len(entries)-len(legal), 'winning':len(winning),
                       'legal_single_seat_changes':legal_edges,
                       'state_changing_changes':variations,
                       'win_loss_changing_changes':winning_edges,
                       'unique_end_states':len({signature(v) for v in legal.values()})}
    return summary


def build():
    data=all_outcomes()
    data['audit']=analyze(data)
    return data


def main():
    data=build()
    out=ROOT/'site/crew-lab-data.json'
    out.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    (ROOT/'docs/redesign/phase07-seat-counterfactual-audit.json').write_text(
        json.dumps(data['audit'],indent=2,sort_keys=True)+'\n')
    print(json.dumps(data['audit'],indent=2))

if __name__=='__main__':main()
