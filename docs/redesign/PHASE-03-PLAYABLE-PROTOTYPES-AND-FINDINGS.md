# GAIM redesign — Phase 3: playable prototype tournament

**Decision:** Both candidate designs have complete, independent, deterministic eight-round Python reference reducers and a terminal interface. **Do not promote either yet.** Phase 4 should compare them against Forecast Market v0.5 using human play and better planning agents. All values below are algorithmic measurements, not human measures of enjoyment or strategic quality.

## What was actually built

`experiments/redesign_phase3/common.py` implements shared immutable-input charge accounting. `engine.py` implements the full Storm Engine draft including upgrades, pending activation, coolant, optional free Switchyard shifts, offline windows, two paid edits, collision power and deadline leakage. `operations.py` implements the full Storm Operations draft including player-count waves, seeded personal 9-card decks, hands/discards/recycling, per-seat orders, rotating initiative, fizzles, all six mission trackers and round-eight resolution. The engines are **not** production rules, nor connected to the multiplayer server.

`cli.py` permits manual JSON decisions or deterministic automated policies with no frontend dependency. `survey.py` generates full 8-round explicit scenarios, runs matched-seed policies and records outcomes. `make_examples.py` produces complete human-inspectable round logs in `phase03-full-game-witnesses.json`. The new unit/integration tests check both Phase 2 fixtures, edge cases, atomic validation, whole-game results, and player-count scaling.

**Run from the repo root:**

```bash
python3 -m experiments.redesign_phase3.cli --game engine --seed 5001
python3 -m experiments.redesign_phase3.cli --game operations --players 2 --seed 7000
python3 -m experiments.redesign_phase3.cli --game engine --seed 5001 --auto
python3 -m experiments.redesign_phase3.cli --game operations --players 4 --seed 7000 --auto
python3 -m experiments.redesign_phase3.survey --seeds 40
python3 -m unittest tests.test_redesign_phase3_engines -v
bash scripts/release_gate.sh
```

In manual mode, an empty line passes. Engine plans are JSON objects such as `{"build":0,"edits":[{"kind":"SHIFT","token":"r1t0","delta":1}]}`. Operations plans are arrays by player, such as `[[{"kind":"LEFT","token":"r1t0"}],[]]`. The terminal shows the current board, arriving and next public storms, engine resources or individual hands, and the effects of each round. Hands are shown in the local developer CLI; an eventual multiplayer client would show each player only their own hand.

## Demonstrated complete-session outcomes

### Storm Engine: persistent strategy has measurable consequences

The **published Phase 2 exact eight-round fixture** now replays as `WIN`, `hull=6`, `power=8`, `levels=[2,2,0]`; the identical storm sequence with no upgrades ends `LOSS_SYSTEMS`. Dynamo level 1 awards no bonus for a Center-only collision, and upgrades have a full-round activation delay.

A **more contested generated scenario (seed 5002)** gives three different outcomes under exactly the same eight storm waves and identical local reactive edits:

| Upgrade priorities | Final state | Result |
|---|---|---|
| Dynamo → Aegis | level 2 Dynamo, level 2 Aegis; 2 hull | **Win** |
| Aegis → Switchyard | level 2 Aegis, level 2 Switchyard; 4 hull | **Win** |
| Dynamo → Switchyard | level 2 Dynamo, level 2 Switchyard; hull 0 | **Loss** |

This is **evidence of consequential strategic investment**. It is not evidence of equally difficult or equally appealing choices: the reactive policy evaluates only current breaches and never selects the Switchyard's *free shift*, so it systematically underestimates that upgrade. This limitation makes the policy-comparison result *biased*, not a reliable balance ranking. The winning routes here still need validation with the system ability actually used.

### Storm Operations: owned cards matter, but participation is unequal

A published **two-player eight-round fixture** now replays exactly: one player's DAMP on `r2t2` during round 3 results in a win on hull 1 with Deep Capture and Precision Route; skipping the intervention causes hull loss in round 7. DAMP is actually consumed from a personal hand and replenished only after resolution.

For player counts 1–4, generated scenarios with `players+1` charges in each of rounds 1–6 provide at least one complete winning run using legal held cards and a complete losing all-pass run **on the same waves**. Seeded witnesses from the 40-seed dataset:

| Players | Seed | Cards used by each seat in winning run | Winner hull | All-pass result |
|---|---:|---|---:|---|
| 1 | 7000 | [3] | 4 | Loss (hull) |
| 2 | 7000 | [6,2] | 6 | Loss (hull) |
| 3 | 7000 | [5,4,3] | 6 | Loss (hull) |
| 4 | 7000 | [6,5,3,0] | 4 | Loss (hull) |

This highlights a serious co-op flaw: the example four-player win included **zero contributions from one player**. It is a valid result and should not be sanitized. The personal-hand idea creates real ownership but does not ensure everyone has something useful to do.

The two-player **paired-shift tactical survival** scenario proves a specific dependency: a Left positive NEAR and a Right negative NEAR require two different player-held SHIFT cards to cancel in Center. From hull 2, both shifts survive; either one alone leaves two raw damage and loses. This is a controlled round-level state, not proof that a whole multiplayer session is satisfying or immune to quarterbacking.

## Reproducible 40-seed policy survey

The survey uses the same 40 explicit seeds per competing *policy within its own game*. Engine and Operations use different victory conditions, different wave composition, different starting hull and different action budgets; **cross-game win rates must not be ranked as game quality**.

### Engine: 40 matching storm sequences per upgrade policy

| Upgrade strategy | Wins / 40 | Mean final hull | Total upgrades built | Total paid edits |
|---|---:|---:|---:|---:|
| Dynamo → Aegis | 30 | 4.28 | 159 | 351 |
| Aegis → Switchyard | 34 | 5.25 | 160 | 354 |
| Dynamo → Switchyard | 19 | 1.80 | 160 | 350 |
| No upgrades | 0 | 1.80 | 0 | 350 |

**25/40 identical storms permit wins under at least two different predefined upgrade orders.** This is a first proof of multiple plausible routes, not proof that neither route dominates under optimal play. The heuristic systematically ignores free Switchyard SHIFT actions, biases the ranking against Switchyard, and buys fixed upgrades regardless of upcoming forecasts.

### Operations: 40 matching storms per player count and action policy

| Players | Pass-only wins / 40 | Reactive owned-card wins / 40 | Mean cards spent per seat across a game |
|---|---:|---:|---:|
| 1 | 3 | 11 | 2.75 |
| 2 | 0 | 17 | 3.30 |
| 3 | 0 | 27 | 3.29 |
| 4 | 0 | 37 | 3.24 |

The reactive policy makes **sequential seat-specific card choices**, without future hand valuation and usually without discovering two-action rescues. It is weak. It also indicates a likely balancing issue: four-player wins are much more frequent than solo wins with the current hull/wave scaling. More players have more intervention cards and two-on-one combinations. **Do not infer that the multiplayer design is proven.**

## Exact correctness and rules disputes resolved in code

- Charge IDs are stable per wave, and collisions total strengths simultaneously per lane; `+3/−1` yields 1 matched strength and 2 damage.
- Held tokens do not move during the held round, remain marked held for life, and cannot be held twice.
- Engine paid edits use at most two **distinct** tokens and consume coolant for DAMP; no invalid plan mutates the original state.
- Engine upgrades deduct power before collision and activate the following round; an offline system retains levels but disables its benefits and counts as inoperable for the round-eight victory check.
- Engine's Switchyard free SHIFT is a distinct slot (after paid edits); its target must survive earlier edits and satisfy the operating level's band limit.
- Operations validates an order's card ownership and original-board legality before lock; two teammates can target the same token, and later orders may fizzle without refunds.
- Operations rotates initiative, resolves cards in seat order, and refills each player's hand after resolution without drawing a just-played card in the same round.
- All six Operations missions are tracked from breach events; a late unresolved token does not score a mission and does leak strength at the deadline.
- Both games end immediately on hull <=0 and impose deadline leakage after round eight.

The candidate rulebooks do not yet specify a production-ready network protocol or live join/leave handling. That's intentionally out of scope: prototypes are independent of server transport.

## Major design failures and proposed Phase 4 pressure tests

**Engine: dominant upgrade order risk.** Aegis might be almost mandatory in hard scenarios. Test optimal or at least beam-search policies that actively exploit Switchyard, and generate scenarios in which investment timing is tight. Either demonstrate worthwhile distinct development paths or remove the lesser upgrades. Consider how four players obtain agency: sharing one BUILD decision and two editable slots may be even worse for co-op than the old four-slot puzzle.

**Engine: too-easy objective in safe storms.** In fixture-like waves, planning a build order is obvious. Need forecast shocks, persistent consequences beyond a static level, more resource tension, and credible mid-game pivots. Do not add extra systems until two choices are demonstrably hard.

**Operations: heavy quarterbacking remains possible.** Full hand disclosure lets one player plan all cards. Verify independent choice and communication with actual people; introduce new structure only if needed.

**Operations: uneven participation and generous 4p difficulty.** Hand scarcity can cause inactive seats, and 4p's extra interventions overpower `players+1` charge scaling. Rebalance with meaningful responsibilities and scenario-level difficulty—not mere bigger numbers. Test starting-card mulligans and mission designs that require complementary orders.

**Operations: mission progress may be automatic.** Naturally matched waves can complete Deep Capture/Precision Route without decisions, while Last-Moment Save may be hard to understand. Require reached-game states where the selected mission *reverses* a plan; otherwise remove decorative missions.

**Neither candidate demonstrates fun yet.** Simulated victories, pure functions, and a few tactical counterexamples are useful necessary evidence, not human validation. Phase 4 must run full human sessions or explicitly mark that gate unresolved.

## Selection status

**Advance both prototypes and the Forecast Market control into Phase 4.** Engine has an initial persistent strategy signal; Operations has an initial personal-action signal. Both have critical unresolved flaws. The objective is not to pick based on seed win rates, but to find the design that gives a more satisfying combination of strategic consequences and human teamwork for similar rules cost.
