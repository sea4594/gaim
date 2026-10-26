"""Counterfactual heuristic: rotate who gets FIRST chance to propose a move.

This intentionally uses the same card valuation and greedy procedure as the
Phase 3 policy, changing only the order of proposal authorship. That isolates
policy ordering as a confound in claims about 4-player agency.
"""
from __future__ import annotations
from collections import Counter
from experiments.redesign_phase3.common import move_and_breach, apply_edit, resolve
from experiments.redesign_phase3 import operations
from experiments.redesign_phase3.survey import operations_waves


def rotating_policy(state):
    n=state['players']; r=state['round']
    board=[*state['board'],*[dict(t,id=f'r{r}t{i}',depth=2,held=False)
            for i,t in enumerate(state['waves'][r-1])]]
    def score(actions):
        trial=[dict(t) for t in board]; stopped=set()
        for action in actions:
            if action['token'] not in [t['id'] for t in trial]: continue
            try:apply_edit(trial,action,stopped,allow_fizzle=True)
            except ValueError:pass
        _,breached=move_and_breach(trial,stopped)
        event=resolve(breached)
        return event['total_match']*1.2-event['raw_damage']*2.3-len(actions)*.12
    plans=[[] for _ in range(n)];planned=[];used=Counter()
    for seat in [(k+r-1)%n for k in range(n)]:
        best=score(planned);selected=None
        for card in sorted(set(state['hands'][seat])):
            for token in board:
                if used[token['id']]>=2:continue
                if card in ('LEFT','RIGHT') and token['lane']+(1 if card=='RIGHT' else -1) not in (0,1,2):continue
                if card=='HOLD' and token['held']:continue
                action=dict(kind=card,token=token['id'])
                v=score(planned+[action])
                if v>best+1e-9:best=v;selected=action
        if selected:
            plans[seat]=[selected];planned.append(selected);used[selected['token']]+=1
    return plans


def play_rotating(seed,n):
    s=operations.new_game(operations_waves(seed,n),n,
       ('deep_capture','precision_route','double_pulse'),seed)
    while s['finished'] is None:
        s=operations.step(s,rotating_policy(s))
    return s


def compare(n_seeds=40,start=91000):
    from experiments.redesign_phase3.survey import run_operations
    result={}
    for n in (2,3,4):
        old=[run_operations(start+i,n) for i in range(n_seeds)]
        rotated=[play_rotating(start+i,n) for i in range(n_seeds)]
        result[str(n)]={
            'seeds': n_seeds,
            'old_wins':sum(s['finished']=='WIN' for s in old),
            'rotated_wins':sum(s['finished']=='WIN' for s in rotated),
            'fixed_order_card_uses':[sum(s['played_by'][seat] for s in old) for seat in range(n)],
            'rotated_order_card_uses':[sum(s['played_by'][seat] for s in rotated) for seat in range(n)],
            'rotated_zero_card_wins':sum(s['finished']=='WIN' and any(k==0 for k in s['played_by']) for s in rotated),
            'changed_win_to_loss':sum(a['finished']=='WIN' and b['finished']!='WIN' for a,b in zip(old,rotated)),
            'changed_loss_to_win':sum(a['finished']!='WIN' and b['finished']=='WIN' for a,b in zip(old,rotated)),
        }
    return result
