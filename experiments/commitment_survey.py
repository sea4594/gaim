"""Exact two-turn commitment microstates (round 7 purchase; rounds 8–9 resolve).

Known, fixed board threats: no future RNG arrivals at rounds 8–9. The full
4-edit action budget is irrelevant because this survey intentionally compares
purchase-now/pass-later vs pass throughout on the SAME fixed storm. It is a
controlled return-on-investment study, not an optimal-policy tournament.
"""
from itertools import product
from collections import Counter
from reference.charge_loom_v01 import State, Token
from experiments.rules_tournament import Trial, step_trial


def samples():
    for source, target in ((0,1), (1,0), (1,2), (2,1)):
        # one, two or zero guaranteed source collisions after investment
        for pairs in (0,1,2):
            for power in product((0,1,2,3), repeat=3):
                if power[source] < 1:
                    continue
                toks = []
                if pairs >= 1:
                    toks += [Token(1,source,1,1,1),Token(2,source,1,-1,1)]
                if pairs == 2:
                    toks += [Token(3,source,2,1,1),Token(4,source,2,-1,1)]
                # For pairs == 0 the source is dry, to test purchase risk.
                state = State(round=6, hp=4, progress=power, coolant=3,
                              tokens=tuple(toks), next_id=len(toks)+1)
                yield source,target,pairs,state


def run(mode, state, purchase=None):
    t = Trial(state, mode, waves=tuple(() for _ in range(9)))
    t = step_trial(t, [purchase] if purchase else [])
    t = step_trial(t)
    t = step_trial(t)
    return t.state


def survey():
    tally = {m: Counter() for m in ('bridge','contract')}
    examples = {m: {} for m in tally}
    for source,target,pairs,s in samples():
        for mode in tally:
            baseline=run(mode,s)
            buy=run(mode,s,(mode,source,target))
            # Compare win/loss and power; identical generation under no purchase.
            win_base=baseline.over == 'win'; win_buy=buy.over == 'win'
            key=('good' if win_buy and not win_base else
                 'bad' if win_base and not win_buy else 'same')
            tally[mode][key] += 1
            tally[mode][f'{pairs}_pairs_{key}'] += 1
            if key not in examples[mode]:
                examples[mode][key] = {'source':source,'target':target,'pairs':pairs,'power':s.progress,
                                       'pass_result': (baseline.over, baseline.progress, baseline.hp),
                                       'purchase_result': (buy.over,buy.progress,buy.hp)}
    return {'cases_per_variant':sum(tally['bridge'][k] for k in ('good','bad','same')),
            'results':{m:dict(c) for m,c in tally.items()},'examples':examples}

if __name__ == '__main__':
    import json
    print(json.dumps(survey(),indent=2))
