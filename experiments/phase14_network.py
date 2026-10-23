"""Pass 14: replace the temporary Bridge economy with actual energy transport.

CONTROL  - unchanged Forecast Market research game.
CONDUIT  - spend one source power and an edit to establish a persistent adjacent
           directed wire. From the FOLLOWING round, the wire moves one existing
           power before collisions if source >=2 and destination <3. Only one
           wire may exist at once; rebuilding replaces it.
SWITCH   - the same persistent, one-link network, but configuration costs an
           edit and no energy. This is a *deliberately easier* complexity control.
SERVICE  - conduit rules plus an alternative economy: each lane may be served
           once for two power and an edit, BEFORE this round's collisions.
           To win, serve two distinct lanes AND finish with >=4 stored power.
           Existing min-2-per-lane goal is completely replaced.

In all variants no Bridge edit is legal. Power transfers conserve energy. The
routing system is serial, not a chain of bonus-production triggers. New routes
cannot move power the same round they are installed. The existing forecast,
storm, damage, token, and four-edit rules are preserved unchanged.

Research-only, never imported by the production server.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from experiments.phase06_lab import Experiment, step as forecast_step
from reference.charge_loom_v01 import TURNS

MODES = ('control', 'conduit', 'switch', 'service')
EDGES = ((0, 1), (1, 0), (1, 2), (2, 1))


def _set_state(exp: Experiment, **updates) -> Experiment:
    core = exp.game.core
    trial = core.trial
    return replace(exp, game=replace(exp.game, core=replace(core, trial=replace(trial, state=replace(exp.state, **updates)))))


@dataclass(frozen=True)
class Network:
    exp: Experiment
    mode: str = 'control'
    link: tuple[int, int] | None = None
    served: tuple[bool, bool, bool] = (False, False, False)
    transferred: int = 0
    invested: int = 0
    deliveries: int = 0
    configurations: int = 0

    @classmethod
    def new(cls, mode='control', seed=0, state=None, waves=None, link=None, served=(False, False, False)):
        if mode not in MODES:
            raise ValueError('unknown network mode')
        if link is not None and link not in EDGES:
            raise ValueError('invalid initial link')
        served = tuple(served)
        if len(served) != 3 or any(type(x) is not bool for x in served):
            raise ValueError('bad service state')
        if mode != 'service' and any(served):
            raise ValueError('service not allowed')
        exp = Experiment.new('market' if state is None or state.round == 0 else 'open',
                             seed=seed, state=state, waves=waves)
        return cls(exp, mode, link, served)

    @property
    def state(self):
        return self.exp.state


def options(g: Network) -> tuple[tuple, ...]:
    if g.state.over or g.mode == 'control':
        return ()
    out=[]
    for src, dst in EDGES:
        if (src, dst) != g.link and (g.mode == 'switch' or g.state.progress[src] >= 1):
            out.append(('wire', src, dst))
    if g.mode == 'service':
        for lane in range(3):
            if not g.served[lane] and g.state.progress[lane] >= 2:
                out.append(('deliver', lane))
    return tuple(out)


def step(g: Network, edits=(), *, draft=None) -> Network:
    if g.state.over:
        raise ValueError('game is finished')
    edits = tuple(tuple(a) for a in edits)
    if len(edits) > 4:
        raise ValueError('team has four edits')
    if any(not a or not isinstance(a[0], str) for a in edits):
        raise ValueError('invalid edit')
    if any(a[0] == 'bridge' for a in edits) and g.mode != 'control':
        raise ValueError('bridge has been replaced by the network')
    extra = [a for a in edits if a[0] in ('wire', 'deliver')]
    if len(extra) > 1:
        raise ValueError('maximum one infrastructure decision per round')
    normal = tuple(a for a in edits if a[0] not in ('wire', 'deliver'))
    if extra and extra[0] not in options(g):
        raise ValueError('illegal infrastructure action')

    power=list(g.state.progress)
    served=list(g.served)
    link=g.link
    invested=g.invested
    deliveries=g.deliveries
    configurations=g.configurations
    # Structural purchases are paid from previously stored power, never energy
    # generated during the round. The prior (not newly purchased) wire resolves.
    if extra:
        a=extra[0]
        if a[0] == 'wire':
            _, src, dest = a
            if g.mode in ('conduit', 'service'):
                power[src]-=1
                invested+=1
            link=(src,dest)
            configurations+=1
        else:
            lane=a[1]
            power[lane]-=2
            served[lane]=True
            deliveries+=1

    transferred=g.transferred
    if g.link is not None:
        src,dst=g.link
        if power[src] >= 2 and power[dst] < 3:
            power[src]-=1
            power[dst]+=1
            transferred+=1
    exp=_set_state(g.exp, progress=tuple(power))
    after=forecast_step(exp, normal, draft=draft)
    # The reference reducer evaluates the ORIGINAL target at the deadline;
    # alternative SERVICE victory is evaluated after exactly the same damage.
    if g.mode == 'service' and after.state.round == TURNS and after.state.hp > 0:
        complete=sum(served)>=2 and sum(after.state.progress)>=4
        after=_set_state(after, over='win' if complete else 'loss: target')
    return Network(after,g.mode,link,tuple(served),transferred,invested,deliveries,configurations)
