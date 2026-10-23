# GAIM — Mechanics Pass 07: Systemic economy, missions, and cooperative decisions

**Status:** Research only. No production reducer, multiplayer-room contract, or golden trace changed.

**Decision:** **Retain Forecast Market (v0.5) as the best-supported research ruleset.** Advance **Council Checkpoints** as the leading challenger, *not* a proven improvement. Do not add recurring demand, conditional wagers, lane tide, or mission swapping to the production rules.

## Question and criteria

Earlier passes searched for tactical verbs: Shift, Hold, Damp, Bridge, Flip, Accelerate. Pass 6 added a public two-offer Storm Market with one-card preview. But energy is still mainly a win counter; four-player participation remains unproven; a narrow victory target limits variation. This pass borrowed *upkeep*, *shared public objectives*, *wager/contract fulfillment*, *automatic map events*, and *modular mission scoring* from strategy/board-game design, then implemented them as deterministic, isolated mechanical experiments.

The decision criteria were (1) distinct meaningful choices, especially when the immediate best-looking move is wrong; (2) comprehensible rules; (3) genuine strategy rather than a free bonus or punitive overhead; (4) compatible with nine-round solo and 1–4 co-op sessions; (5) reproducible tests; (6) robustness versus the unchanged control. **Win percentage was never used as a proxy for fun.** More scoring choices do not prove more viable strategic plans.

## A. Exact contenders and proposed rules

All variants preserve the storm market, all six existing tactical verbs, the fixed 3-lane/3-band board, the nine-round deadline, and the four shared edits. Additional effects occur **after** ordinary charge resolution unless noted.

| Variant | Additional rules | Evaluation |
|---|---|---|
| **Forecast Market** | No changes. Match charges, use stored power on Bridge/Flip, draft incoming storms. | **Retain as control and winner** |
| **Rotating Demand** | At the end of each round 3–9, the settlement consumes one energy from a rotating lane (L→C→R). Missing demand deals 1 hull. New win goal: service at least four demands and finish with ≥1 per lane and ≥5 overall. | Too punitive with current storm population; not selected |
| **Flexible Demand** | Same as Demand but each payment may come from the rotating lane **or its clockwise neighbor**. | Less blackout damage, but the simple planner depletes too much stored energy; no demonstrated gain |
| **Conditional Pledge** | At the beginning of rounds 1,3,5,7, optionally escrow one energy in any lane. Choose one of: simultaneous matching in ≥2 lanes, a newly achieved size-2+ match in the escrow lane, or a safe round with actual production. If fulfilled, return two energy to the escrow lane (capacitor cap still 3); otherwise forfeit the deposit. No edit cost. | Too easy to collect when a known matching arrangement already exists; do not adopt |
| **Lane Tide** | At end of even rounds 2,4,6,8, charges in SOON band drift from L/R into Center automatically. | Rule exception and central congestion; no demonstrated distinctive strategic gain |
| **Demand + Pledge** | Combine first and fourth systems. | Adds rules without restoring strong play under tested policy |
| **Milestones** | At ends of rounds **3,6,9 only**, draw one energy from L,C,R respectively. Missing energy deals **2 hull**. New win goal: serve at least **two** of three checkpoints, survive, and finish with ≥1 per lane and ≥5 overall. | Better than continual drain, but the single-source rule has little choice at payment time |
| **Council Checkpoints** | Same three public checkpoints; at each, the team may spend one energy from either the requested lane **or its clockwise neighbor**. Checkpoint 1: L/C; checkpoint 2: C/R; checkpoint 3: R/L. Failure in both choices costs 2 hull. Same milestone win goal. | **Strongest challenger**: meaningful resource allocation with no new tactical verb |

*Paying energy* affects future tactical options: Bridge and Flip spend from lane capacitors, so a safe-looking checkpoint payment may remove the power needed for a later combo. The rules have an explicitly public schedule; no one must guess which lane is billed. For each checkpoint, there is one group decision, not a separately granted action per human. One player chooses in solo; all players discuss the same decision in multiplayer. **This does not cure quarterbacking.**

### Concrete, executable Council counterexample

At the final checkpoint, the team has already served two demands, has 7 hull, no incoming threats, and holds L=3, C=2, R=1 power. The third checkpoint allows either R or L to pay one. Paying R leaves **3–2–0**, causing loss because one lane has no power. Paying L leaves **2–2–1**, satisfying the new ≥1-each and ≥5-total objective, and wins. Both are legal. Tests also verify a case where choosing the empty lane causes a fatal 2-hull blackout. This demonstrates consequential choice, **not** whether human players find it difficult to identify the better payment.

### Important counterpoint: the Council option may be obvious

The currently implemented policy chooses a checkpoint lane using immediate outcome scoring. We have not identified a broad set of naturally visited states in which an immediately inferior payment turns out better two or more rounds later. Without that evidence, Council may be a cleaner economic rule but *not* a deeper game. This is why it is a challenger and not the selected ruleset.

## B. Paired full-game exploratory benchmarks

All test games below use the **same storm seeds for each mode within each set**. They share a published one-step, open-board action heuristic. Critically, that heuristic was built for Forecast Market; it is **not demand-aware in advance**, and the Council selector looks only at the current checkpoint. In the wager variant it opportunistically buys only pledges with immediate visible expected returns. These policy asymmetries prevent using win rates for ranking ultimate game quality.

| Mode | Development 20 seeds (14000–14019), wins | Holdout 20 seeds (19500–19519), wins |
|---|---:|---:|
| Forecast Market | **15** | **12** |
| Rotating Demand | 4 | 2 |
| Flexible Demand | 0 | 1 |
| Conditional Pledge | 16 | 15 |
| Lane Tide | 11 | 7 |
| Demand + Pledge | 5 | not separately reported |
| Milestones | 10 | 7 |
| **Council Checkpoints** | **11** | **8** |

Demand variants change the victory condition (to reflect power consumption), so these **are not apples-to-apples difficulty scores**. In development's 20 sessions, Rotating Demand triggered 32 blackouts; Flexible Demand triggered 15; Milestones 12; Council just 5. Council's optional payment lane helps survival but not necessarily the power required for victory.

A small six-seed two-step planning check on each of two distinct ranges had Forecast Market at 4/6 and 5/6 wins; Council at 2/6 and 3/6. This is too small for strong inference and the planner still does not optimize future payments. It does not prove Council is worse with appropriate human planning, only that improvement has not been demonstrated.

## C. Structural counterfactuals

1. **Council can change a final outcome:** With no edits and uniform random capacitor/hull states in 600 synthetic final checkpoints (two earlier bills already served), choosing R or L altered the eventual victory outcome **56 times**, altered final capacitor distribution **564 times**, and altered hull **233 times**. Another **115** states won under either choice and **429** lost under either choice. This establishes mechanical stakes but not decision difficulty. The synthetic states are deliberately not sampled from real policy trajectories.
2. **Pledges risk becoming safe bonuses:** In 240 one-round, no-edit synthetic states, we enumerated **1,596** legal escrow options. Relative to no pledge, **21** yielded more final power, **1,401** less, **174** tied. An action-aware chooser selected very few; in 20 full seeded development games it placed **16 pledges and all 16 fulfilled**. This is too easy to time after publicly visible matching and therefore fails the goal of meaningful uncertainty. The very uneven option distribution also adds search clutter.
3. **Mission cards are not yet mechanically distinctive:** Existing Shield/Choreography/Voltage victory rules were compared in **300** synthetic final states enumerating pass or one legal edit. **30** states offered winning actions under multiple missions; **zero** demonstrated disjoint winning-action sets for two such missions. That does not prove the missions have the same optimal full-game strategies, but neither does it support advertising them as delivering replayability yet. In a separate 400-state no-edit probe, outcome labels varied in only **30** states. More varied endings are not the same as varied plans.
4. **Lane Tide is predictable but centralizes play:** It moved charges toward Center on even rounds, increasing the premium on that location. The central-lane bias was previously one of Charge Loom's diagnosed strategic weaknesses. Its effect on the game is not sufficiently compelling to justify another timing exception.
5. **The unchanged Storm Market remains mechanistically cleanest:** It changes the *order in which problems arise* using one drafting choice, with no per-token or post-resolution exception. The experimental additions did not demonstrate a clear, repeatable new strategic advantage at proportional rules complexity.

## D. What this does and does not establish about cooperative play

The initial hypothesis was that public choice of expenditure source could add a real joint decision without hiding arbitrary cards or restricting teammates' access to useful moves. Council does exactly that: the players must choose where to pay, affecting later investment and tactics, while solo still chooses normally. That is **an additional group decision**, not **genuine independent player agency**. Four people could still follow one optimizer, and no live human test was conducted. Do not claim that this iteration solved quarterbacking or four-player inactivity.

The rejected operator action-menu design in Pass 6 offered a valuable control: preventing teammates from making needed actions just to make their menus unique reduced viable solutions without proving better cooperation. We should resist replacing that with any cosmetically similar restriction.

## E. Selection and risk register

### Selected: keep **Forecast Market v0.5 research** unchanged

This is an explicit decision **against automatic feature accumulation**. It remains the easiest well-tested ruleset to explain: three lanes, charge polarity/strength, six tactical verbs with a shared four-edit budget, stored power funding delayed Bridges and Flips, and a two-offer one-preview forecast that reorders (but never removes) incoming waves. No variant in this pass showed sufficiently stronger strategic diversity for its added rules.

### Retain as a focused next challenger: Council Checkpoints

It is the first tested proposal here that makes electricity actually **consumed on a public schedule**, without another tactical action. It also offers mission-like strategic variation (which lane must retain capacity) while preserving the same phone-sized board. The next evidence gate is not a higher win rate. It is: a demand-aware two-to-four-turn planner must discover reproducible states where the immediately safer consumption choice loses later, while a more subtle allocation wins. It must also be able to achieve reasonable solvability with *only the public forecast*.

### Not selected

- Seven-round drain: strains the current generator too severely and punishes without new agency.
- Conditional free wagers: selectively easy to collect and risks bloating the game with obvious opportunities.
- Lane Tide: added exception and central-lane gravitational bias.
- Current mission variants: insufficient evidence that they change good action choices, as opposed to changing success labels.
- Council + Pledge: additional complexity without evidence of meaningful synergy.

## F. Next tests worth doing

1. Train/evaluate a **future-demand-aware limited-information planner**, independently of the previously tuned Forecast Market policy, to compare Council and no-upkeep on information actually public to players.
2. Search for **non-myopic Council counterexamples** (two or more storm rounds, same visible three-card forecast). Reject Council if paying the fullest capacitor is almost always correct.
3. Design **one genuinely different mission structure** (e.g. protecting two publicly chosen facilities with independent failure conditions), then measure strategy divergence, not merely final win labels.
4. Test human 2–4 player sessions for simultaneous participation, unsolicited suggestions, and individual satisfaction. Four-player agency remains the most important unanswered product question.
5. Revisit rule pruning. The existing core is already six verbs plus drafting; do not import upkeep unless it earns its cognitive cost.

## Reproduction

From repository root after hotfix installation:

```sh
python3 -m unittest tests.test_phase07_lab -v
python3 -m experiments.phase07_survey --games 20 --lookahead 1
bash scripts/release_gate.sh
```

Full numerical inputs, representative counterexamples and replayable deterministic outcomes are in `docs/design/pass07-results.json`; source is `experiments/phase07_lab.py` and `experiments/phase07_survey.py`.

**Caveat:** This is a research prototype. Only the original Charge Loom v0.1 production game is served by the existing multiplayer implementation. No web UI, online server rules or deployed game have been changed by this pass.
