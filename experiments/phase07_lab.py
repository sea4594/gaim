"""Pass 07: systemic mechanics research; shipping engine is never modified.

Modes compete against Forecast Market: rotating infrastructure demand, a publicly
chosen service lane, conditional collateral wagers, and a mechanical lane tide.
All state transitions are immutable. Synthetic tests are not human playtests.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from experiments.phase06_lab import Experiment, step as market_step
from reference.charge_loom_v01 import State, Token

MODES=('market','demand','flex_demand','pledge','tide','demand_pledge','milestones','council')

@dataclass(frozen=True)
class Audit:
    experiment: Experiment
    mode: str
    serviced: int=0
    blackouts: int=0
    wagers: int=0
    wagers_won: int=0
    wager_spent: int=0
    chosen_demand: tuple[int,...]=()

    @classmethod
    def new(cls, mode='market', seed=0, state=None, waves=None):
        if mode not in MODES:raise ValueError('unknown pass07 mode')
        return cls(Experiment.new('market' if state is None or state.round==0 else 'open',seed=seed,state=state,waves=waves),mode)

    @property
    def state(self):return self.experiment.state


def demand_options(g:Audit):
    """One consumption after each of rounds 3-9. Forecast is public."""
    r=g.state.round+1
    if g.mode not in ('demand','flex_demand','demand_pledge','milestones','council'):
        return ()
    if r < 3 or (g.mode in ('milestones','council') and r not in (3,6,9)):return ()
    primary=((r-3)//3)%3 if g.mode in ('milestones','council') else (r-3)%3
    return (primary,(primary+1)%3) if g.mode in ('flex_demand','council') else (primary,)


def _change_state(exp:Experiment,state:State)->Experiment:
    core=exp.game.core
    game=replace(exp.game,core=replace(core,trial=replace(core.trial,state=state)))
    return replace(exp,game=game)


def step(g:Audit, actions=(), draft=None, pledge=None, demand=None):
    """Resolve public pledge cost, normal storm/edit resolution, demand, and terminal.

    pledge = (condition, source_lane) where condition is 'sync', 'surge', or 'safe'.
    Deposit one power in source before any edits; on success add two to source.
    It is NOT a free bonus: it can fail, sacrifices stored victory power, and
    competes with Bridge/Flip for the same power. At most 1 on rounds 1,3,5,7.
    Conditions are evaluated after normal actions, before demand effects.
    'sync': matching in >=2 lanes this round; 'surge': strength >=2 matched in
    source lane this round; 'safe': at least one collision & 0 hull loss.
    All conditions are public and deterministic; future storms are not revealed.
    """
    if g.state.over:raise ValueError('game ended')
    actions=tuple(tuple(a) for a in actions)
    if pledge is not None:
        if 'pledge' not in g.mode or g.state.round not in (0,2,4,6):
            raise ValueError('pledge not available this round')
        if not isinstance(pledge,tuple) or len(pledge)!=2:
            raise ValueError('pledge must be (condition,source_lane)')
        condition,source=pledge
        if condition not in ('sync','surge','safe') or type(source) is not int or source not in range(3):
            raise ValueError('bad pledge')
        if g.state.progress[source]<1:raise ValueError('insufficient power deposit')
        progress=list(g.state.progress);progress[source]-=1
        exp=_change_state(g.experiment,replace(g.state,progress=tuple(progress)))
    else:
        exp=g.experiment
    start_hp=g.state.hp
    before_sync=exp.game.synchronized
    before_large=exp.game.large
    out=market_step(exp,actions,draft=draft)
    result=out.state
    new_progress=list(result.progress)
    hp=result.hp
    coolant=result.coolant
    complete=False
    if pledge is not None:
        cond,source=pledge
        sync=out.game.synchronized>before_sync
        surge=bool((out.game.large & (1<<source)) and not (before_large & (1<<source)))
        # 'surge' uses ever-achieved lane tracking: cannot farm same lane again
        safe=hp>=start_hp and (sync or out.game.large!=before_large or sum(result.progress)>sum(exp.state.progress))
        complete={'sync':sync,'surge':surge,'safe':safe}[cond]
        if complete:new_progress[source]=min(3,new_progress[source]+2)
    r=g.state.round+1
    serviced=g.serviced;blackouts=g.blackouts;chosen=g.chosen_demand
    if g.mode in ('demand','flex_demand','demand_pledge','milestones','council') and r>=3 and (g.mode not in ('milestones','council') or r in (3,6,9)):
        opts=((r-3)//3)%3,
        if g.mode in ('demand','flex_demand','demand_pledge'):opts=((r-3)%3,)
        if g.mode=='flex_demand': opts=((r-3)%3,(r-2)%3)
        if g.mode=='council': opts=(((r-3)//3)%3,(((r-3)//3)+1)%3)
        if demand is None:demand=opts[0]
        if type(demand) is not int or demand not in opts:raise ValueError('illegal demand lane')
        chosen=chosen+(demand,)
        if new_progress[demand]>0:
            new_progress[demand]-=1;serviced+=1
        else:
            hp-=2 if g.mode in ('milestones','council') else 1;blackouts+=1
    elif demand is not None:
        raise ValueError('demand selection not allowed now')
    # Final victory target differs intentionally under upkeep: it is more about
    # sustained throughput than hoarding 8 of the maximum 9 possible points.
    if hp<=0:over='loss: breach'
    elif r==9:
        if g.mode in ('demand','flex_demand','demand_pledge'):
            success=min(new_progress)>=1 and sum(new_progress)>=5 and serviced>=4
        elif g.mode in ('milestones','council'):
            success=min(new_progress)>=1 and sum(new_progress)>=5 and serviced>=2
        else:success=min(new_progress)>=2 and sum(new_progress)>=8
        over='win' if success else 'loss: target'
    else:over=''
    result=replace(result,progress=tuple(new_progress),hp=hp,coolant=coolant,over=over)
    out=_change_state(out,result)
    if g.mode=='tide' and not result.over and r in (2,4,6,8):
        # Forecast lateral drift: charges in SOON band drift toward CENTER
        # at the end of selected even rounds; no wraparound.
        # Deterministic automatic environment with no extra player action.
        shifted=tuple(replace(t,lane=(1 if t.lane in (0,2) else t.lane)) if t.row==1 else t for t in out.state.tokens)
        out=_change_state(out,replace(out.state,tokens=shifted))
    return Audit(out,g.mode,serviced,blackouts,g.wagers+int(pledge is not None),
                 g.wagers_won+int(complete),g.wager_spent+int(pledge is not None),chosen)
