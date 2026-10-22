"""Manual headless prototype. Research only; not a network client."""
import argparse
from experiments.phase04_lab import Lab, options, step
from experiments.rules_tournament import planning_tokens


def show(game):
    s=game.trial.state
    print(f'\nRound {s.round+1}/9 | Hull {s.hp} | Capacitors {s.progress} | Coolant {s.coolant}')
    if game.trial.bridge:
        print('BRIDGE:',game.trial.bridge)
    if game.resonator:
        print('RESONATOR:',game.resonator)
    for r in (2,1,0):
        row=[]
        for lane in range(3):
            ts=[t for t in planning_tokens(game.trial) if t.row==r and t.lane==lane]
            row.append(' '.join(f'#{t.id}{"+" if t.sign==1 else "-"}{t.size}{"h" if t.held else ""}' for t in ts) or '.')
        print(['NOW','SOON','FAR'][r], ' | '.join(f'{a:24.24}' for a in row))


def main():
    ap=argparse.ArgumentParser(description='Research-only Charge Loom actions; production rules unchanged.')
    ap.add_argument('--mode',default='bridge_flip',choices=('baseline','bridge','split','flip','transfer','resonator','bridge_split','bridge_flip'))
    ap.add_argument('--seed',type=int,default=3)
    args=ap.parse_args()
    g=Lab.new(args.mode,args.seed)
    while not g.trial.state.over:
        show(g)
        legal=options(g)
        print('Candidate edits (you may submit up to four):')
        for ix,a in enumerate(legal):print(f'  {ix:2d}. {a}')
        entered=input('Action numbers, comma separated; blank passes > ').strip()
        if not entered:planned=[]
        else:
            try:planned=[legal[int(i.strip())] for i in entered.split(',')]
            except (ValueError,IndexError):
                print('Invalid action index');continue
        try:g=step(g,planned)
        except (ValueError,TypeError) as e:
            print('Rejected:',e);continue
        print('Resolved:',g.trial.state.progress,'hull',g.trial.state.hp)
    print('\nOutcome:',g.trial.state.over,'Final:',g.trial.state.progress,'Hull:',g.trial.state.hp)

if __name__=='__main__':main()
