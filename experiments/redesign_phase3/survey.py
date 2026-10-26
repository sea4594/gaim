"""Reproducible exploratory policy tournament; diagnostic, not a fun/balance score."""
from __future__ import annotations
import argparse
import json
import random
from collections import Counter
from pathlib import Path
from . import engine, operations
from .common import resolve, token_by_id


def engine_waves(seed):
    rng=random.Random(seed)
    waves=[]
    # Favor some matched storms, add occasional dangerous or cross-lane fragments.
    for r in range(8):
        if r>=7: waves.append([]); continue
        lane=rng.randrange(3)
        wave=[{'lane':lane,'sign':1,'strength':rng.choice([1,2])},
              {'lane':lane if rng.random()<.63 else rng.randrange(3), 'sign':-1,'strength':rng.choice([1,2])}]
        if rng.random()<.38:
            wave.append({'lane':rng.randrange(3),'sign':rng.choice([-1,1]),'strength':1})
        waves.append(wave)
    return waves


def operations_waves(seed, players):
    rng=random.Random(f'{seed}:{players}')
    waves=[]
    for r in range(8):
        if r>=6: waves.append([]); continue
        lane=rng.randrange(3)
        wave=[{'lane':lane,'sign':1,'strength':rng.choice([1,2])},
              {'lane':lane if rng.random()<.60 else rng.randrange(3), 'sign':-1,'strength':rng.choice([1,2])}]
        for i in range(players-1):
            wave.append({'lane':rng.randrange(3), 'sign':rng.choice([-1,1]),'strength':1})
        waves.append(wave)
    return waves


def engine_policy(state, mode='dynamo_aegis'):
    # Candidate-build strategy is fixed in advance; reactive token edits stay simple.
    sequence={'dynamo_aegis':[0,0,1,1], 'aegis_switchyard':[1,1,2,2],
              'dynamo_switchyard':[0,0,2,2], 'no_build':[]}[mode]
    s=state
    # Forecast upcoming arrival is public. Use actual board and current storm wave.
    board=[*s['board'], *[dict(t,id=f'r{s["round"]}t{i}',depth=2,held=False)
                         for i,t in enumerate(s['waves'][s['round']-1])]]
    # Go after imminent charge mismatches; exhaustively check the best first edit
    # under the current unaltered storm, not secretly on future waves.
    def evaluate(acts):
        trial=[dict(t) for t in board]
        stopped=set(); coolant=s['coolant']
        from .common import apply_edit,move_and_breach
        for a in acts:
            if a['kind']=='DAMP':coolant-=1
            apply_edit(trial,a,stopped)
        _,breach=move_and_breach(trial,stopped)
        e=resolve(breach)
        return (e['total_match']*1.35 - e['raw_damage']*1.8
                -len(acts)*.22 - (s['coolant']-coolant)*.75)
    candidates=[]
    for t in board:
        if t['depth']!=1:continue
        for delta in (-1,1):
            if 0<=t['lane']+delta<=2:
                candidates.append(dict(kind='SHIFT',token=t['id'],delta=delta))
        if not t['held'] and s['round']<8:
            candidates.append(dict(kind='HOLD',token=t['id']))
        if s['coolant']>0:candidates.append(dict(kind='DAMP',token=t['id']))
    edits=[]; best=evaluate([])
    for a in candidates:
        val=evaluate([a])
        if val>best+1e-9: best=val; edits=[a]
    # A second action may make a weak first action useful; keep search bounded.
    for i,a in enumerate(candidates):
        for b in candidates[i+1:]:
            if a['token']==b['token'] or sum(x['kind']=='DAMP' for x in (a,b))>s['coolant']:
                continue
            val=evaluate([a,b])
            if val>best+1e-9: best=val; edits=[a,b]
    plan={'edits': edits}
    for target in sequence:
        current=s['levels'][target]+(s['pending']==target)
        if current<2:
            if s['power']>=2 and not s['outages'][target]: plan['build']=target
            break
    return plan


def run_engine(seed, mode):
    waves=engine_waves(seed)
    s=engine.new_game(waves)
    while s['finished'] is None:
        s=engine.step(s,engine_policy(s,mode))
    return s


def operations_policy(state, style='active'):
    if style=='pass': return [[] for _ in range(state['players'])]
    # Seats independently propose using ONLY their current hand and public board.
    # Each seat picks a one-edit mitigation; all other seats PASS when evaluating.
    # This deliberately weak heuristic misses multi-seat synergy: quantify this.
    from .common import move_and_breach, apply_edit
    r=state['round']; board=[*state['board'],
        *[dict(t,id=f'r{r}t{i}',depth=2,held=False)
          for i,t in enumerate(state['waves'][r-1])]]
    def score(acts):
        trial=[dict(t) for t in board]; stopped=set(); touched={}
        for action in acts:
            if action['token'] not in [t['id'] for t in trial]:continue
            try: apply_edit(trial,action,stopped,allow_fizzle=True)
            except ValueError: pass
            touched[action['token']]=touched.get(action['token'],0)+1
        _,breached=move_and_breach(trial,stopped)
        ev=resolve(breached)
        return ev['total_match']*1.2-ev['raw_damage']*2.3 -len(acts)*.12
    plans=[[] for _ in range(state['players'])]; planned=[]; used=Counter()
    for seat in range(state['players']):
        best=score(planned); selected=None
        for card in sorted(set(state['hands'][seat])):
            for t in board:
                if used[t['id']]>=2: continue
                if card in ('LEFT','RIGHT') and t['lane']+(1 if card=='RIGHT' else -1) not in (0,1,2): continue
                if card=='HOLD' and t['held']:continue
                a=dict(kind=card, token=t['id'])
                score_value=score(planned+[a])
                if score_value>best+1e-9:
                    best=score_value; selected=a
        if selected:
            plans[seat]=[selected];planned.append(selected);used[selected['token']]+=1
    return plans


def run_operations(seed,players,style='active'):
    waves=operations_waves(seed,players)
    missions=('deep_capture','precision_route','double_pulse')
    s=operations.new_game(waves,players,missions,seed)
    while s['finished'] is None:
        s=operations.step(s,operations_policy(s,style))
    return s


def survey(seeds=36):
    results=dict(engine={},operations={})
    for mode in ('dynamo_aegis','aegis_switchyard','dynamo_switchyard','no_build'):
        states=[run_engine(i+5000,mode) for i in range(seeds)]
        results['engine'][mode]=dict(wins=sum(s['finished']=='WIN' for s in states),
              avg_hull=round(sum(s['hull'] for s in states)/seeds,2),
              builds=sum(sum(h['build'] is not None for h in s['history']) for s in states),
              action_edits=sum(sum(len(h['edits']) for h in s['history']) for s in states))
    for players in range(1,5):
        records={}
        for style in ('pass','active'):
            states=[run_operations(i+7000,players,style) for i in range(seeds)]
            records[style]=dict(wins=sum(s['finished']=='WIN' for s in states),
                 average_rounds=round(sum(len(s['history']) for s in states)/seeds,2),
                 per_seat_actions=round(sum(sum(s['played_by']) for s in states)/(players*seeds),2),
                 avg_hull=round(sum(s['hull'] for s in states)/seeds,2))
        results['operations'][str(players)]=records
    # Count different strategies that survive and win in the SAME scenario.
    results['engine']['multiple_upgrade_paths_winning']=sum(
        sum(run_engine(i+5000,mode)['finished']=='WIN' for mode in
            ('dynamo_aegis','aegis_switchyard','dynamo_switchyard'))>=2
        for i in range(seeds))
    results['methodology']='Heuristic policies with full public current/next wave only; not difficulty or fun estimates.'
    return results


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--seeds',type=int,default=36)
    a.add_argument('--output',type=Path)
    args=a.parse_args()
    output=json.dumps(survey(args.seeds),indent=2)+'\n'
    if args.output:args.output.write_text(output)
    else:print(output)
