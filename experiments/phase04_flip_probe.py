"""Check if polarity reversal is a real choice or near-dominant cheap rescue."""
from collections import Counter
import json
from experiments.phase04_lab import Lab, step, options
from experiments.rules_tournament import score


def immediate_impact(seeds=80):
    counts=Counter()
    for seed in range(seeds):
        g=Lab.new('flip',seed)
        while not g.trial.state.over:
            baseline_score=score(step(g).trial)
            impacts=[]
            for a in options(g):
                if a[0]!='flip': continue
                try:v=score(step(g,[a]).trial)-baseline_score
                except ValueError:continue
                impacts.append(v)
                counts['candidate_actions']+=1
                counts['good' if v>1e-9 else ('bad' if v<-1e-9 else 'neutral')]+=1
            if impacts:
                counts['rounds_with_flip']+=1
                counts['both_good_bad_available']+=any(v>1e-9 for v in impacts) and any(v<-1e-9 for v in impacts)
                counts['only_good_available']+=all(v>1e-9 for v in impacts)
                counts['only_bad_available']+=all(v<-1e-9 for v in impacts)
            # Follow the same one-step greedy selection used by main tournament.
            planned=[];best=baseline_score
            for _ in range(4):
                winner=None
                for a in options(g):
                    if a[0]=='pass' or a in planned:continue
                    try:
                        current=score(step(g,planned+[a]).trial)
                    except (ValueError,TypeError):continue
                    if current>best+1e-9:
                        best=current;winner=a
                if winner is None:break
                planned.append(winner)
            g=step(g,planned)
    return {'seeds':seeds,'counts':dict(counts),'warning':'single-action immediate score, conditional on states reached by one-step greedy policy'}


def reckless(seeds=80):
    results=Counter()
    for seed in range(seeds):
        g=Lab.new('flip',seed)
        while not g.trial.state.over:
            force=next((a for a in options(g) if a[0]=='flip'),None)
            chosen=[force] if force is not None else []
            if force:results['forced_flips']+=1
            # Greedy can add remaining moves, but cannot undo the forced purchase.
            best=score(step(g,chosen).trial)
            for _ in range(4-len(chosen)):
                winner=None
                for a in options(g):
                    if a[0]=='pass' or a in chosen:continue
                    try:v=score(step(g,chosen+[a]).trial)
                    except (ValueError,TypeError):continue
                    if v>best+1e-9:best=v;winner=a
                if winner is None: break
                chosen.append(winner)
            g=step(g,chosen)
        results['wins']+=g.trial.state.over=='win'
        results['survivals']+=g.trial.state.hp>0
    return {'seeds':seeds,'results':dict(results),
            'warning':'reversal first on the first legal target is intentionally reckless and has other greedy support edits'}

if __name__=='__main__':
    print(json.dumps({'immediate':immediate_impact(80),'reckless':reckless(80)},indent=2))
