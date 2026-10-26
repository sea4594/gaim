# Redesign Phase 6 — Cooperative Turn Economy: Four Duties Versus Flexible Crews

**October 26, 2026.** **Verdict: keep flexible crew staffing as a research challenger; NO production promotion.** The revised turn economy adds *real, independently verifiable multi-worker economic consequences*, but neither prototype meets the demanding four-player engagement and anti-quarterbacking acceptance gate. Storm Engine remains the provisional strategic chassis, not an approved multiplayer system.

## The problems addressed

The earlier Storm Engine allows only **two charge edits** per round; four players receive too few chances to act. Phase 5 showed that distributing permissions over those two edits is not a solution, and splitting a known decision into two compulsory approvals is merely procedural. Phase 6 therefore asks whether a team can operate **four different work units** while retaining the tactical charge model and persistent settlement investment economy.

All versions are **research-only** wrappers around the Phase 3 deterministic engine. They use the same eight-round incoming wavebooks, charge collisions, three upgradeable systems, damage, construction delay and victory condition; the production TypeScript engine, server, golden traces and GitHub Pages website are unchanged.

## Two competing playable systems

### Candidate A: Four fixed duties

Each round provides four work units assigned cyclically to seats:

1. **Navigation:** at most one SHIFT or HOLD on a charge.
2. **Control:** at most one DAMP or HOLD on a different charge, with normal coolant cost.
3. **Engineer:** build one standard two-power upgrade (activates next round), or spend one stored power to gain one coolant (maximum three).
4. **Dispatch:** spend one stored power to place a lane-specific cover (prevent up to two points of that lane's breach damage) or attempt to recharge one coolant after a matching collision in a designated lane (no refund on a miss).

The original maximum **two tactical edits per round** remains. Engine systems can still be knocked offline by breaches, and cover does not prevent the round-eight unresolved-charge deadline penalty. Dispatch protection and engineering payment both use **stored power available before this round's collisions**. The economic timing is real: players cannot freely finance everything with the power that the current storm will produce.

### Candidate B: Flexible work crew

The same **four work units** are available, but players may staff stations in different quantities. Each station can receive zero, one, or two units. A second worker unlocks a *specific strengthening effect*:

| Doubled station | Cooperative effect | Cost / tradeoff |
| --- | --- | --- |
| Navigation | Can perform a second SHIFT/HOLD, subject to the total two-edit limit | At least one other workstream receives no unit |
| Control | Can perform a second DAMP/HOLD, subject to the total two-edit limit and coolant | Same workstream tradeoff |
| Engineer | One infrastructure upgrade costs **one** stored power instead of two, still activates **next round** | Two work units occupied; at most one build |
| Dispatch | Lane cover blocks at most three rather than two raw leak points; a successful coolant recharge gains up to two rather than one | Two work units occupied; still spends one stored power |

A staff assignment is an explicit, legal action, not an abstract bonus. A second Engineer really changes how much power remains to fund the Dispatcher or future construction. The entire staffing vector is a shared public commitment; multiple players contributing to one station is meaningful *in the arithmetic*, but still risks quarterbacking when all information is public.

**Player-count normalization:** All variants always have **four work units**. One human controls four; two humans control two each; three humans split two/one/one (the double-workload rotates); four humans receive one each. The total work budget never grows merely because more people joined. Explicit seat-to-station assignments are validated; the same legal work plan resolves identically for one or four humans. This addresses power inflation, not social engagement.

**Scope exclusions:** No new mission decks, personal asymmetric powers, artificial lane ownership, secret numbers, or combat phase. The study is deliberately about whether flexible commitment improves the underlying turn, not about piling on new rules.

## Verified causal example: support + protection are both required

In a constructed, legal round-seven position with one hull, two power, a level-2 Dynamo, a level-1 Aegis, a level-0 Switchyard, and an imminent strength-two breach in Switchyard's lane:

- Assign **two Engineers + one Dispatcher + one Navigator**.
- Engineers install level-2 Aegis **for one power** (activates next round).
- Dispatcher spends the **other power** covering the exposed lane.
- The settlement survives the breach at one hull; in round eight, Aegis activates, leaving two functioning level-2 systems: **WIN**.
- With only one Engineer, building and covering together costs **three** when only two are stored, so the combined plan is illegal.
- With two Engineers but **without protection**, the settlement loses immediately to hull damage.
- With protection but **without construction**, it survives but fails the level-2 system objective: **LOSS_SYSTEMS**.

This is independently executed against the actual prototype reducer and regression tested. It is convincing evidence of a *causal joint work plan*, but does not prove that two people would independently discover or enjoy it.

## Paired full-session surveys

Forty reproducible eight-round storm sequences per set, with three previously established infrastructure strategies alternating by seed. All compare exactly matched storms within each set. The original Phase 3 Storm Engine reactive policy is the baseline. Both crew policies use that same edit heuristic and target-build ordering. Candidate B uses a **one-ply centralized planner** to select the best of all 19 legal staffing distributions based on immediate post-round state value; Candidate A must always staff each station exactly once.

| Variant | Development victories / 40 | Holdout victories / 40 | Holdout hull average |
| --- | ---: | ---: | ---: |
| Unmodified Storm Engine control | 32 | 30 | 3.73 |
| A — Fixed stations | 26 | 24 | 3.92 |
| B — Flexible work crews | **37** | **35** | 5.78 |

**Important interpretation:** These are **different action economies**, not balanced alternatives with matched power levels. Improved flexible-crew win rates can result primarily from the *discounted upgrade* and *direct breach prevention*, which make the game easier. They are **not evidence of stronger strategic depth or enjoyable teamwork**. Candidate B also receives additional one-ply policy search that fixed stations do not require, and one heuristic build order is not an optimal solver.

Complete-game replay witnesses demonstrate both sides: on seed **231001**, flexible staffing wins where fixed loses, while seed **231003** is a **fixed-staffing win but flexible-staffing loss**. A separate holdout rescue is on seed **232005**. All witnesses contain actual incoming waves and each seat's assignments and orders; an automated test replays the exact eight rounds and outcome, and recomputes both 40-seed survey outputs.

### How many seats actually contribute?

The most important negative result is that **four work units ≠ four useful player decisions**. A seat is counted active if at least one of its staffed stations executes a non-PASS decision. Being assigned a station alone does not count. Seat counts include a supporting Engineer's real build discount, but we still cannot infer *independent judgment* from the outcome.

| Four-player measure | Fixed duties | Flexible work crews |
| --- | ---: | ---: |
| Development rounds with all four seats active | 13 / 311 (4.2%) | **55 / 320 (17.2%)** |
| Holdout rounds with all four seats active | 21 / 317 (6.6%) | **49 / 320 (15.3%)** |
| Holdout seat 1 active rounds | 149 / 317 | 168 / 320 |
| Holdout seat 2 active rounds | 112 / 317 | 173 / 320 |
| Holdout seat 3 active rounds | 195 / 317 | 223 / 320 |
| Holdout seat 4 active rounds | 151 / 317 | 203 / 320 |

These numbers are stronger than Phase 5's two-action-per-round architecture but **fail the requirement that every teammate has regular substantive participation**. Many assigned stations have no useful order, and flexible staffing's additional power removes pressure rather than creating more difficult decisions. Most crucially, a centralized solver chooses everything; no test can demonstrate resistance to quarterbacking.

## Methodological limitations and explicit rejection criteria

- **No human playtest.** The experiment cannot establish fun, good communication, fair ownership of plans, attention, or quarterbacking resistance.
- **No real limited information.** The current wave is public, and the staffing plan is entirely determined from shared facts. Adding private forecasts would be a separate, potentially counterproductive mechanic.
- **Unequal strategic power.** Engineer's second worker discounts construction; cover makes damage avoidance easier; endgame win-rate comparisons are therefore not apples-to-apples difficulty comparisons.
- **Single heuristic and one-ply allocations.** Fixed crews' poorer wins may be policy artifacts. Flexible crews sometimes make worse long-term choices, including an actual full-session loss where fixed wins.
- **No human decision time measurements.** Four stations may require more cognitive overhead than their added value justifies, especially on phones.
- **No independent agency benchmark passed.** Actively staffing a worker may be a meaningful decision in theory, but executing a common solver's allocation isn't equivalent to different teammates having distinct valuable information or judgments.

**Phase 6 research verdict:** Preserve the *flexible allocation of a fixed total work budget* and the *support + cover + future infrastructure* interaction as **promising research**, not a settled rule. **Do not promote either complete crew structure.** Reject fixed duties as the final solution: they make players wait for their station to have something useful to do. The cooperation acceptance gate remains open.

## Reproduction

```bash
python3 -m experiments.redesign_phase6.survey --start 231000 --n 40
python3 -m experiments.redesign_phase6.survey --start 232000 --n 40
python3 -m experiments.redesign_phase6.make_witnesses
python3 -m unittest tests.test_redesign_phase6_crews -v
bash scripts/release_gate.sh
```

## Roadmap adaptation after this phase

**Phase 7 — Human-operable cooperation and engagement prototype:** before missions or balancing, strip the staffing menu down to a small number of hard tradeoffs, build a barebones pass-and-play/seat-by-seat prototype (not the full UI), and test whether people actually independently contribute; add light asymmetric information only if it creates real decisions. Record seat-specific decision frequency, communication, quarterbacking, and rules friction. A scripted bot is not enough.

**Phase 8 — Strategic variety and replayability:** missions, setups and threat patterns must change the preferred development plan and player interactions; evaluate multiple viable paths against one another.

**Phase 9 — Rules refinement and balance:** tune permanent defense, build discounts, throughput, 1–4-player scaling, difficulty and session arc; remove systems that fail complexity/engagement tradeoffs.

**Phase 10 — Production multiplayer and portrait UI:** implement only accepted rules in the canonical TypeScript engine, server and mobile interface, with full gates and trace conformance.

**Phase 11 — Whole-game review:** audit replayability, agency, complexity and fun across human sessions; retain the ability to pivot or simplify further.

The additional phase is intentional. It would be counterproductive to build content around an unresolved participation problem.
