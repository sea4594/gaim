"""Paired full-session Phase 5 architecture diagnostics, NOT human co-op evaluation.

All modes use the *same* Storm Engine stormbook per seed and the same reactive
base agent. Scores compare outcomes within Engine; they do not constitute
meaningful assessments of human enjoyment or anti-quarterbacking.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from experiments.redesign_phase3 import engine
from experiments.redesign_phase3.survey import engine_policy,engine_waves
from experiments.redesign_phase5.coop import (owned_step,owners,edit_board,
    joint_step,construction_seats,guarded_step,imminent_after_primary)
from experiments.redesign_phase3.common import token_by_id

STRATEGIES=('dynamo_aegis','aegis_switchyard','dynamo_switchyard')


def own_assign(state, players, edits):
    """Match the original agent's proposed edits to legal current ownership.
    Rotate priority for collisions among seats; never fabricate new edits.
    This is conservative and disadvantages ownership vs re-optimization.
    """
    if players==1:return ({0:edits} if edits else {})
    lanes=owners(players,state['round']); board=edit_board(state)
    proposals={}; missed=0
    for edit in edits:
        token=token_by_id(board,edit['token'])
        eligible=[seat for seat in range(players) if lanes[seat]==token['lane'] and seat not in proposals]
        if eligible:
            # Rotate tie-breaking by round to avoid fixed-first-seat artifacts.
            seat=min(eligible,key=lambda i:((i-state['round']+1)%players))
            proposals[seat]=edit
        else:missed+=1
    return proposals


def legal_lane_opportunities(state,players):
    """Number of seats with at least one immediate legal SHIFT/HOLD/DAMP."""
    board=edit_board(state); lan=owners(players,state['round'])
    valid_lanes=set()
    for token in board:
        if token['depth'] in (1,2) and (token['lane'] in (0,1,2)):
            valid_lanes.add(token['lane'])
    return sum(l in valid_lanes for l in lan)


def last_round_rush(state, target):
    """Intentionally narrow rush policy so results aren't from clairvoyance."""
    return (target is not None and state['power']>=3 and state['round']==8 and
            state['levels'][target]+int(state['pending']==target)==1)


def run(seed, strategy,players,mode, *, trace=False):
    s=engine.new_game(engine_waves(seed))
    turns=[]
    tally=Counter(); seat_actions=[0]*players; seat_possible=[0]*players
    while s['finished'] is None:
        plan=engine_policy(s,strategy); n=s['round']; edits=plan['edits']
        board=edit_board(s); lanes=owners(players,n)
        for i,l in enumerate(lanes):
            seat_possible[i]+=int(any(t['lane']==l for t in board))
        if mode=='baseline':
            if trace:turns.append({'round':n,'plan':plan})
            nxt=engine.step(s,plan)
        elif mode=='owned':
            orders=own_assign(s,players,edits)
            tally['edit_proposals_lost']+=len(edits)-sum(len(v) if isinstance(v,list) else 1 for v in orders.values())
            tally['structural_non_editing_seats']+=max(0,players-2)
            tally['potential_lane_seats']+=legal_lane_opportunities(s,players)
            for i in orders:seat_actions[i]+=1
            if trace:turns.append({'round':n,'orders':orders,'build':plan.get('build')})
            nxt=owned_step(s,players,orders,ordinary_build=plan.get('build'))
        elif mode in ('joint_standard','joint_rush'):
            target=plan.get('build')
            if target is None:
                if trace:turns.append({'round':n,'proposal':None,'allocation':None,'edits':edits})
                nxt=joint_step(s,players,None,None,edits=edits)
            else:
                mode_selected='rush' if mode=='joint_rush' and last_round_rush(s,target) else 'standard'
                # Credit proposing/funding as *choices*, not tactical edits.
                a,b=construction_seats(players,n)
                tally['affordable_construction_rounds']+=1
                tally['separate_proposer_and_funder']+=int(a!=b)
                if mode_selected=='rush':tally['rushes']+=1
                if trace:turns.append({'round':n,'proposal':target,'allocation':mode_selected,'edits':edits})
                nxt=joint_step(s,players,target,mode_selected,edits=edits)
        else:raise ValueError('Unknown run mode')
        if mode=='baseline':tally['baseline_edits']+=len(edits)
        if mode=='owned':tally['owned_edits']+=len(nxt['history'][-1]['edits'])
        s=nxt
    output=dict(outcome=s['finished'],hull=s['hull'],levels=s['levels'],
                power=s['power'],rounds=len(s['history']),counts=dict(tally),
                seat_actions=seat_actions,seat_possible=seat_possible)
    if trace:output['replay']={'seed':seed,'strategy':strategy,'players':players,
                   'mode':mode,'waves':engine_waves(seed),'turns':turns}
    return output


def survey(start=121000,n=28):
    result={'methodology':{'seed_start':start,'seed_count':n,
        'paired':True,'notes': 'Heuristic agent re-used, no human tests; ownership policy filters original agent and is not re-optimized.'},
        'owned':{},'joint':{},'guarded':{}}
    for players in (1,2,3,4):
        baseline_wins=0; owned_wins=0; lost=0; silence=0; possible=0
        actions=[0]*players; lane_access=[0]*players
        for i in range(n):
            seed=start+i; strat=STRATEGIES[i%len(STRATEGIES)]
            base=run(seed,strat,players,'baseline')
            own=run(seed,strat,players,'owned')
            baseline_wins+=base['outcome']=='WIN';owned_wins+=own['outcome']=='WIN'
            lost+=own['counts'].get('edit_proposals_lost',0)
            silence+=own['counts'].get('structural_non_editing_seats',0)
            for seat in range(players):
                actions[seat]+=own['seat_actions'][seat]
                lane_access[seat]+=own['seat_possible'][seat]
        result['owned'][str(players)]={'baseline_wins':baseline_wins,'owned_wins':owned_wins,
             'filtered_desired_actions':lost,'minimum_inactive_edit_seat_rounds':silence,
             'executed_actions_per_seat':actions,'lane_access_opportunity_per_seat':lane_access}
    for players in (1,2,3,4):
        baseline=Counter();standard=Counter();rush=Counter()
        for i in range(n):
            seed=start+i;strat=STRATEGIES[i%len(STRATEGIES)]
            for mode,aggregate in [('baseline',baseline),('joint_standard',standard),('joint_rush',rush)]:
                game=run(seed,strat,players,mode)
                aggregate['wins']+=int(game['outcome']=='WIN')
                aggregate['hull_total']+=game['hull']
                for k,v in game['counts'].items():aggregate[k]+=v
        result['joint'][str(players)]={'baseline':dict(baseline),'standard':dict(standard),'rush':dict(rush)}
    # Benchmark guarded decisions against the EXACT committed information set.
    # A branch evaluated on a known board is reproducible by open informed play.
    triggers=Counter()
    for i in range(n):
        s=engine.new_game(engine_waves(start+i))
        s['board']=[dict(id='primary',lane=0,sign=1,strength=2,depth=1,held=False),
                    dict(id='backup',lane=1,sign=-1,strength=1,depth=1,held=False)]
        primary=dict(kind='SHIFT',token='backup',delta=-1)
        backup=dict(kind='DAMP',token='primary')
        for threshold in (1,2):
            conditional=guarded_step(s,2,primary,backup,dict(lane=0,min_leak=threshold))
            unconditional=engine.step(s,dict(edits=conditional['history'][-1]['edits']))
            for k in ('hull','power','coolant','levels','board','finished'):
                assert conditional[k]==unconditional[k]
            triggers['cases']+=1
            triggers['triggered']+=int(conditional['history'][-1]['guard']['triggered'])
            triggers['equivalent_to_informed_open_order']+=1
    result['guarded']=dict(triggers)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,default=121000)
    ap.add_argument('--n',type=int,default=28);ap.add_argument('--output',type=Path)
    a=ap.parse_args();data=json.dumps(survey(a.start,a.n),indent=2)+'\n'
    if a.output:a.output.write_text(data)
    else:print(data)
