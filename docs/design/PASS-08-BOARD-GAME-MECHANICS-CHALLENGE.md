# GAIM Mechanics Research — Pass 08: Can economy and tempo beat Forecast Market?

**Decision: NO CHANGE.** Keep Forecast Market v0.5 as the leading *research* ruleset; keep the actual shipping v0.1 engine and multiplayer unchanged. The six new experimental configurations did not clear the evidence bar. This is an intentional negative result, not a failed pass.

## Design brief / quality bar

We specifically challenged earlier design drift toward “more buttons = more depth.” The desired medium-weight board-game experience should have consequential choices that can be *wrong*, more than one strong line of play, some opportunity for multi-turn forecasting, distinct teamwork (not four interchangeable edit slots), and a teachable ruleset. We borrowed from (a) auctions and resource bidding, (b) emergency powers and opportunity costs, (c) public upkeep/worker obligations, and (d) push-your-luck/tempo control.

Criteria, in priority order: strategic decision quality; genuine cooperative agency; variety/replayability; clarity/exception count; portrait-mobile execution. Policy wins can only serve as diagnostics, **not** as a proxy for fun. A harder game is not automatically a better game, and alternative victory thresholds invalidate direct win-rate rankings.

## Baseline (unchanged)

Forecast Market v0.5 research: three lanes, three time bands, nine rounds, four shared edits per round; SHIFT, HOLD, DAMP, BRIDGE, FLIP, ACCELERATE; two public incoming storm offers and one preview, with no payment for selecting the newer offer. Charges cancel when opposite signs meet in the same lane on the same breach round. Standard victory requires ≥2 stored power in all three capacitors and ≥8 total while alive.

## Six new executable challengers

All modes operate through immutable wrappers around the existing experiment reference reducers. They do not import into the TypeScript production engine.

| Variant | Exact added or changed rule | Why it might help | Main risk |
|---|---|---|---|
| **Coolant Bid** | Selecting newer storm offer costs **1 coolant before actions**; older offer remains free. | Storm timing competes with the defensive DAMP resource. | Limited coolant makes drafting feel constrained rather than strategic. |
| **Power Bid** | Selecting newer storm costs **1 CENTER stored power before actions**. | Timing competes with investing and final victory. | Punishes the center, increases center-lane bias, can prohibit draft early. |
| **Emergency Repair** | **Once per game**, spend **2 power from one capacitor** and **one of the four edits** to restore **2 hull**, capped at original 7 HP. | Gives hull an economic choice; can rescue a disastrous round. | Tight power victory threshold makes most repairs too costly to win. |
| **Council** | At the **end** of rounds 3, 6, 9, choose a capacitor from public pairs **L/C**, **C/R**, **R/L**; spend 1 power or lose 2 hull. Final goal is **≥1 per lane, ≥5 total, at least 2 successful payments**, plus survival. | Forces planning for future public obligations and different lane priorities. | Changed objective makes comparisons difficult; choices may still be obvious. |
| **Council + Coolant Bid** | Both rules above simultaneously. | Couples long-term resource obligations with storm timing. | Too many resource drains for same small engine. |
| **Storm Surge** | **Once per game**, spend **1 coolant** at planning start to bring **both visible offers this round** (rather than one). Every one of the original seven real waves still arrives exactly once; advancing two now leaves one later storm round empty. No extra edit is required. | Lets players voluntarily accelerate trouble to create larger synchronized matching opportunities; a genuine temporal/tempo decision. | Early surcharge can look beneficial in greedy evaluation, hurting later survival and potentially creating an obvious first-turn play. |

Three tabletop sketches were deliberately **not implemented**, after feasibility review: (1) borrowed action points against next round, because the current underlying reducers *hard-enforce four edits*, so a faithful six-edit round needs an engine-level redesign; (2) private, restricted “operator” hands, because the Pass 06 tests found mostly friction and fewer useful actions; and (3) bidding against teammates for a storm, because competing incentives would violate the game's fully cooperative promise unless there were another independently meaningful payoff. These remain ideas, not tested mechanics.

## Reproducible results

Full nine-round simulations use **identical seeds** in two independent sets: 16000–16023 and 17000–17023. For each mode, a common code path greedily considers eligible individual edits, both market offers, and (where applicable) both Council payments or a Surge. It scores *public* visible formations and resources. It is not an optimal player. The private future storm deck is not consulted by the scoring function, but the reducer retains the full deck for deterministic resolution. The agent does **not** perform deep multi-round tree search.

| Rule set | Set 1 wins /24 | Set 2 wins /24 | Total /48 | Important qualifier |
|---|---:|---:|---:|---|
| Forecast Market control | 17 | 15 | **32** | Standard victory condition |
| Coolant Bid | 16 | 15 | 31 | Standard victory condition |
| Power Bid | 12 | 11 | 23 | Standard victory condition |
| Emergency Repair | 17 | 14 | 31 | Standard victory condition |
| Council Checkpoints | 19 | 19 | **38** | **Different, noncomparable victory condition** |
| Council + Coolant Bid | 16 | 16 | 32 | **Different, noncomparable victory condition** |
| Storm Surge | 15 | 13 | 28 | Standard victory condition |

*Never* rank Council above control because 38 > 32: its final target is fundamentally different. Its stronger showing is a prompt to test a demand-aware, multi-turn solver under carefully calibrated difficulty.

Other diagnostics from the same 48 scenarios:

- Control used **583 of 1,728 available edits** (66.3% unused), confirming that four-player agency remains an enormous unresolved problem.
- Coolant Bid selected the newer storm **90 times**, versus **153** for the free control; Power Bid selected it **6 times**. Neither price currently demonstrates a superior decision landscape.
- Emergency Repair was selected **15 times** but did **not** improve aggregate winning outcomes. Across the paired seed sets, it created no new win when control lost and lost one control victory. The repair cap and the ≥8 final energy requirement pull against each other.
- Storm Surge was used in **46 of 48** games by the heuristic, but finished with four fewer wins than the control. In direct paired results, Surge turned **three control losses into wins**, but **seven control wins into losses**. The mismatch between frequent selection and improved outcomes is especially concerning: the heuristic may be overvaluing early formation or the rule may be a tempting trap.
- Coolant Bid won five games that control lost, but lost six games control won. That's evidence it reshapes decisions, **not** evidence it improves fun or balance.

Exact tests (see `tests/test_phase08_lab.py`) include:

1. A synthetic case in which bringing a +2 and −2 storm simultaneously creates two power in Left and prevents two hull damage; postponing one storm doesn't create the match.
2. A synthetic hull-1 case where spending the last coolant on Storm Surge makes a needed DAMP unavailable, immediately losing the game. Saving the coolant and DAMPing the visible NOW token survives. **Surge can clearly be right or wrong.**
3. A Council final payment from Left wins at power **3–2–1** after two prior serviced checkpoints, while the same payment from Right loses. This proves meaningful choice *at the edge*, but not difficult foresight.
4. Strict resource validation, seeded deterministic replays, once-per-game repair/surge limits, and exactly seven real storm waves conserved after Surge.

The survey's exact inputs and aggregate results are checked in at `docs/design/pass08-results.json`. Reproduce:

```bash
python3 -m unittest tests.test_phase08_lab -v
python3 -m experiments.phase08_survey --games 24 --start 16000
python3 -m experiments.phase08_survey --games 24 --start 17000
bash scripts/release_gate.sh
```

## Judged outcome: why no promotion

**Coolant Bid:** A defensible opportunity cost, but primarily constrains access to Storm Market; no evidence it creates sufficiently difficult new strategic questions. Reject for now.

**Power Bid:** Dramatically suppresses drafts, and creates an arbitrary center-resource privilege. Reject.

**Emergency Repair:** Competent, understandable rule, but largely another tactical safety button conflicting with the near-max energy victory target. Reject under the current win condition. It could merit testing after that target is redesigned.

**Council Checkpoints:** **Reserve challenger.** It is the only contender that materially changes *why a resource matters in the future*, rather than merely adding immediate flexibility. But a test against optimized long-range planning and matched-difficulty missions is essential. We should not force it in without that evidence.

**Council + Coolant Bid:** Complexity compounds and survival drops; no synergy established. Reject.

**Storm Surge:** Strongest original brainstorm candidate of this pass, and specific, working code proves different tactical outcomes. But the 46/48 selection frequency and worse 48-game results suggest it could be a *greedy trap*. Keep its reference prototype for future analysis; do not ship.

### Structural problems none of these fixes

- A single perfectly informed player can still design the entire four-player plan. **The quarterbacking / agency problem remains.** The current public all-actions structure has no proven co-op-specific payoff.
- Repeated randomized storms are not sufficient proof of endlessly replayable strategies. No variant creates a new distinct mission archetype with demonstrated different optimal plans.
- Actual choices in midgame are much narrower than the legal action count implies. The high edit inactivity means simply increasing maximum edits cannot produce cooperation.
- We have no human observation of decision satisfaction, table talk, perceived fairness, or strategic variety. No simulation score can substitute for that.

## Next high-value experiments

1. **Mission generator with solvable public obligations:** Predeclare one of several lane/tempo obligations at setup, search for feasible decks with limited-information agents, and test whether optimal *action categories*, not just success rates, differ between missions. Calibrate comparable difficulty. Test Council here rather than in isolation.
2. **Genuine co-op mechanisms, not artificial action scarcity:** Prototype a plan with two independently proposed *conditional* actions that resolve together (e.g., “shift this if the incoming charge is routed right; otherwise save power”), and compare human contributions to a fully open planning baseline. Solo controls the same two scripts without four unit menus.
3. **Prune existing verbs:** Study action use and pairwise redundancy by removing individual verbs using stronger policies, while preserving a goal-specific affordance. Target a concise modern board-game complexity envelope, not maximal action count.
4. **Challenge Storm Surge more intelligently:** A horizon-3 planner with explicit coolant shadow pricing and visible storm forecasts may avoid the seductive but harmful early purchase. If Surge is rarely correct for that planner, discard it entirely.

**Final status:** Phase 08 is research only. v0.5 stays the *research leader*, Phase 7 v0.1 shipping code/golden traces are untouched, and no new mechanic is promoted without stronger evidence.
