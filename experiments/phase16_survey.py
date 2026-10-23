"""Small deterministic paired exploration of costly guarded orders. Research only."""
from __future__ import annotations
import argparse,json,random
from collections import Counter
from experiments.phase15_survey import base_board,wave
from experiments.phase15_forecast_council import make_world,payoff_table
from experiments.phase16_conditional_commitments import best_fixed,best_guarded


def survey(count=24,start=261600,horizon=3):
    rng=random.Random(start)
    totals=Counter();best=None
    for seed in range(start,start+count):
        board=base_board(seed)
        worlds=[make_world(board,wave(rng,2),wave(rng,2)) for _ in range(4)]
        tables=[payoff_table(g,horizon=horizon) for g in worlds]
        b=best_fixed(tables)
        c,order=best_guarded(tables,worlds)
        totals['boards']+=1
        totals['fixed_sum']+=b
        totals['guarded_sum']+=c
        if order:
            totals['strictly_better']+=1
            if best is None or c-b>best['delta']:
                best={'seed':seed,'delta':round(c-b,5),'guard':order.kind,
                      'if_true':order.when_true,'if_false':order.when_false,
                      'mean_fixed_score':round(b,5),'mean_guarded_score':round(c,5)}
    return {'method':'Four synthetic hidden worlds per reached board, truthful storm-card predicate, best one-edit fixed action vs two-slot guard (one action actually executes). Both evaluations use 3-round passive continuation heuristic.',
            'sample':count,'start':start,'horizon':horizon,
            'strict_guard_improvements':totals['strictly_better'],
            'mean_fixed':round(totals['fixed_sum']/count,4),
            'mean_guarded_upper':round(totals['guarded_sum']/count,4),
            'best_example':best,
            'limitations':['Guarded value is an optimistic upper bound using all hidden-world payoffs for choosing branches.',
                'Two reserved edit slots impose a cost not subtracted from the numeric heuristic.',
                'Synthetic future cards differ from production storm generator.',
                'Present public Storm Market reveals cards already; guard only relevant with revised advance-information schedule.',
                'No evidence about real human communication or quarterbacking.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=24);p.add_argument('--start',type=int,default=261600);args=p.parse_args()
    print(json.dumps(survey(args.count,args.start),indent=2,default=list))
