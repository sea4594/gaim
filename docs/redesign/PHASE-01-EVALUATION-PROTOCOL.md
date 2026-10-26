# GAIM redesign — comparison and evidence protocol (Phase 1)

**Use:** In Phases 2–7, compare coherent games instead of accumulating clever rules. This is a research plan, **not** a claim that these tests have been run. Keep separate logs for simulations, designer playthroughs, and human playtests.

## 1. Hard gates (a high weighted score cannot compensate)

**Rules-completeness gate (before any coding):** An unfamiliar implementer could carry out a round without inventing rules. Provide a finite state model, action legality, cost timing, simultaneous conflicts, randomness/visibility contract, loss/win and deadline behavior, and 1–4-player turn participation. Undefined edge cases fail.

**Meaningful-interaction gate (before promotion):** Record at least two **different mechanisms** through which one player's contribution changes another player's options or payoff. For each, give an exact before/after state and a counterfactual without the partner's contribution. Mechanically coordinated actions alone may pass the *engine* test but **not** the human-cooperation test.

**Strategic-path gate (before promotion):** Demonstrate at least two substantially different *credible* approaches to a complete game (e.g., build/economy vs. aggressive mission timing). Show an early action changing later decisions and the cost of the path not taken. Examine several reached states plus withheld scenario seeds. A path that only uses more of one action is not distinct.

**Fairness gate:** Run an agent that sees **only the player-visible information at that decision**, as well as a separately labeled omniscient upper-bound solver. Record the gap and irreversible decisions made before critical facts become visible. Fix invisible forced guesses or explain intentional risk control.

**Complexity/UX gate:** A teachable core and a legible portrait screen. Count independent verbs, persistent resources, phases and exceptions. Compare total explanation burden and the frequency each rule materially matters. A new system that is rarely relevant fails unless it produces exceptional, evidenced value.

**Human evidence gate (later, not Phase 1):** Do not label a concept “fun,” “fair,” “good for four players,” or “replayable” as established until tested with people at 1, 2, 3, and 4 players and repeated sessions. Small samples support iteration, not certainty.

A candidate can receive a **provisional** pass at design/prototype stage with human metrics marked *pending*. Full human gates are not prerequisites to explore a novel concept.

## 2. Weighted qualitative scorecard

Score each dimension **0–4** using the descriptions below. The weighted total is `sum(weight × score / 4)` out of 100. Assign scores independently by two reviewers if available and record disagreement; do not massage scores to match enthusiasm.

| Dimension | Weight | 0 | 2 | 4 |
| --- | ---: | --- | --- | --- |
| Strategic depth | 25 | Dominant or trivial next move | Some tradeoffs; limited lasting choices | Multiple viable long-range paths with consequential counterfactuals |
| Cooperation & agency | 25 | One player can direct all | Useful combos but authority centralized | Complementary decisions from several contributors; demonstrable agency |
| Experience & pacing | 20 | Many empty or rote rounds | Some tension, several dull turns | Consistent tension/reversal, clear decisions, strong ending **observed in humans** |
| Replayability | 15 | Cosmetic randomness | Some varied states, similar plan | Replay prompts different worthwhile plans and adaptation |
| Rules elegance | 10 | Exceptions and bookkeeping dominate | Teachable but awkward | Small coherent ruleset, high interaction-to-rules ratio |
| Portrait suitability | 5 | Needs desktop/full table | Playable with compromises | Core state and actionable forecast readable on portrait phone |

Intermediate scores: **1** = weak/occasional evidence, **3** = good but with a known deficiency. If human observations are missing, mark experience/cooperation *provisional*; do not convert predicted excitement into observed data. Preserve raw notes alongside scores.

**Decision hierarchy:** hard gates → comparison of meaningful player decisions and rule burden → scorecard → creative judgment with explicit rationale. Small score differences do not justify declaring a winner.

## 3. Required evidence packets per prototype

1. **Rules + teach:** at most one-page quick-start, complete longer rules, worked example and rules ambiguities log.
2. **Full traces:** one ordinary success, one failure, one strategic reversal and a complete match for each player count (with automated seats if humans unavailable, marked clearly).
3. **Three contested forks:** two appealing legal plans from the same visible state, their near/far consequences, and why one can be right under different public circumstances.
4. **Two cooperation cases:** at least two independently authored choices whose joint value differs from isolated use; follow with human evidence later.
5. **Three decision horizons:** one immediate tactical decision, one medium-term commitment, one early investment still relevant in the finale.
6. **Rule audit:** count verbs, resources, phases, persistent states, exceptions and dead/automatic choices. List what was removed from Charge Loom.
7. **Comparable-state and distribution analysis:** repeated scenarios, withheld seeds, strategy diversity, frequency of passes, resource uses, terminal reasons, obvious exploits.
8. **Player test record (when available):** session video/notes (with consent), completion time, rules questions, agency ratings, conflict/resolution moments, replay desire, fatigue points.

## 4. Reproducible test design

- Register candidate version, scenario generator, seeds, difficulty and policy parameters **before** looking at holdout results.
- Separate **development seeds**, **holdout seeds**, and **hand-crafted counterexamples**. Don't train/test on the same small scenario bank.
- For alternatives with different win conditions, compare **decision diversity, scarcity, readable threats and session arc**, not raw wins as equivalent successes.
- Include: trivial pass/greedy, one-step, bounded 2–3-step, budgeted information-set search, and (where feasible) more advanced methods with matched computation. Run ablations: remove the new rule, remove one player contribution, remove forecast data, and examine equivalent cost.
- For positive findings give denominators, paired wins/losses, uncertainty and cases where the new mechanic **hurts**. Check whether it is an automatic bonus or a genuine dilemma.
- **Do not** describe synthetic optimizer scores as player preference or fairness.

## 5. Human-cooperation observation protocol

In a later phase, recruit mixed-skill pairs and groups of three/four plus solo playtesters. With consent, observe at least several complete sessions per player count and repeat play on another scenario. This is exploratory; avoid pretending a small convenience sample proves mass appeal.

For every planning round, record whether each participant:

- proposed a plan or modification; 
- noticed information, constraint or opportunity others missed;
- accepted a meaningful risk/resource commitment;
- had their contribution adopted, changed, or considered;
- simply executed another player's instruction;
- had no meaningful input.

Record critical incidents: positive surprise; productive disagreement; quarterbacking; long indecision; unclear outcomes; avoidable information surprises; desire for immediate replay. **Do not use button presses alone as engagement.**

After each session, ask each player separately (1–5): *I made meaningful decisions*, *I understood why we won/lost*, *Our coordination changed the result*, *I want another session*. Also ask: *Which decision was hardest? What would you do differently?* Capture comments rather than optimizing only numbers.

An initial **review trigger** (not a statistical guarantee): if a participant reports agency ≤2/5, if one person directs the overwhelming majority of consequential choices, or if multiple sessions end with “the optimal plan was obvious,” redesign the interaction structure rather than adding superficial roles.

## 6. Phase advancement criteria

| Phase | What qualifies for advancement |
| --- | --- |
| 1 — Charter | This charter, evaluation protocol, baseline inventory and rival design briefs completed; no mechanics promoted |
| 2 — Rival designs | Two genuinely different complete rule systems, explicit examples, no unresolved core procedures |
| 3 — Prototypes | Both games implement full sessions and produce counterfactual decisions; transparent limitations |
| 4 — Select | Evidence packet compares both and original; rejects superficial improvements; chooses or pivots |
| 5 — Co-op | Mechanical complementarity **plus** initial human 1–4-player findings; solo need not puppet four avatars |
| 6 — Replay | Mission/starting variation changes viable plans, not just visuals; no obvious always-best recipe in tested pool |
| 7 — Polish | Unused rules pruned; clarity, pacing, fairness tested with people and agents |
| 8 — Production | Versioned implementation, conformance traces, authoritative rooms, all release gates |
| 9 — Handoff | Full rules, validation status, known weaknesses, tested deployment and next iteration report |

**Do not pretend to have completed a later phase during Phase 1.**
