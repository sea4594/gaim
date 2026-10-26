# GAIM board-game redesign — Phase 1 design charter

**Status:** Approved *research brief for comparison*, not a gameplay-rule change.  
**Date:** 2026-10-26  
**Repository:** `sea4594/gaim`, branch `main`; prototype implementation remains untouched.

## 1. North star

> A portrait-native, 1–4-person cooperative strategy game in which players develop a shared situation, face genuinely conflicting plans, and make complementary contributions that produce memorable reversals — with understandable rules and a reason to play again.

The central source of excitement should be **clever decisions under pressure**, not spectacle, breadth of abilities, arbitrary hidden information, or an optimal sequence of clicks. Aim for the approachable depth of a thoughtful modern board game, not a resource-management spreadsheet. A short complete session is preferable to an extended session of repetitive turns.

### What we are **not** optimizing for

- Number of legal actions, features, character classes, technology branches, or board cells.
- Raw bot win rates or number of mathematically solvable states.
- Four action slots being occupied merely to keep four players busy.
- Deliberate secrecy that disappears as soon as players use voice chat.
- Random levels that all ask for the same strategy.
- Permanent preservation of our existing six-action research ruleset.

## 2. Verified starting point and what is still only a hypothesis

| Asset | Current role | Preserve? |
| --- | --- | --- |
| `reference/charge_loom_v01.py`, `src/engine.ts` | Production-compatible v0.1 rules with golden-trace parity | **Freeze as comparison control** |
| `src/rooms.ts`, `server/http.mjs` | Tested headless online room scaffold | Preserve; does **not** prove enjoyable cooperation |
| `contracts/golden-traces.v0.1.json` | Seven replay-verified **selected** wins | Preserve unchanged; **not** a fairness sample |
| Forecast Market research v0.5 (Phase 6 experiment) | Current leading **research** system: 2-offer storm draft + Shift/Hold/Damp/Bridge/Flip/Accelerate | Comparison control; **not** the shipping engine |
| Research passes 7–17 | Tested alternatives and many negative results | Preserve evidence; no automatic rule adoption |
| Pages replay viewer | Disposable documentation of v0.1 | May remain static until a redesign earns promotion |

**Findings supported by existing data:** some charge interventions have non-obvious multi-turn consequences, team actions can be strictly complementary, and the golden paths replay deterministically. **Not yet demonstrated:** meaningful four-player autonomy, repeated viable strategic approaches, limited-information fairness, player enjoyment, or sustained replayability. Do not conflate these.

## 3. Target experience (provisional constraints, not universal facts)

| Dimension | Intent | Research check |
| --- | --- | --- |
| Players | 1–4, with 2–4 being genuinely cooperative, not group-operated solo | Full sessions at all counts; observe per-person decisions, not taps |
| Session | Aim for **12–25 min** after learning; reconsider if tests justify otherwise | Time complete sessions; distinguish first play from experienced play |
| Learnability | A new player can describe the objective and make a meaningful first decision after a short explanation | 5-minute teach **aspiration**, assessed with novices; no false claims before test |
| Depth | Several attractive, conflicting plans; early commitments change later turns | Replay actual counterfactual forks from early, middle and late game |
| Uncertainty | Enough public forecast to plan; limited information may improve teamwork but must not force guessing | Test decisions with player-visible information only |
| Rules weight | Approximately an approachable **medium-weight co-op board game** | Prefer one core resolution model, a handful of verbs and resources; audit each exception |
| Interface | Portrait smartphone, touch, one-hand friendly when practical | Paper-sized 360–390px mockups; no tiny precision taps required to parse game state |
| Accessibility | No reliance on polarity being conveyed by red/green alone | Signed numbers/shapes and textual state available |
| Online | Short reconnections, no voice chat required, voice chat should not invalidate challenge | Protocol tests + human tests with and without voice |

These are **design targets**, not results or promises; the practical thresholds may change with evidence.

## 4. The experience we are seeking

A full session should offer:

1. **Opening orientation:** a meaningful starting constraint or opportunity; the group forms a provisional plan instead of simply fixing the nearest emergency.
2. **Developing position:** a choice that establishes an advantage **and** a weakness lasting several rounds (infrastructure, a scarce private capability, a mission commitment, or something better discovered later).
3. **Interacting obligations:** at least two useful competing demands for time, energy or player capabilities. One choice creates an opportunity another player can exploit.
4. **Adaptation:** a forecast, opponent, or resource consequence makes the original plan less attractive. A good team can reinterpret its position.
5. **A consequential finish:** the result depends partly on earlier decisions, not just on a surprise final die-roll. Defeat is explainable.

A **good round** is not necessarily busy: passing can be meaningful. It must be possible to articulate *which opportunity was forgone* and *why*.

A **good co-op moment** occurs when another participant contributes a non-trivial insight, constraint, option or commitment that makes the joint plan qualitatively better. Merely obeying a team leader's instructions does not count.

## 5. Design pillars, ranked

1. **Shared strategy with individual agency.** Each person has meaningful contributions; contributions combine; avoid a single player's omniscient control. Keep solo elegant.
2. **Persistent consequences.** Early choices create lasting opportunities/liabilities. If the same board effectively resets after each storm, the candidate must find a different source of strategy.
3. **Resource opportunity cost.** The same scarce asset must have at least two attractive uses under different circumstances. Investing, spending and preserving must each sometimes be right.
4. **Bounded, legible uncertainty.** Decisions should be grounded in available information; players can plan robustly against uncertainty rather than suffer hidden traps.
5. **Strategic replayability.** Different scenarios *or different players' choices in the same scenario* should support distinct approaches. Randomized tokens alone do not qualify.
6. **Rules efficiency and tactile readability.** Fewer coherent rules with emergent interactions outrank extra actions and exception cards.

## 6. Comparative lessons, not mechanics to copy

- **Spirit Island:** distinct powers, energy spending, simultaneous planning, and fast/slow timing create specialization and long-range tradeoffs. *Borrow the principle of evolving strategic positions*, not the full card/element system. [Publisher-maintained rules](https://rules.dized.com/game/zuxKPAGpQWaqnMZgld8YBg/spirit-island).
- **Sky Team:** divided resources and interdependent placement decisions make both players consequential even on a small board. *Borrow interdependence*, not compulsory silence or dice placement. [Rules overview](https://boardgamearena.com/gamepanel?game=skyteam).
- **The Crew: Mission Deep Sea:** distributed hands plus mission-specific constraints can make a small action vocabulary replayable. *Borrow the strength of different missions and complementary information*, not restricted speech for its own sake. [Rules](https://www.thamesandkosmos.com/manuals/full/691869_Crew_Deep%20Sea_Manual.pdf).
- **Current Charge Loom:** clear spatial/temporal charge matching and amplification are promising distinctive elements. *Borrow the matching consequences*, not an obligation to retain the three capacitors, fixed nine rounds or six action verbs.

All named games are references for design structures, not claims that GAIM should imitate their expressions or content.

## 7. Explicit boundaries and permission to pivot

**Preserve by default:** manipulating arrival time, spatial synchronization, risky amplification, interpretable outcomes, deterministic simulation. These are hypotheses worth retesting, not sacred mechanics.

**Free to replace:** three-lane board, capacitors, victory condition, session length, Storm Market, action slots, Hold/Shift/Damp/Bridge/Flip/Accelerate inventory, player ownership and scoring.

A candidate can be **less complex** than v0.5 if its decisions are better. A completely different strategic core is allowed if charged-storm mechanics prove an obstacle to the desired cooperative game.

## 8. Non-negotiable decision rules

- No candidate wins merely because its win rate increases or it has more legal actions.
- A new system must **replace or justify** what it adds; state the rule it makes redundant.
- No compelled private-information mechanic without a tested reason that communicating information isn't trivially sufficient.
- No simulated four-player “cooperation” claim based on allocating four virtual action slots.
- No declaration of fairness from an omniscient witness path.
- No feature promotion on hand-built examples alone: include reached states and unseen holdout seeds.
- Human enjoyment and quarterbacking judgments remain **unproven until human sessions**. Mark them that way.

## 9. Phase 1 completion and handoff

**Complete:** design pillars, realistic constraints, baseline inventory, evaluation protocol, and rival briefs are documented. No gameplay rules are promoted; no site/backend changes are required.

**Phase 2 must produce:** two substantially different *complete* preliminary rulebooks, each with board components, setup, exact turn loop, costs, collisions/other resolution, player information, player-count adaptations, progression, victory/defeat and at least three conflict-rich worked situations. Use `PHASE-02-CANDIDATE-COMPETITION.md` as the brief, and `PHASE-01-EVALUATION-PROTOCOL.md` as the evaluation instrument.
