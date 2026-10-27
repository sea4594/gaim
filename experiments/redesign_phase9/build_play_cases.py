"""Export reproducible human-playable wavebooks and independent Python witnesses."""
from __future__ import annotations
import json
from pathlib import Path
from experiments.redesign_phase3 import engine, survey

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'site/play-cases.json'
SEEDS=[(5000,'First watch','Learn the flow; several investments can work.'),
       (5009,'Tough current','Defense and positioning are especially important.'),
       (5011,'Power surge','Different settlement builds can succeed.')]


def render():
    games=[]
    for seed,label,description in SEEDS:
        waves=survey.engine_waves(seed)
        state=engine.new_game(waves)
        steps=[]
        while state['finished'] is None:
            plan=survey.engine_policy(state,'aegis_switchyard' if seed==5009 else 'dynamo_aegis')
            before={k:state[k] for k in ('round','hull','power','coolant','levels','pending','outages','board')}
            state=engine.step(state,plan)
            steps.append({'before':before,'plan':plan,'after':state})
        games.append({'id':str(seed),'title':label,'description':description,
                      'waves':waves,'example':steps,'example_result':state['finished']})
    return json.dumps({'ruleset':'redesign/phase3-storm-engine','export':'phase9-browser-play-parity-v1',
            'note':'Complete eight-round experimental Storm Engine, NOT the published production v0.1 reducer.',
            'games':games},indent=2,sort_keys=True)+'\n'

if __name__=='__main__':OUTPUT.write_text(render())
