"""Pass 05 independent board-game structure tournament: draft / accelerate / heat / mission.

Opt-in research only. Never imported from src, rooms, or production server.
All state is immutable and testable with explicit wave decks.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from reference.charge_loom_v01 import State, Token, wavebook, TURNS
from experiments.phase04_lab import Lab, step as core_step, options as core_options
from experiments.rules_tournament import Trial, planning_tokens

VARIANTS = ('control','draft','accelerate','draft_accelerate','heat','mission','draft_mission','draft_accelerate_mission','accelerate_no_damp','accelerate_no_hold','accelerate_no_flip')

@dataclass(frozen=True)
class Design:
    core: Lab
    variant: str
    deck: tuple                         # fixed source deck, always seven waves
    available: tuple[int,...] = ()       # offered wave indices, first=older
    cursor: int = 0                     # next deck index not yet offered
    heat: int = 0
    synchronized: int = 0               # number of rounds matching >=2 lanes
    large: int = 0                      # number of different lanes with >=2 matched, bitmask
    mission: str = 'standard'

    @property
    def state(self): return self.core.trial.state

    @classmethod
    def new(cls,variant='control',seed=0,state=None,waves=None,mission='standard'):
        if variant not in VARIANTS:raise ValueError('unknown variant')
        if mission not in ('standard','shield','choreography','voltage'):raise ValueError('unknown mission')
        schedule=tuple(waves) if waves is not None else wavebook(seed)+ ((),())
        if len(schedule)!=9:raise ValueError('nine waves required')
        deck=tuple(tuple(tuple(item) for item in wave) for wave in schedule[:7])
        # Supplied state near end is permitted for exact mechanical counterexamples.
        s=state or State(seed=seed)
        if 'draft' in variant and s.round!=0:raise ValueError('draft fixtures start at round zero')
        offered=(0,1) if 'draft' in variant else ()
        return cls(Lab.new('bridge_flip',seed=seed,state=s,waves=schedule),variant,deck,offered,2 if offered else 0,mission=mission)


def offers(game:Design):
    return tuple((ix,game.deck[ix]) for ix in game.available)


def options(game:Design):
    if game.state.over:return []
    out=list(core_options(game.core))
    if game.variant.endswith('_no_damp'):
        out=[a for a in out if a[0]!='damp']
    if game.variant.endswith('_no_hold'):
        out=[a for a in out if a[0]!='hold']
    if game.variant.endswith('_no_flip'):
        out=[a for a in out if a[0]!='flip']
    if 'accelerate' in game.variant:
        for t in planning_tokens(game.core.trial):
            if t.row>=1:out.append(('accelerate',t.id))
    if 'draft' in game.variant and len(game.available)>1 and game.state.round<7:
        out.extend([('draft',0),('draft',1)])
    return out


def _preflight_matches(game:Design,actions, trial:Trial):
    """Record matched breach amount independent of saturated capacitor scoring."""
    toks={t.id:t for t in planning_tokens(trial)}
    held=set()
    for a in actions:
        typ=a[0]
        if typ=='shift':
            t=toks[a[1]];toks[a[1]]=replace(t,lane=t.lane+a[2])
        elif typ=='hold':
            t=toks[a[1]];toks[a[1]]=replace(t,size=min(3,t.size+1),held=1);held.add(a[1])
        elif typ=='damp':
            t=toks[a[1]];toks[a[1]]=replace(t,size=t.size-1)
        elif typ=='flip':
            t=toks[a[1]];toks[a[1]]=replace(t,sign=-t.sign)
        elif typ=='accelerate':
            t=toks[a[1]];toks[a[1]]=replace(t,row=t.row-1)
    result=[]
    for lane in range(3):
        good=[t for t in toks.values() if t.lane==lane and t.id not in held and t.row==0 and t.size>0]
        result.append(min(sum(t.size for t in good if t.sign==1),sum(t.size for t in good if t.sign==-1)))
    return tuple(result)


def _mission_result(mission,state,synchronized,large):
    e=state.progress
    if mission=='standard':return min(e)>=2 and sum(e)>=8
    if mission=='shield':return min(e)>=2 and sum(e)>=7 and state.hp>=4
    if mission=='choreography':return min(e)>=2 and sum(e)>=7 and synchronized>=1
    if mission=='voltage':return min(e)>=1 and sum(e)>=7 and large.bit_count()>=2
    raise ValueError('bad mission')


def step(game:Design,planned=()):
    s=game.state
    if s.over:raise ValueError('game ended')
    planned=tuple(tuple(a) for a in planned)
    choices=[a for a in planned if a and a[0]=='draft']
    if len(choices)>1:raise ValueError('at most one draft decision per round')
    action_edits=tuple(a for a in planned if a and a[0]!='draft')
    if len(action_edits)>4:raise ValueError('four edits maximum')
    forbidden={'accelerate_no_damp':'damp','accelerate_no_hold':'hold','accelerate_no_flip':'flip'}.get(game.variant)
    if forbidden and any(a and a[0]==forbidden for a in action_edits):raise ValueError('action excluded by this rule variant')
    has_draft='draft' in game.variant and s.round<7
    selected=0
    if choices:
        if not has_draft or len(choices[0])!=2 or type(choices[0][1]) is not int or choices[0][1] not in range(len(game.available)):
            raise ValueError('illegal draft choice')
        selected=choices[0][1]
    elif not has_draft and choices:raise ValueError('draft not permitted')
    trial=game.core.trial
    base=trial.waves
    if has_draft:
        schedule=list(base)
        schedule[s.round]=game.deck[game.available[selected]]
        trial=replace(trial,waves=tuple(schedule))
    touched=set();accelerate=[];normal=[]
    for a in action_edits:
        if a and a[0]=='accelerate':
            if 'accelerate' not in game.variant or len(a)!=2 or type(a[1]) is not int:
                raise ValueError('illegal accelerate')
            accelerate.append(a)
        else: normal.append(a)
        if a and a[0] in ('hold','damp','shift','flip','accelerate'):
            if len(a)<2 or type(a[1]) is not int or a[1] in touched:raise ValueError('token edited twice or bad id')
            touched.add(a[1])
    all_tokens={t.id:t for t in planning_tokens(trial)}
    for a in accelerate:
        if a[1] not in all_tokens or all_tokens[a[1]].row<1:
            raise ValueError('accelerate only FAR or SOON tokens')
    match=_preflight_matches(game,action_edits,trial)
    if accelerate:
        # Materialize this round's visible arrivals once, then suppress duplicate spawning.
        wave=trial.waves[s.round]
        stored={t.id:t for t in planning_tokens(trial)}
        for a in accelerate:
            t=stored[a[1]];stored[a[1]]=replace(t,row=t.row-1)
        schedule=list(trial.waves)
        schedule[s.round]=()
        adjusted=replace(trial,state=replace(trial.state,tokens=tuple(sorted(stored.values())),next_id=s.next_id+len(wave)),waves=tuple(schedule),front=0)
        # normal core executes same bridge/flip rules without an additional spawn
        after=core_step(replace(game.core,trial=adjusted),normal)
    else:
        after=core_step(replace(game.core,trial=trial),normal)
    after=replace(after,trial=replace(after.trial,waves=base))
    heat=game.heat
    out=after.trial.state
    if game.variant=='heat':
        # Thermal overload: strong collisions create heat; at 2 heat the
        # reactor vents explosively (2 hull) and heat resets to zero.
        if any(x>=2 for x in match):heat+=1
        if heat>=2:
            out=replace(out,hp=out.hp-2)
            heat=0
    synchronized=game.synchronized+int(sum(x>0 for x in match)>=2)
    large=game.large
    for i,x in enumerate(match):
        if x>=2:large |= 1<<i
    if s.round+1==TURNS or out.hp<=0:
        over='loss: breach' if out.hp<=0 else ('win' if _mission_result(game.mission,out,synchronized,large) else 'loss: target')
        out=replace(out,over=over)
    after=replace(after,trial=replace(after.trial,state=out))
    available=game.available
    cursor=game.cursor
    if has_draft:
        available=tuple(w for ix,w in enumerate(available) if ix!=selected)
        if cursor<len(game.deck):
            available=available+(cursor,)
            cursor+=1
    return Design(after,game.variant,game.deck,available,cursor,heat,synchronized,large,game.mission)
