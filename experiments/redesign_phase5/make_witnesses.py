"""Select and verify complete legal session witnesses from fixed public seed ranges."""
from __future__ import annotations
import json
from pathlib import Path
from experiments.redesign_phase3 import engine
from .coop import joint_step,owned_step
from .survey import run,STRATEGIES


def replay(game):
    r=game['replay'];s=engine.new_game(r['waves'])
    for turn in r['turns']:
        assert turn['round']==s['round']
        if r['mode']=='baseline':
            s=engine.step(s,turn['plan'])
        elif r['mode']=='owned':
            s=owned_step(s,r['players'],{int(k):v for k,v in turn['orders'].items()},
                         ordinary_build=turn['build'])
        elif r['mode'] in ('joint_rush','joint_standard'):
            s=joint_step(s,r['players'],turn['proposal'],turn['allocation'],edits=turn['edits'])
        else:raise ValueError('Unrecognized witness mode')
    assert s['finished']==game['outcome']
    assert s['hull']==game['hull']
    assert s['levels']==game['levels']
    assert s['power']==game['power']
    assert len(s['history'])==game['rounds']
    return s


def collect():
    results={'description':'Full session decisions; exact reducer replay; no human playtest','witnesses':{}}
    found={}
    for seed in list(range(121000,121040))+list(range(122000,122040)):
        strategy=STRATEGIES[(seed-(121000 if seed<122000 else 122000))%len(STRATEGIES)]
        base=run(seed,strategy,4,'baseline')
        own=run(seed,strategy,4,'owned')
        rush=run(seed,strategy,4,'joint_rush')
        if base['outcome']!='WIN' and rush['outcome']=='WIN' and 'rush_rescue' not in found:
            found['rush_rescue']=(seed,strategy,'joint_rush')
        if base['outcome']=='WIN' and own['outcome']!='WIN' and 'owned_loss' not in found:
            found['owned_loss']=(seed,strategy,'owned')
        if len(found)==2:break
    assert len(found)==2,found
    for label,(seed,strategy,mode) in found.items():
        results['witnesses'][label]=[
            run(seed,strategy,4,'baseline',trace=True),
            run(seed,strategy,4,mode,trace=True)]
        for game in results['witnesses'][label]:replay(game)
    return results


if __name__=='__main__':
    dest=Path(__file__).resolve().parents[2]/'docs/redesign/phase05-full-session-witnesses.json'
    dest.write_text(json.dumps(collect(),indent=2)+'\n')
    print(dest)
