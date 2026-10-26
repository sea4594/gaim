# Redesign Phase 5 — Cooperative Architecture Experiments

**Date:** October 26, 2026. **Outcome:** No cooperative rules promoted. The Phase 5 research pass is complete, but the board-game cooperation acceptance gate is **NOT** met. Storm Engine remains the provisional *strategy chassis*, not a chosen multiplayer game. The next phase will focus on rebuilding the cooperative turn economy before adding scenario variety.

## Why this pass matters

Two paid edits per round were inherited from solo Storm Engine. Four humans controlling a shared pair of edit slots cannot each execute a tactical decision every round; dividing those slots into permissions does not solve the issue. Phase 4 also established that naive card-action counts can be badly confounded by automated proposal order. We therefore compare three *separate*, small systems with paired, reproducible complete sessions and explicitly distinguish active contribution from mere menu ownership.

### Rules of the three prototypes

These are experimental wrappers around `experiments/redesign_phase3/engine.py`, never production rules. All storms, collision rules, upgrade paths and win conditions are otherwise unchanged. No new character abilities, missions or decks were added.

**A — Owned Interventions.** For 2–4 players, each seat may author at most one paid Shift, Hold or Damp, only on a charge currently in its assigned lane; two total paid edits remain. Lane assignments rotate each round; in four-player mode the duplicated lane pairing rotates as well. Solo retains both original edit slots without ownership restrictions. Upgrade selection remains open. Thus this tests whether distributing *permissions* under a shared bottleneck creates agency; it does not quietly introduce more edits.

**B — Joint Investment.** At most one infrastructure upgrade per round. Two seats rotate responsibility: *proposer* chooses which of the three settlement systems to upgrade; *financier* selects Standard (2 existing power, activates next round, identical to base Engine) or Rush (3 existing power, activates **this** round). Both choices are required. Rush's extra power is spent before this round's matching and can immediately alter defense, bonus production, or the final victory condition. Already-completed or offline systems remain ineligible. Solo makes both choices without extra avatar turns. Tactical edits stay the original shared pair. This is intentionally a **small** timing-versus-cost economy, not a separate construction game.

**C — Guarded Order.** Two multiplayer seats jointly commit a primary edit, a different-target backup edit, and a public predicate such as `Left leak after primary >= 1`. The engine first computes provisional post-primary breach/matches, then executes the backup if the predicate holds; only an executed backup spends an edit and coolant. Guard detection precedes actual breach resolution. The full current storm is public and there is no hidden random event. This is a strict comparison against a normal fully informed second edit, rather than artificially rewarding conditionality by withholding public information from the baseline.

## Verification approach

* Paired 40-seed development (`121000..121039`) and separate 40-seed holdout (`122000..122039`), with three existing build strategies alternating by seed. All models use the same seeded eight-round wavebook for each comparison.
* Baseline reactive agent is reused. For Owned, the agent's open best action list is **filtered**, not re-optimized for the lane constraints. This disadvantages Owned; do not call the outcome difference the optimal-rule value of ownership.
* Joint Standard uses exactly the Engine policy and is a control. Joint Rush uses a deliberately narrow, public, non-clairvoyant heuristic: rush only a level-1 target on round eight when three stored power is available. Other plausible timing policies are not tested.
* The guard comparison uses seeded board arrivals plus identical explicitly constructed imminent charges to exercise both true and false branches. These are **not natural full-game incidence rates**. Because both primary decision and guard input are public and deterministic, a fully informed regular edit always produces an exact counterpart.
* The two selected complete-session witnesses contain actual incoming waves and every committed decision, and are replayed with the real research reducers; there is also a handcrafted single-round example establishing target-versus-funding causality.
* No humans played these versions. No evidence here can establish enjoyment, genuine anti-quarterbacking, player skill fairness or balanced 1–4-player difficulty.

Reproduce:

```bash
python3 -m experiments.redesign_phase5.survey --start 121000 --n 40
python3 -m experiments.redesign_phase5.survey --start 122000 --n 40
python3 -m experiments.redesign_phase5.make_witnesses
python3 -m unittest tests.test_redesign_phase5_cooperation -v
bash scripts/release_gate.sh
```

## A — Owned Interventions: four seats still share two edits

| Players | Dev baseline / 40 | Dev Owned / 40 | Holdout baseline / 40 | Holdout Owned / 40 | Blocked original-agent edits (Dev + Holdout) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 34 | 34 | 32 | 32 | 0 |
| 2 | 34 | 18 | 32 | 19 | 219 |
| 3 | 34 | 31 | 32 | 28 | 52 |
| 4 | 34 | 33 | 32 | 30 | 41 |

The two-player case often assigns both best actions to the same person's lane, forcing the prototype to drop an edit (219 dropped across these two samples). With three or four players the owner coverage is somewhat broader, but at **four players and only two edits, at least two players cannot execute a paid charge edit in every played round** (630+ such seat-rounds per 40 games; exact values in result files). Changing who owns which lane doesn't remove the scarce-action bottleneck.

Four-player edit usage after rotating lane ownership was `[69,66,87,89]` (development) and `[71,63,71,74]` (holdout), without the extreme first-seat bias of the earlier Operations bot. Still, **number of moves is not agency**, and unused seats could discuss options freely even if they cannot press an edit.

**Verdict:** Reject lane ownership as the cooperation solution. The solo game remains intact, but multiplayer gets restricted choices without new meaningful responsibilities. Not an optimal-search comparison.

## B — Joint Investment: real interaction, not proven teamwork

Under both sets, ordinary two-power joint Standard play returns the exact same result as original Storm Engine. In four-player mode, the narrowly triggered Rush variant yields **37/40 vs. 34/40** baseline development wins and **35/40 vs. 32/40** holdout wins, with three final-round Rush actions per batch. The totals are identical for 1, 2, 3 and 4 players because the same agent chooses target *and* funding in every setting.

There is a verified **two-dimensional causal example** on a valid round-eight state: hull 1, power 3, current Dynamo level 2, Aegis level 1, incoming unmatched strength 2, and Switchyard level 0. `propose Aegis + fund Rush` raises defense immediately and completes the second level-2 system: **WIN**. Holding target constant and choosing Standard gives **LOSS_HULL**. Holding Rush constant and choosing Switchyard also gives **LOSS_HULL**. This demonstrates that each component of the joint decision can be consequential under the rules. It does **not** demonstrate that two humans will form independent judgments when they know the same public information.

A complete 8-round witness on seed **121013** also moves from **LOSS_SYSTEMS** with the original build sequence to **WIN** with the late Rush intervention. This illustrates both the real timing choice and a **red flag**: Rush can become a late shortcut that weakens the need for carefully planned infrastructure timing.

Across the 40 holdout four-seat games, there were **160 affordable construction rounds**, on average only four of eight rounds. Outside those turns, the two extra strategic roles are absent; charge edits remain centralized. No evidence supports four consistently engaged players. The Rush policy is intentionally weak and only tests last-round timing, not broad viability.

**Verdict:** Preserve the target-versus-timing tradeoff as a *candidate research interaction* but **do not promote joint construction**. The interaction can be assigned to two seats, but structural separation of buttons is not proof of cooperation. Test with human collaboration and a less abusable activation rule only if a redesigned four-player turn economy needs it.

## C — Guarded Orders: redundant under public information

Both 80-case development and 80-case holdout checks (constructed board probes) produced exact equivalence to a plain, informed sequence of charge edits: 80/80 and 80/80. Half of the test conditions triggered; half did not. The backed-up edit condition affects the executed action list, but a fully informed teammate can simply submit that same action list directly with no new state, predicate or rulebook cost. This is a deterministic semantic equivalence, not an estimate of human performance.

**Verdict:** Reject under public-storm rules. Only reopen if an independently worthwhile uncertainty/reveal system exists; never introduce artificial ignorance purely to justify the conditional order.

## The real discovery: design the four-player action economy, not another edit

A cooperative strategy game needs useful work for four people. We have shown that two charge edits plus intermittent shared investment leaves that requirement unfulfilled. Adding an authorization layer to one centrally solved move is likely to *increase* quarterbacking friction instead of reducing it.

### Decision

* **Promotions to production or provisional accepted rules: NONE.** Leave Forecast Market v0.5 and the working production game unchanged. Storm Engine remains a strategic *chassis only*.
* **Keep:** charged collisions with temporal movement, an evolving settlement economy, the insight that investment timing creates interesting survival/goal tradeoffs, and the lesson that bot proposal order needs rotation in evaluations.
* **Drop from shortlist:** lane-ownership permissions and guarded orders with fully public information. Keep Joint Investment as a documented test case, not a selected co-op architecture.
* **Phase 5 acceptance gate is not passed.** This is a completed *research phase* with negative findings, not a completed successful multiplayer redesign.

## Revised remaining phases (adaptive)

The original Phase 6 would have moved directly to replayability. That is premature while four-player agency is still unresolved. Instead:

* **Phase 6 — Cooperative core rebuild (new hard gate).** Prototype a genuinely multiplayer *turn economy*: each player should have one consequential lever or resource decision per round, whether it contributes to storm control, settlement operation or future preparations. A game may deliberately allow passing, but not two structurally excluded seats every round. Compare fully open communication with bounded, fair individual options; test paired sessions and action ablation; conduct actual human playtests before claiming reduced quarterbacking. If the Engine chassis cannot support this elegantly, pivot to an Operations-derived game with persistent strategy.
* **Phase 7 — Strategic replayability.** Add variable scenarios and mission incentives only after Phase 6 proves a viable co-op turn. Verify different long-term plans remain viable and missions require deliberate investment.
* **Phase 8 — Balance, pacing and simplification.** Audit economies, player-count difficulty, unclear information, overpowered passive Aegis, late-round loopholes and complexity; run human tests, prune aggressively.
* **Phase 9 — Production integration and portrait multiplayer UI.** Implement accepted rules in deterministic TypeScript engine and online rooms, preserving full release gate; upgrade GitHub Pages preview incrementally.
* **Phase 10 — Whole-game audit.** Evaluate full sessions with people and algorithms, assess onboarding, long-term replayability and the co-op experience; review shortcomings without inventing success.

No phase is allowed to automatically graduate to production on synthetic win rates alone.
