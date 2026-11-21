# Gaim improvement roadmap — Phase 1: Core gameplay redesign

Status: **CONTINUE — mechanically implemented and regression-tested, but not accepted as an enjoyable game.**
This is an improvement-roadmap phase distinct from the repository's historical redesign phases.

## Changes shipped

- `site/storm-v2.mjs`: isolated, deterministic Beacon solo ruleset. Historical `site/play-engine.mjs`, its Python counterpart, and old production multiplayer rules stay unchanged.
- Mission: survive 8 rounds with all 3 Beacon cells charged and at least one upgraded system **online entering round 8**. Beacon cells cost 2 Power each, consume the same one-project-per-round slot as building, and can be charged in round 8. Construction activates one round later and is unavailable in round 8.
- Immediate tactical tradeoff: spend 0–2 Power on shielding *before* resolution; each Power blocks 1 raw leakage by default, 2 with Aegis level 1, or 3 with Aegis level 2. No passive protection; offline Aegis grants no multiplier. Unused shielding is not refunded and does not prevent unresolved-charge deadline damage.
- Dynamo level 1 adds +1 Power when a Left collision occurs; level 2 adds +2 Power if any lane collides. Switchyard retains distinct free positioning. Outages, Hull, Coolant, HOLD, DAMP, SHIFT, charge matching, and movement retain the core phase3 puzzle.
- The playable page now has a shared project selection, shield selector, next-wave forecast, Beacon tracker, deterministic current-plan preview, and three new full-game example plans. The rules page matches the new game.
- Python `experiments/phase1_beacon_engine.py` is independently implemented for differential verification. `scripts/generate_phase1_cases.mjs` regenerates sample victories reproducibly.

## Verification evidence

1. Three published storms have complete eight-round winning examples in the new ruleset (final Hull: First Watch 2; Tough Current 1; Power Surge 3).
2. All three examples replay exactly in JavaScript and independently in Python.
3. Forty randomized complete Python sessions exactly match JavaScript state after every round, including paid edits, investments, Power shielding and occasional Switchyard actions.
4. Node tests cover objective constraints, exclusivity, delayed builds, shield spending and effects, outages, action errors, and loss/win edge cases.
5. Chromium UI automation executed eight rounds of each scenario from the sample plan at 390px width, achieving all three victories with no script errors or horizontal overflow; localhost navigation was blocked in the execution environment, so browser assets were injected unchanged except for a data-URL module import and in-memory JSON fetch stub. This does not verify the remote Pages deployment.
6. The complete project `scripts/release_gate.sh` passed locally, including its historical Python/Node/TypeScript suites, release artifacts and Pages verification.

## Limitations and critical next work before accepting Phase 1

- **No human playtesting yet.** This is the main blocker. Invite at least five novice players to complete a solo game from the rules without live guidance. Collect mistakes, confusion points, duration and their individual replay interest. Do not substitute automated policies for human evidence.
- **Balance not established.** Three winning witnesses establish feasibility, not multiple genuinely competitive strategies. Some published scenarios permit wins with any opening system, potentially indicating that upgrades are merely an objective checkbox. Explore meaningful Dynamo/Aegis/Switchyard incentives and compare alternative competent strategies on unseen storms.
- **Decision quality not established.** An exact-information preview may make some consequences easy to optimize. Test whether it supports comprehension without trivializing meaningful dilemmas. Check whether Beacon charging remains a repetitive or obvious choice after the first upgrade.
- **Pacing remains unverified.** Round 1 still has no breaches; eight rounds and the final deadline may feel too short, passive or abrupt. Time human sessions and evaluate dramatic arcs.
- **Replayability/co-op intentionally deferred.** Three fixed storms and solo controls do not satisfy Phases 2–3.

## Suggested human test protocol

Give each participant the prototype and rules; avoid coaching except to unblock a UI failure. After their first game ask, in their own words: (1) What is the objective? (2) Why would you ever prefer to build instead of charge the Beacon? (3) What did your largest shield expense prevent? (4) Which decision would you change if replaying? (5) Do you want to play again? Also record the game length, specific confusion moments, and major strategic choices. Re-run with people who have not seen sample plans, then collect independent written feedback. Do not infer a pass until this evidence exists.

## Roadmap after this delivery

1. **Phase 1 (current):** Human and strategic validation; refine or simplify the new economy and objective if necessary.
2. **Phase 2:** Genuine cooperative action economy and specialist agency (1–4 people).
3. **Phase 3:** Mission and scenario replayability, development variety.
4. **Phase 4:** Strategy balance, difficulty and pacing refinement.
5. **Phase 5:** Single canonical rules engine, persistent online multiplayer.
6. **Phase 6:** Professional responsive UI, tutorials, accessibility and feedback.
7. **Phase 7:** Human retention testing, selective content expansion, release readiness.
