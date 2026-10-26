"""Generate replayable complete eight-round witness data with no random handwaving."""
import json
from pathlib import Path
from . import engine, operations, survey


def generate():
    document={}
    fixture=json.loads((Path(__file__).resolve().parents[2]/'docs/redesign/phase02-sanity-fixtures.json').read_text())
    f=fixture['engine'];builds={int(k):{'build':v} for k,v in f['builds'].items()}
    eng=engine.play(f['rounds'],builds)
    document['engine_phase02_fixture']={'waves':f['rounds'],'decisions':builds,'outcome':eng['finished'],
              'history':eng['history'],'final_levels':eng['levels']}
    # Prefer a genuinely contested result: two plans win, third does not.
    for seed in range(5000,5090):
        states={m:survey.run_engine(seed,m) for m in
              ('dynamo_aegis','aegis_switchyard','dynamo_switchyard')}
        if states['dynamo_aegis']['finished']==states['aegis_switchyard']['finished']=='WIN' and states['dynamo_switchyard']['finished']!='WIN':
            document['engine_contested_seed']={'seed':seed,'waves':survey.engine_waves(seed),
                'results':{k:dict(outcome=v['finished'],levels=v['levels'],hull=v['hull'],
                    history=v['history']) for k,v in states.items()}}
            break
    operations_witness={}
    for players in (1,2,3,4):
        found=False
        for seed in range(7000,7070):
            active=survey.run_operations(seed,players,'active')
            passive=survey.run_operations(seed,players,'pass')
            if active['finished']=='WIN' and passive['finished']!='WIN' and sum(active['played_by']):
                initial=operations.new_game(survey.operations_waves(seed,players),players,
                     ['deep_capture','precision_route','double_pulse'],seed)
                operations_witness[str(players)]=dict(seed=seed,players=players,
                     waves=initial['waves'],starting_hands=initial['hands'],
                     active=dict(outcome=active['finished'],hull=active['hull'],
                           played_by=active['played_by'],completed=operations.completed(active),
                           history=active['history']),
                     passive=dict(outcome=passive['finished'],hull=passive['hull'],
                                  last_round=passive['history'][-1]['round']))
                found=True
                break
        if not found:raise AssertionError(f'No win vs loss for {players}p')
    document['operations_by_player_count']=operations_witness
    return document

if __name__=='__main__':
    p=Path(__file__).resolve().parents[2]/'docs/redesign/phase03-full-game-witnesses.json'
    p.write_text(json.dumps(generate(),indent=2,sort_keys=True)+'\n')
    print(p)
