"""Save paired full-game staffing rescues and counterexamples; replay every one."""
from pathlib import Path
import json
from experiments.redesign_phase3 import engine
from .survey import play, replay, STRATEGIES

OUT=Path(__file__).resolve().parents[2]/'docs/redesign/phase06-crew-witnesses.json'


def build():
    records=[]
    for seed in (231001,231003,232005):
        mode=STRATEGIES[(seed-(231000 if seed<232000 else 232000))%3]
        variants={}
        for variant in ('fixed','flexible'):
            sample=play(seed,mode,variant,players=4,record=True)
            state=replay(sample['waves'],sample['decisions'],4)
            assert state['finished']==sample['outcome'] and state['hull']==sample['hull']
            variants[variant]=sample
        records.append({'seed':seed,'mode':mode,'variants':variants})
    return {'purpose':'Exact public wavebooks, staffed seats and orders for reproducible full sessions. Research only.',
            'witnesses':records}


if __name__=='__main__':
    OUT.write_text(json.dumps(build(),indent=2)+'\n')
    print('wrote',OUT)
