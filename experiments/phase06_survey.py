"""Pass 06 paired-policy evaluation. Reproducible diagnostics, NOT playtest scores.

One-step greedy policy has imperfect long-term vision; metrics are expressly
restricted to mechanical feasibility, action frequency, and policy dependence.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import replace
import json, random, argparse
from reference.charge_loom_v01 import State,Token
from experiments.phase06_lab import Experiment,step,opportunities,hand
from experiments.phase05_survey import utility

MODES=('open','market','paid_market','operator','market_operator','recycle','regulator','market_recycle','paid_market_recycle')


def value(g:Experiment):
    return utility(g.game)


def plan(g:Experiment, lookahead=1):
    """Select draft and up to four actions; each candidate is validated by reducer.

    The same one-round utility drives every variant. Card constraints are
    explicit and NEVER ignored when selecting an operator action.
    """
    drafts=range(len(g.game.available)) if 'market' in g.mode and g.state.round<7 else (None,)
    best_overall=None
    for draft in drafts:
        chosen=[];seat_ids=[]
        try:baseline=value(step(g,chosen,draft=draft,operators=seat_ids))
        except (ValueError,TypeError):continue
        # Operator consoles make their own one choice in console order; others
        # have a shared pool of four actions. Both can pass.
        if 'operator' in g.mode:
            choices=range(4)
        else:choices=range(4)
        for console in choices:
            if g.mode.startswith('paid_market') and draft==1 and console==3:continue
            best=baseline;best_action=None
            for a in opportunities(g,draft or 0):
                if 'operator' in g.mode and a[0] not in hand(g.state.seed,g.state.round)[console]:continue
                if 'operator' not in g.mode and a in chosen:continue
                try:
                    score=value(step(g,chosen+[a],draft=draft,operators=seat_ids+[console]))
                except (ValueError,TypeError,KeyError,IndexError):continue
                if score>best+1e-9:
                    best=score;best_action=a
            if best_action is not None:
                chosen.append(best_action);seat_ids.append(console);baseline=best
        # Optional next-round market lookahead, still myopic for token actions.
        # NOTE: only one recursive lookahead layer, not an optimal solution.
        compared=baseline
        if lookahead>1:
            outcome=step(g,chosen,draft=draft,operators=seat_ids)
            if not outcome.state.over:
                next_actions,next_draft,next_owners,_=plan(outcome,lookahead=1)
                compared=value(step(outcome,next_actions,draft=next_draft,operators=next_owners))
            else:compared=value(outcome)
        candidate=(compared,tuple(chosen),draft,tuple(seat_ids),baseline)
        if best_overall is None or candidate[0]>best_overall[0]+1e-9:
            best_overall=candidate
    if best_overall is None:raise RuntimeError('no legal plan')
    _,actions,draft,consoles,score=best_overall
    return actions,draft,consoles,score


def survey(n=16,seed_start=8100,lookahead=1):
    result={}
    for mode in MODES:
        total=Counter()
        for seed in range(seed_start,seed_start+n):
            g=Experiment.new(mode,seed)
            turns=0
            while not g.state.over:
                acts,draft,consoles,_=plan(g,lookahead=lookahead)
                bought_draft=int(mode.startswith('paid_market') and draft==1)
                total['edits']+=len(acts) + bought_draft
                total['inactive_slots']+=4-len(acts)-bought_draft
                total['active_console_rounds']+=len(set(consoles))
                total['draft_second']+=int(draft==1)
                total.update('action_'+a[0] for a in acts)
                g=step(g,acts,draft=draft,operators=consoles)
                turns+=1
                if turns>9:raise AssertionError('unexpected game length')
            total['games']+=1
            total['wins']+=g.state.over=='win'
            total['alive']+=g.state.hp>0
            total['hp_sum']+=max(0,g.state.hp)
            total['power_sum']+=sum(g.state.progress)
            total['rounds']+=turns
        result[mode]=dict(total)
    return {'seed_range':[seed_start,seed_start+n-1], 'lookahead':lookahead,
            'caveat':'Policy comparison only, rule accessibility and scripted wins are NOT quality/fun measures', 'variants':result}


def legality_probe(n=160,seed=333):
    """How much does action-menu drafting remove from one-step choices?

    Sample states from original reference engine using the same *no-edit*
    rollout; compare availability of verb categories, not relative win rate.
    """
    rng=random.Random(seed);cnt=Counter()
    for index in range(n):
        round_index=rng.randrange(0,9)
        toks=[]
        for i in range(rng.randint(2,5)):
            toks.append(Token(i+1,rng.randrange(3),rng.randrange(3),rng.choice((-1,1)),rng.choice((1,2))))
        progress=tuple(rng.randrange(4) for _ in range(3))
        s=State(round=round_index,hp=rng.randint(1,7),progress=progress,
                coolant=rng.randrange(4),tokens=tuple(toks),next_id=len(toks)+1,seed=seed+index)
        wave=tuple(() for _ in range(9))
        g=Experiment.new('operator',seed=seed+index,state=s,waves=wave)
        open_g=Experiment.new('open',seed=seed+index,state=s,waves=wave)
        available=set(a[0] for a in opportunities(open_g))
        menus=hand(g.state.seed,g.state.round)
        served=set(x for pair in menus for x in pair)
        cnt['cases']+=1
        cnt['available_type_total']+=len(available)
        cnt['missing_action_type_cases']+=bool(available-served)
        cnt['unavailable_categories_total']+=len(available-served)
        cnt['zero_legal_card_console_total']+=sum(not any(x in available for x in pair) for pair in menus)
        cnt['all_four_consoles_have_legal_category']+=all(any(x in available for x in pair) for pair in menus)
    return dict(cnt)


def draft_order_probe(n=120,seed=951):
    """Exact 7-step two-offer order selection with no token edits.

    All 7 waves used exactly once; analyze how often wave ORDER alone changes
    outcome. Start from randomized near-win states to make order relevant.
    """
    rng=random.Random(seed);cnt=Counter();examples={}
    for case in range(n):
        # Deterministic, hand constructed small deck with two threats that may pair.
        deck=[]
        for i in range(7):
            deck.append(((rng.randrange(3),rng.choice((-1,1)),rng.choice((1,2))),))
        waves=tuple(deck)+((),())
        power=tuple(rng.choice((0,1,2,3)) for _ in range(3))
        s=State(seed=seed+case,progress=power,hp=rng.randint(2,7))
        base=Experiment.new('open',state=s,waves=waves)
        while not base.state.over:base=step(base)
        # Exhaust complete 2-offer choice trees: at most 2**6 unique permutations.
        frontier=[(Experiment.new('market',state=s,waves=waves),())]
        for turn in range(7):
            nxt=[]
            for g,record in frontier:
                if g.state.over:
                    nxt.append((g,record));continue
                for choice in range(len(g.game.available)):
                    nxt.append((step(g,draft=choice),record+(choice,)))
            frontier=nxt
        endings=[]
        for g,rec in frontier:
            while not g.state.over:g=step(g)
            endings.append((g.state.over=='win',g.state.hp,g.state.progress,rec))
        cnt['cases']+=1
        wins=sum(x[0] for x in endings)
        cnt['market_some_win']+=wins>0
        cnt['market_all_win']+=wins==len(endings)
        cnt['market_mixed_win']+=0<wins<len(endings)
        cnt['base_win']+=base.state.over=='win'
        cnt['market_better_final_hp_possible']+=max(x[1] for x in endings)>base.state.hp
        cnt['market_worse_final_hp_possible']+=min(x[1] for x in endings)<base.state.hp
        if 0<wins<len(endings) and 'win_and_loss' not in examples:
            good=next(x for x in endings if x[0]);bad=next(x for x in endings if not x[0])
            examples['win_and_loss']={'case':case,'power':power,'deck':deck,
                                      'win_choices':good[3],'loss_choices':bad[3],
                                      'win_state':good[:3],'loss_state':bad[:3]}
    return {'diagnostics':dict(cnt),'example':examples,
            'caveat':'no-edit storm-order stress test; 2**6 choices per seed, includes many unwinnable seeds'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--games',type=int,default=12)
    parser.add_argument('--draft-cases',type=int,default=120)
    parser.add_argument('--lookahead',type=int,default=1)
    args=parser.parse_args()
    print(json.dumps({'games':survey(args.games,lookahead=args.lookahead),
                      'legality':legality_probe(),
                      'draft_order':draft_order_probe(args.draft_cases)},indent=2))
