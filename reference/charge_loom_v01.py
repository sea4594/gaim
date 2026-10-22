"""GAIM Phase 5 CHARGE LOOM provisional rules v0.1. Headless reference, not production.
Three lanes by three time bands. All outstanding charges incur end-of-game liability.
"""
from dataclasses import dataclass, replace
from functools import lru_cache
from itertools import combinations
import random

@dataclass(frozen=True,order=True)
class Token:
    id: int
    lane: int
    row: int
    sign: int
    size: int
    held: int = 0 # may hold at most once in lifetime

@dataclass(frozen=True)
class State:
    round: int=0
    hp: int=7
    progress: tuple=(0,0,0)
    coolant: int=3
    tokens: tuple=()
    next_id: int=1
    seed: int=0
    over: str=''

TURNS=9

@lru_cache(maxsize=4096)
def wavebook(seed):
    """Seven public-wave turns generated from a balanced signed bag. The eighth and ninth are cleanup beats."""
    rng=random.Random(seed*1597+73)
    sizes=[3,2,3,2,3,2,3]
    for _ in range(1000):
        signs=[1]*9+[-1]*9
        rng.shuffle(signs)
        # Avoid pathological three-beat polarity runs. Still permits tactically uneven waves.
        windows=[]; pos=0
        for n in sizes:windows.append(signs[pos:pos+n]);pos+=n
        if all(any(s==1 for row in windows[i:i+3] for s in row) and any(s==-1 for row in windows[i:i+3] for s in row) for i in range(5)):
            break
    waves=[];ix=0
    for count in sizes:
        row=[]
        for _ in range(count):
            row.append((rng.randrange(3),signs[ix],rng.choice((1,1,2))))
            ix+=1
        waves.append(tuple(row))
    return tuple(waves)

def arrivals(seed,roundnum):
    return wavebook(seed)[roundnum-1] if 1<=roundnum<=7 else ()

def start(seed=0): return State(seed=seed)

def options(s):
    result=[('pass',)]
    for t in s.tokens:
        if t.lane>0:result.append(('shift',t.id,-1))
        if t.lane<2:result.append(('shift',t.id,1))
        if t.held==0:result.append(('hold',t.id))
        if s.coolant and t.size>0:result.append(('damp',t.id))
    # arrive at beginning of round, so options visible for next turn cannot include newly spawned threats
    return result

def step(s,actions=()):
    if s.over:raise ValueError('game ended')
    if len(actions)>4:raise ValueError('only four edits')
    roundnum=s.round+1
    toks=list(s.tokens)
    nid=s.next_id
    for lane,sign,size in arrivals(s.seed,roundnum):
        toks.append(Token(nid,lane,2,sign,size));nid+=1
    used=set();hold=set(); coolant=s.coolant
    for action in actions:
        typ=action[0]
        if typ=='pass':continue
        if typ not in ('shift','hold','damp'):raise ValueError('bad action')
        tid=action[1]
        if tid in used: raise ValueError('one edit per token per round')
        used.add(tid)
        i=next((i for i,t in enumerate(toks) if t.id==tid),None)
        if i is None: raise ValueError('bad id')
        t=toks[i]
        if typ=='shift':
            d=action[2]
            if d not in (-1,1) or not 0<=t.lane+d<3:raise ValueError('bad shift')
            toks[i]=replace(t,lane=t.lane+d)
        if typ=='hold':
            if t.held:raise ValueError('used hold')
            toks[i]=replace(t,held=1,size=min(3,t.size+1))
            hold.add(tid)
        if typ=='damp':
            if coolant==0:raise ValueError('out of coolant')
            coolant-=1
            toks[i]=replace(t,size=t.size-1)
    toks=[t for t in toks if t.size>0]
    # all except held tokens move toward breach; bottom row -1 breaches
    moved=[]
    for t in toks:
        moved.append(t if t.id in hold else replace(t,row=t.row-1))
    breach=[t for t in moved if t.row<0]
    kept=tuple(sorted((t for t in moved if t.row>=0)))
    hp=s.hp;points=list(s.progress)
    for lane in range(3):
        plus=sum(t.size for t in breach if t.lane==lane and t.sign==1)
        minus=sum(t.size for t in breach if t.lane==lane and t.sign==-1)
        points[lane]=min(3,points[lane]+min(plus,minus))
        hp-=abs(plus-minus)
    over=''
    # No artificial victory by storing storm charges past the round-nine deadline.
    # After ordinary synchronized breach resolution, any still-unresolved charge
    # becomes unpaired leakage, not objective energy (time bands cannot match).
    if roundnum==TURNS:
        hp-=sum(t.size for t in kept)
        kept=()
    if hp<=0:over='loss: breach'
    elif roundnum==TURNS:
        over='win' if min(points)>=2 and sum(points)>=8 else 'loss: target'
    return State(roundnum,hp,tuple(points),coolant,kept,nid,s.seed,over)


def legal_actions(s):
    """generate edits on current and newly spawned tokens for current turn"""
    toks=list(s.tokens);nid=s.next_id
    for lane,sign,size in arrivals(s.seed,s.round+1):toks.append(Token(nid,lane,2,sign,size));nid+=1
    d=[('pass',)]
    for t in toks:
        if t.lane>0:d.append(('shift',t.id,-1))
        if t.lane<2:d.append(('shift',t.id,1))
        if not t.held:d.append(('hold',t.id))
        if s.coolant:d.append(('damp',t.id))
    return d

def score(s):
    if s.over=='win':return 10000
    if s.over.startswith('loss: breach'):return -10000
    # consider target distribution rather than just total matches
    return 4*s.hp+ 7*sum(min(4,p) for p in s.progress) +8*min(s.progress) +2*s.coolant + 0.5*sum(t.size for t in s.tokens)

def greedy(s):
    acts=[];best=score(step(s,acts));used=set()
    for _ in range(4):
        candidate=None
        for a in legal_actions(s):
            if a[0]=='pass' or a[1] in used: continue
            try: n=step(s,acts+[a])
            except ValueError: continue
            value=score(n)
            if value>best+1e-8:
                best=value;candidate=a
        if candidate is None:break
        acts.append(candidate);used.add(candidate[1])
    return acts

if __name__=='__main__':
    for seed in range(10):
        s=start(seed)
        while not s.over:
            a=greedy(s);s=step(s,a)
        print(seed,s.over,s.progress,s.hp)
