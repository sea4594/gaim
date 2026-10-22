"""Manual text-only playground for the opt-in mechanics tournament.

Example: python3 -m experiments.play_tournament --mode bridge --seed 3
This does not connect to a server or change production rules.
"""
import argparse
from experiments.rules_tournament import MODES, Trial, planning_tokens, actions, step_trial


def describe(t):
    s=t.state
    print(f'\nROUND {s.round + 1}/9 | HP {s.hp} | POWER {s.progress} | COOLANT {s.coolant}')
    if t.bridge:
        b=t.bridge
        print(f'BRIDGE {b.source}->{b.dest} active {b.begins}-{b.ends}')
    if t.pledge:
        print(f'PLEDGE {t.pledge.source}->{t.pledge.dest} due {t.pledge.due}')
    for r in (2,1,0):
        print(('FAR ','SOON','NOW ')[2-r], ' | '.join(
            ' '.join(f'{"+" if z.sign>0 else "-"}{z.size}#{z.id}' for z in planning_tokens(t)
                     if z.row == r and z.lane == lane) or '·' for lane in range(3)))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=MODES,default='bridge')
    p.add_argument('--seed',type=int,default=3)
    a=p.parse_args()
    t=Trial.new(a.mode,a.seed)
    print('EXPERIMENT ONLY — not the live Charge Loom multiplayer rules.')
    print('Choose up to four edit numbers, separated by commas. Empty = pass. Ctrl-C exits.')
    while not t.state.over:
        describe(t)
        opts=[x for x in actions(t) if x[0]!='pass']
        for ix,option in enumerate(opts,1):
            print(f'{ix:2}. {option}')
        while True:
            try:
                raw=input('Edits> ').strip()
                indices=[int(s.strip()) for s in raw.split(',') if s.strip()] if raw else []
                if len(indices)>4 or any(ix not in range(1,len(opts)+1) for ix in indices):
                    raise ValueError('choose 0 to 4 valid edit numbers')
                nxt=step_trial(t,[opts[ix-1] for ix in indices])
                t=nxt
                break
            except ValueError as error:
                print(f'Invalid: {error}')
            except (EOFError,KeyboardInterrupt):
                print('\nSession stopped.')
                return
    print(f'\n{t.state.over} | HP {t.state.hp} | power {t.state.progress}')

if __name__=='__main__':main()
