# GAIM redesign — Phase 4: Adversarial comparison and architecture selection

**Decision, October 26, 2026:** Select **Storm Engine as the provisional *strategic chassis*** for redesign Phases 5–7. **Do not promote its rules into production.** Preserve Storm Operations as the competing cooperative-interaction laboratory and Forecast Market v0.5 as the original control. No hybrid is accepted in this phase; combining the existing systems would compound rules without establishing that four players have distinct contributions.

**This is an architectural decision, not a finding that Storm Engine is a finished fun game.** Phase 5 is a mandatory gate: if we cannot create meaningful multiplayer agency, reopen selection and favor a leaner Operations-style structure or a new pivot. The requirements of human co-op enjoyment, balanced 1–4 player scaling and replayability are **not met**.

## Scope and reproducibility

I examined the Phase 2 rulebooks, Phase 3 source reducers (`engine.py`, `operations.py`, `common.py`), Phase 3 full-game witness tests, the Forecast Market v0.5 experimental reducer, and the Phase 1 charter. I retained both published prototypes without modifying their core rules. The only new executable research is an adversarial tournament and a changed-**policy-only** Operations rotating-proposal experiment.

The tournament runs paired 40-seed batches (development seeds `91000..91039`; separate holdout `93000..93039`) within each game's own scenario generator. An additional 40-seed post-hoc stress batch `95000..95039` was run while diagnosing the Switchyard evaluation. **The generators and victory criteria differ, so Engine and Operations win counts must never be directly compared to each other or Forecast Market as game-quality scores.** Human tests: **zero**.

Reproduce from the project root:

```bash
python3 -m experiments.redesign_phase4.tournament --n 40 --start 91000
python3 -m experiments.redesign_phase4.tournament --n 40 --start 93000
python3 -c 'from experiments.redesign_phase4.rotation import compare; print(compare(40,91000))'
python3 -c 'from experiments.redesign_phase4.rotation import compare; print(compare(40,93000))'
python3 -m unittest tests.test_redesign_phase4_selection -v
bash scripts/release_gate.sh
```

Data files: `phase04-comparison-development.json`, `phase04-comparison-holdout.json`, `phase04-rotation-development.json`, `phase04-rotation-holdout.json`. Every number below is from runnable Python with explicit seeds.

## 1. Storm Engine: long-term choices exist, but Aegis and the bot obscure them

The current Engine has 8 rounds, six hull, starting two power and two coolant, two paid charge edits per round, one optional 2-power build, and three two-level systems. An upgrade becomes active next round. Win with any two systems at level 2 and positive hull. This is a persistent **position** in the board-game sense: choices change later action value and risk tolerance.

Paired outcomes, 40 seeds in each batch; same reactive charge-edit policy, only the **preselected upgrade priority** changes:

| Build route | Development wins | Holdout wins | Total / 80 |
| --- | ---: | ---: | ---: |
| Dynamo + Aegis | 38 | 32 | **70** |
| Aegis + Switchyard | 29 | 28 | **57** |
| Dynamo + Switchyard | 27 | 23 | **50** |

The high results **do not** establish an ideal game difficulty. The simulator chooses matched-friendly storms, and the bot is short-sighted. Across the two batches, Dynamo+Aegis beats Aegis+Switchyard in 15 seeds where the reverse is not true; Aegis+Switchyard wins in two seeds where Dynamo+Aegis does not. Therefore there is a *preference* in this sample, **not an absolute dominant strategy**.

Aegis often reduces raw storm breach damage without spending resources. In 40 development games, the Aegis+Switchyard route benefited from Aegis in 278 of 320 resolved rounds and prevented **115 damage** under the observed policy. Dynamo+Switchyard lacks any such damage reduction. These aggregate shields are part of the engine, but cannot be taken as evidence that humans would prefer the mechanic.

**Important counterfactual to the Phase 3 interpretation:** Switchyard's free movement was previously never used by the bot, so it was unfair to infer it was weak from the win table. I added a *greedy free-shift and paid-edit substitution* policy, then checked exact legality through the reducer. It made 25/29 free shifts in development/holdout Aegis+Switchyard batches and 13/17 with Dynamo+Switchyard. However, it produced no additional victories; it turned one win into a loss in each Aegis+Switchyard batch. On the additional 40-seed stress set it made 27 Aegis+Switchyard free shifts, rescued zero losses and spoiled two wins. **The agent is still short-sighted and cannot co-optimize a future multi-turn move, so this does not prove Switchyard is inherently weak.** It establishes that the attractive-sounding free action is not giving clear realized value *under these policies*.

**Design failure to carry forward:** Aegis is passive and forgiving; Switchyard introduces a conditional free extra action, depth restrictions and activation timing. These systems are not currently comparable in decision agency. Phase 5–7 should challenge reducing Aegis to a controlled power-for-protection choice and simplifying Switchyard, rather than buffing either by fiat. The team also makes construction decisions centrally, making the current design susceptible to quarterbacking.

## 2. Storm Operations: individual cards matter, but passive progress and player-count scaling are serious

The current Operations game has individual nine-card decks, three- or four-card hands, simultaneous orders (one per multiplayer seat; up to two solo), rotating resolution order, six mission types (choose three), and mission victory by completing any two before round eight with positive hull. Storm threat count increases with the player count; initial hull is `4 + players`.

| Players | Development wins / 40 | Holdout wins / 40 | Total / 80 |
| --- | ---: | ---: | ---: |
| 1 | 15 | 9 | **24** |
| 2 | 17 | 18 | **35** |
| 3 | 31 | 34 | **65** |
| 4 | 35 | 35 | **70** |

This curve is concerning even after scaling waves: it becomes drastically easier with additional seats **for this bot and generator**. At the same time, successful runs can have an inactive seat; 7 of 35 four-seat development wins and 12 of 35 holdout wins under the fixed-order bot had at least one player contribute zero cards. That is a poor signal for engagement, though number of cards is not identical to number of meaningful thoughts.

**Missions can complete passively:** In the development 40-seed batch, 8 all-pass four-player games still earned two missions even though the team lost the match; in the holdout another 8 did. Deep Capture was earned in 32/40 and 28/40 passive four-seat games respectively. Automatically appearing Center matches can therefore satisfy an objective without strategic intent. The system needs missions whose accomplishment is *caused by costly action*, not merely scripted storms.

### A crucial bot-confound discovered in Phase 4

The Phase 3 Operations policy awards move proposals in fixed seat order `0, 1, 2, 3` even though resolution initiative rotates. This means the earliest bot gets first pick of beneficial moves; later bots see those advantages already captured.

**40-seed development sample, 4 players:**

| Proposal method | Seat 0 cards | Seat 1 | Seat 2 | Seat 3 | Wins |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixed planning order | 218 | 120 | 109 | 66 | 35 |
| Round-robin first proposer | 112 | 124 | 142 | 118 | 38 |

**Holdout:** fixed proposer uses `[214,135,91,57]`, while rotating uses `[113,138,140,103]`. Wins: 35 versus 36. In the rotating policy, **four wins still have a completely inactive seat** in each sample. These are heuristic results, not evidence of equitable *human* agency. Nonetheless, **much of the severe apparent seat imbalance was a bad evaluation policy, not necessarily inherent in the card rules.** Preserve this correction in future analyses.

Dropping a seat's moves in the fixed-policy counterfactual sometimes hardly changes the outcome (e.g. four-seat development batch, skipping seat 3 turns only four wins into losses), but this is equally confounded by fixed proposal order and must not be described as evidence that the player is unnecessary under optimal play.

### What Operations does better than Engine

Players genuinely own limited tactical instruments; consuming a card changes their future choices, and same-turn independently held cards can combine. Initiative changes the value of commitments; clean full-session tests demonstrate legal causal interventions. This is a real foundation for cooperation—but without a longer-term economy, missions often become achieved-by-default badges and eight rounds tend to consist of isolated responses.

## 3. Forecast Market v0.5: preserve as a control, not automatic winner

Forecast Market combines the charge puzzle with Bridge, Flip, Accelerate and two-storm drafting (two offers, one preview). It has verified positional/timing counterexamples and a functioning research reducer. But its four shared edits remain interchangeable, capacitors are largely a threshold score, and it does not create a lasting player-created strategic position. Earlier research repeatedly found unused edits and weak differentiation of objectives. These findings are from prior experimental seed sets, **not paired to the present two redesigns**; there is no valid raw win-rate head-to-head.

The controls are important: neither new game is proven more fun simply because it has additional systems. Forecast Market remains a fall-back if Phase 5 cannot establish genuine cooperation in Storm Engine or Operations.

## 4. Do we combine both rulebooks now? **No**

A naive hybrid would add Engine's build/power/upgrades to Operations' decks/missions and simultaneous per-seat orders. That introduces *at least* two overlapping victory systems, two consumable resource models, personal decks, persistent outages, initiative/fizzle rules and persistent infrastructure.

There is also a participation incompatibility: Engine budgets **two paid tactical edits** per round; Operations gives up to one to every player. Assigning those two edits among four players would leave at least two with no tactical edit that round, before counting shared construction. Raising the Engine budget to four would fundamentally change damage balance and invalidate the prior evidence. Personal cards may improve cooperation, but **not as an unexamined plug-in**.

Reject the naive hybrid on the rules-complexity/participation gate. It remains legitimate in Phase 5 to borrow *one* element such as owned limited intervention options and test it against a redesigned shared action economy.

## 5. Selected direction and provisional evidence score

**Provisional selection: Storm Engine is the best strategic chassis.** It demonstrates persistent changes, opportunity costs and multiple successful build trajectories in exactly the same waves, while Operations is stronger as a **cooperation laboratory**. This is a conditional selection, not a winner-take-all freeze of Engine's current levels or player model. In Phase 5, openly challenge the choice against Operations and Forecast Market if Engine cannot deliver independent player contributions.

| Dimension | Storm Engine | Storm Operations | Forecast Market |
| --- | --- | --- | --- |
| Lasting changes to future options | Demonstrated (three upgrade tracks) | Mainly personal decks, limited | Temporary investment; limited |
| Shared economic scarcity | Build vs emergency tactics; some investment tension | No energy economy | Flip vs Bridge vs threshold |
| Distinct player-owned decisions | **Not yet** | Card ownership; limited; mixed evidence | **Not yet** |
| Proven player-count equity | No | No (major active win-rate curve) | No |
| Different credible strategies | Multiple winning paths; Aegis favoritism risk | Some mission tactics, passive scoring risk | Tactical alternatives; shallow strategic arc |
| Rules burden | Medium with upgrade exceptions | Medium with hands/recycle/fizzles/missions | Six verbs plus drafting and resources |
| Human satisfaction evidence | **None** | **None** | **None** |

A numeric score would imply human enjoyment data we do not have. Phase 1 weighted dimensions remain the evaluation charter; this evidence matrix and hard gates take precedence over manufactured precision.

### Explicit Phase 5 handoff (cooperative system competition)

Implement and evaluate **three small co-op mechanisms on the same Engine strategic chassis**, instead of adding all three:

1. **Owned limited interventions:** each player has two openly discussable choices, with a modest rotation of who can execute which; avoid frustrating lock-outs. Compare all-permitted versus owned choices and measure lost wins and agency opportunities.
2. **Shared construction commitments:** a strategic investment requires two distinct seat contributions—e.g. one proposes the system to invest in, another selects which resource to forgo—with separate opportunity costs. Solo makes both without controlling four puppets. Verify both decisions can matter and are not just ceremonial votes.
3. **Joint conditional operations:** players publish complementary plans that fire based on the publicly announced storm; reserve scarce planning capacity for contingencies. Ensure hidden information is not used to create arbitrary impossible guesses. Test message burden and whether a one-player solution can simply replace all contributions.

For each mechanism, keep the storm, resources, build goal and public forecast identical where possible, with explicit 1–4-player scaling. Show at least two independently contributing players, with two counterfactual situations where one teammate's action changes what another should do. Reject a mechanism if it only raises win rates or withholds necessary tools. Under the current two-edit budget, a 4-player design requires consequential *non-edit* decisions or a deliberate new action-economy design.

### Other acceptance gates for Phases 5–7

- Replace the current automatic shield bonus if human testing reveals it is a dominant passive upgrade; explicitly test pay-to-protect versus passive armor on paired seeds.
- Create difficulty cohorts with stable 1–4-player win ranges **under appropriately trained agents**, not just wave-count scaling. The present Operations spread is too large.
- Require mission progress to depend on player choices in a substantial fraction of sampled sessions; the current passive Deep Capture violates the intent.
- Establish a fair public-information contract for any early irreversible investment. Compare a decision-maker who sees only current/preview waves with a separate omniscient upper bound.
- Perform **real 1-, 2-, 3-, and 4-person sessions** before claiming quarterbacking is solved or the game is genuinely fun. Track independently originated proposals and adopted plans, not mere clicks.
- If the Engine-based cooperative candidates fail, **reopen architecture selection** before production implementation. This is a feature of the process, not a regression.

## 6. Production and release boundary

**No Engine, Operations, Forecast Market, TypeScript reducer, room/server, Pages code or official golden scenario is modified by this Phase 4 research package.** Phase 5 research can change the experimental designs freely; promotion to production happens only after Phases 5–7 gates pass.

Phase 4 conclusions are provisional about quality but final about **what to test next**. What survives is not a pile of new verbs; it is a strategic chassis plus a controlled three-way co-op experiment.
