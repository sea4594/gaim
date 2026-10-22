"""Pass 04: independent, opt-in alternative mechanical engines.

Preserve the shipping v0.1 rules untouched. Explicit input waves and pure
step transitions allow exact replay. These are hypotheses, not playtest data.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from reference.charge_loom_v01 import State, Token, arrivals, TURNS
from experiments.rules_tournament import Trial, Bridge, planning_tokens, step_trial

MODES = ('baseline','bridge','split','flip','transfer','resonator','bridge_split','bridge_flip')

@dataclass(frozen=True)
class Resonator:
    source: int
    dest: int
    begins: int
    ends: int

@dataclass(frozen=True)
class Lab:
    trial: Trial
    mode: str = 'baseline'
    resonator: Resonator | None = None

    @classmethod
    def new(cls, mode='baseline', seed=0, state: State | None = None, waves=None):
        if mode not in MODES: raise ValueError('unknown mode')
        base = 'bridge' if mode in ('bridge','bridge_split','bridge_flip') else 'baseline'
        return cls(Trial(state or State(seed=seed), base, waves=waves), mode)


def options(g: Lab) -> list[tuple]:
    from experiments.rules_tournament import actions
    t = g.trial
    result = actions(t)
    extra = []
    if g.mode in ('split', 'bridge_split'):
        for tok in planning_tokens(t):
            if tok.size >= 2:
                for d in (-1,1):
                    if 0 <= tok.lane+d < 3: extra.append(('split',tok.id,d))
    elif g.mode in ('flip','bridge_flip'):
        for tok in planning_tokens(t):
            if t.state.progress[tok.lane] >= 1: extra.append(('flip',tok.id))
    elif g.mode == 'transfer':
        for src, p in enumerate(t.state.progress):
            if p >= 2:
                for dst in (src-1,src+1):
                    if 0 <= dst < 3: extra.append(('transfer',src,dst))
    elif g.mode == 'resonator' and g.resonator is None and t.state.round < TURNS-1:
        for src,p in enumerate(t.state.progress):
            if p:
                for dst in (src-1,src+1):
                    if 0 <= dst < 3: extra.append(('resonator',src,dst))
    return result + extra


def _prepare(t: Trial) -> Trial:
    # Materialize the current public incoming wave before modifying an arrival,
    # then suppress a second spawn for THIS round only; future waves unchanged.
    s=t.state
    wave = t.waves if t.waves is not None else tuple(arrivals(s.seed,r) for r in range(1,TURNS+1))
    toks = planning_tokens(t)
    nxt = replace(s,tokens=toks,next_id=s.next_id+len(wave[s.round]))
    changed = list(wave)
    changed[s.round] = ()
    return replace(t,state=nxt,waves=tuple(changed),front=0)


def _matches(prep: Trial, edits: tuple[tuple,...]) -> tuple[int,int,int]:
    """Independent preflight: amount of actual matched strength at breach."""
    toks={tok.id:tok for tok in prep.state.tokens}
    held=set()
    for a in edits:
        if a[0]=='shift':
            toks[a[1]]=replace(toks[a[1]],lane=toks[a[1]].lane+a[2])
        elif a[0]=='hold':
            x=toks[a[1]]
            toks[a[1]]=replace(x,size=min(3,x.size+1),held=1)
            held.add(a[1])
        elif a[0]=='damp':
            toks[a[1]]=replace(toks[a[1]],size=toks[a[1]].size-1)
    totals=[]
    for lane in range(3):
        a=sum(x.size for x in toks.values() if x.id not in held and x.row==0 and x.lane==lane and x.sign==1 and x.size>0)
        b=sum(x.size for x in toks.values() if x.id not in held and x.row==0 and x.lane==lane and x.sign==-1 and x.size>0)
        totals.append(min(a,b))
    return tuple(totals)


def step(g: Lab, planned=()) -> Lab:
    t=g.trial
    s=t.state
    planned=tuple(tuple(a) for a in planned)
    if s.over: raise ValueError('ended')
    if len(planned)>4: raise ValueError('four edits max')
    allowed={'shift','hold','damp','pass'}
    if g.mode in ('bridge','bridge_split','bridge_flip'):allowed.add('bridge')
    if g.mode in ('split','bridge_split'):allowed.add('split')
    if g.mode in ('flip','bridge_flip'):allowed.add('flip')
    if g.mode=='transfer':allowed.add('transfer')
    if g.mode=='resonator':allowed.add('resonator')
    if any(not a or a[0] not in allowed for a in planned): raise ValueError('bad experimental action')
    # Default/Bridge parity uses the existing independent Phase 3 reducer.
    if g.mode in ('baseline','bridge'):
        return replace(g,trial=step_trial(t,planned))
    prep=_prepare(t)
    touched=set()
    special=[]
    normal=[]
    tokens={tok.id:tok for tok in prep.state.tokens}
    points=list(s.progress)
    new_id=prep.state.next_id
    reactor=g.resonator
    for a in planned:
        kind=a[0]
        if kind in ('shift','hold','damp','split','flip'):
            if len(a)<2 or type(a[1]) is not int or a[1] not in tokens or a[1] in touched:
                raise ValueError('bad or repeated token edit')
            touched.add(a[1])
            if kind in ('shift','hold','damp'):
                normal.append(a)
            elif kind=='split':
                if len(a)!=3 or type(a[2]) is not int or a[2] not in (-1,1):raise ValueError('bad split')
                x=tokens[a[1]]
                if x.size<2 or not 0<=x.lane+a[2]<3:raise ValueError('cannot split')
                tokens[x.id]=replace(x,size=x.size-1)
                tokens[new_id]=Token(new_id,x.lane+a[2],x.row,x.sign,1,1)
                new_id+=1
            elif kind=='flip':
                if len(a)!=2:raise ValueError('bad flip')
                x=tokens[a[1]]
                if points[x.lane]<1:raise ValueError('flip needs lane power')
                points[x.lane]-=1
                tokens[x.id]=replace(x,sign=-x.sign)
        elif kind=='pass':
            if len(a)!=1: raise ValueError('bad pass')
        else:
            special.append(a)
            if len(special)>1:raise ValueError('at most one infrastructure action per round')
            if kind=='bridge': normal.append(a)
            elif kind=='transfer':
                if len(a)!=3 or type(a[1]) is not int or type(a[2]) is not int:
                    raise ValueError('invalid transfer')
                _,src,dst=a
                if not 0<=src<3 or not 0<=dst<3 or abs(src-dst)!=1 or points[src]<2:
                    raise ValueError('transfer requires 2 source power and adjacent dest')
                points[src]-=2
                points[dst]=min(3,points[dst]+1)
            elif kind=='resonator':
                if len(a)!=3 or g.resonator is not None or s.round+1>=TURNS:
                    raise ValueError('bad resonator')
                _,src,dst=a
                if type(src) is not int or type(dst) is not int or not 0<=src<3 or not 0<=dst<3 or abs(src-dst)!=1 or points[src]<1:
                    raise ValueError('resonator needs one source power and adjacent destination')
                points[src]-=1
                reactor=Resonator(src,dst,s.round+2,s.round+3)
    # Runtime TypeError from bad normal edits is okay, as it rejects invalid plans.
    prep = replace(prep,state=replace(prep.state,progress=tuple(points),tokens=tuple(sorted(tokens.values())),next_id=new_id))
    matched=_matches(prep,tuple(a for a in normal if a[0]!='bridge'))
    out=step_trial(prep,normal)
    if reactor is not None and reactor.begins<=out.state.round<=reactor.ends and matched[reactor.source]>=2:
        power=list(out.state.progress)
        power[reactor.dest]=min(3,power[reactor.dest]+2)
        state=replace(out.state,progress=tuple(power))
        if state.round==TURNS and state.hp>0:
            state=replace(state,over='win' if min(power)>=2 and sum(power)>=8 else 'loss: target')
        out=replace(out,state=state)
    if reactor and out.state.round>=reactor.ends:reactor=None
    if out.state.over:reactor=None
    # Prep materializes this round's arrivals into the state, then restores the
    # ORIGINAL future wave schedule for next step (important for replay).
    out=replace(out,waves=t.waves)
    return Lab(out,g.mode,reactor)
