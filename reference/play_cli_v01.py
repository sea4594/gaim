"""Headless local play for the experimental GAIM Charge Loom rules.
Run: python3 play_cli.py --seed 4
This is a v0.1 experimental terminal harness, not network multiplayer or mobile UI.
"""
from charge_loom_v01 import start,step,arrivals,Token
import argparse


def visible(s):
    new=[];idx=s.next_id
    for lane,sign,size in arrivals(s.seed,s.round+1):
        new.append(Token(idx,lane,2,sign,size));idx+=1
    return tuple(sorted(s.tokens+tuple(new)))


def printed(s):
    print(f'\n=== Round {s.round+1}/9 | hull {s.hp}/7 | capacitors {s.progress} (cap 3 each; goal 8 total and at least 2 each) | coolant {s.coolant}/3 ===')
    tokens=visible(s)
    for row in (2,1,0):
        cells=[]
        for lane in range(3):
            v=[t for t in tokens if t.row==row and t.lane==lane]
            cells.append(' '.join(f'#{t.id}{"+" if t.sign==1 else "-"}{t.size}{"*" if t.held else ""}' for t in v) or '·')
        print(('FAR   ' if row==2 else 'SOON  ' if row==1 else 'NOW   ')+' | '.join(f'{c:17}' for c in cells))
    future=arrivals(s.seed,s.round+2)
    if future:print('Next incoming wave:', ', '.join(f'{"LCR"[l]}{"+" if sign==1 else "-"}{size}' for l,sign,size in future))
    print('Moves: S <id> L/R (shift one lane); H <id> (hold; strengthens +1, once in lifetime); D <id> (damp size -1, costs coolant); DONE. Max 4, one edit per token.')
    print('WARNING: On round 9, all storm tokens not yet breached leak their FULL strength as hull damage.')


def parse(line):
    p=line.strip().upper().split()
    if not p: return None
    if p[0] in ('DONE','GO'):return ('done',)
    if len(p)==3 and p[0]=='S' and p[1].isdigit() and p[2] in ('L','R'):
        return ('shift',int(p[1]),(-1 if p[2]=='L' else 1))
    if len(p)==2 and p[1].isdigit() and p[0] in ('H','D'):
        return (('hold' if p[0]=='H' else 'damp'),int(p[1]))
    raise ValueError('Unrecognized edit')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=2)
    seed=parser.parse_args().seed;s=start(seed)
    while not s.over:
        printed(s);a=[]
        while len(a)<4:
            try:
                v=parse(input(f'edit {len(a)+1}/4> '))
                if v is None:continue
                if v[0]=='done':break
                step(s,a+[v]) # immediate legality check
                a.append(v)
            except ValueError as ex:print('Invalid:',ex)
            except (EOFError,KeyboardInterrupt): print('\nStopped');return
        s=step(s,a)
        print(f'RESULT: HP {s.hp} | charge {s.progress} | stored coolant {s.coolant} | {s.over or "continue"}')
    print('*** '+s.over.upper()+' ***')

if __name__=='__main__':main()
