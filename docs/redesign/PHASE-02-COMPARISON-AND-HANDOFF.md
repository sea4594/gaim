# GAIM board-game redesign — Phase 2 comparison and Phase 3 handoff

**Date:** 2026-10-26  
**Decision:** Advance **both** complete preliminary designs; do **not** select a winner. Forecast Market v0.5 remains the external control.  
**Evidence status:** Rulebooks and basic arithmetic smoke fixtures checked; no full independent prototype, balanced scenario population, or human co-op sessions completed.

## 1. Why these really are different games

| Dimension | A: STORM ENGINE | B: STORM OPERATIONS | Control: Forecast Market v0.5 |
|---|---|---|---|
| Primary challenge | Invest scarce power to build 2 of 3 persistent settlement systems | Coordinate individually owned tactic cards to complete 2 of 3 mission objectives | Arrange/transform charges and choose storm order to fill energy meters |
| What changes over time | System levels, available positional/defensive/economic benefits, disabled modules | Personal hand/deck composition, rotating initiative, mission counters | Current charges, stored power/coolant, temporary Bridge |
| Scarce assets | Power, coolant, 2 shared edits, 1 BUILD, remaining hull | Each person's non-replaceable card options this round, hull, deck cycle | Shared action slots, capacitor power, coolant |
| Information | Fully public current + next storm; no private info | Public world + next storm, individually owned private hands; unrestricted communication | Public current offers + next preview |
| Player identity | Minimal: candidates for team strategy; cooperation is known vulnerability | Stronger hypothesis: each player commits from own changing options | Players largely interchangeable |
| Winning | Reach level 2 in any two different systems and survive round 8 | Complete any 2 of 3 selected mission conditions and survive round 8 | Survive nine rounds, fill three capacitors to narrow targets |
| New complexity | 3 systems × 2 levels, purchase lag, system outage | Player decks/hands, simultaneous plans, double targeting, mission counters |
| Intentional removals | Flip, Accelerate, Bridge, Storm Market, lane capacitors | Power, coolant, construction, Bridge, Accelerate, Storm Market | Baseline has all of those actions |

This is **not** a ranking. A might be a deeper solo strategy game but worse multiplayer. B might create engaging coordination but fall apart due to luck and restricted hands. The point of Phase 3 is to find out.

## 2. What has actually been checked

The Phase 2 smoke test `tests/test_redesign_phase2_specs.py` independently verifies:

- Shared `min(P,N)` collision / `abs(P−N)` breach arithmetic.
- The published **eight-round Storm Engine sanity scenario**, including purchases, delayed Dynamo benefit and two restored systems.
- The same Engine storm schedule **without purchases**, which survives but loses the system objective.
- The published **eight-round two-player Storm Operations scenario**, including one DAMP intervention, two completed missions and hull 1 at victory.
- The same Operations waves with no DAMP, which loses the hull on round 7 despite completing missions.
- Basic player-count hull scaling, wave-length assertions, and core document invariants.

These tests are **not** complete rules engines. They omit real card shuffling, token IDs, concurrent editing, offline outages, HOLD timing, paid SHIFT ordering, mission combinations and scenario generation. They are intended to catch blatant rulebook arithmetic mistakes before Phase 3, **not** to certify the design.

### Sanity state summaries

**A, constructive example:** Six matched pairs entered across rounds 1–6, and no further arrivals in 7–8; Dynamo upgrades on rounds 1 and 3, Aegis on rounds 4 and 5. The team survives at hull 6 with levels `[2,2,0]`, power 8 (capped). This is intentionally easy. It demonstrates the economic state transition, not that meaningful strategic alternatives already exist.

**B, defensive example:** Six waves each contain a matched Center strength-2 pair and one unmatched Left strength-1 charge. Two-player hull starts 6. Without interventions, round 7 kills the team; DAMPing the round-2 Left token before breach on round 3 leads to a round-8 hull-1 win. Both Deep Capture and Precision Route complete by round 3. This is intentionally *not* evidence of advanced cooperation—one defensive card suffices. The Phase 3 game must demonstrate materially richer cases.

## 3. Strict promotion criteria for both candidates

1. **Legally replayable sessions:** Full reducer with all rules, deterministic explicit waves/decks, wins and losses at 1, 2, 3 and 4 players. The smoke scripts are insufficient.
2. **Persistent consequence:** At least two reached early-game choices producing different useful capabilities or constraints **three or more rounds later**, and both can be rational under different forecasts.
3. **Real tradeoff:** A resource/option spend is sometimes necessary for a win *and* sometimes loses an otherwise winning scenario; verify at least two non-handpicked reached states per outcome with independent solver/rollouts.
4. **Distinct strategies:** At least two complete winning strategies on one scenario that differ in more than token-edit order. For Engine: different restored-system pairs. For Operations: different mission pairs and actual hand use.
5. **Information fairness:** A policy restricted to actual current/next wave and individual hands must be able to make informed plans. Omniscient solver-only wins are not enough.
6. **Co-op agency:** At 2–4 players, track whose observation or decision changed the final plan, who proposed the move, whether other players could disagree usefully, and idle/quarterbacking frequency. **Human evidence required before claiming success.**
7. **Complexity:** Each new exception must be necessary for an interesting decision. A large increase in cognitive bookkeeping is an explicit penalty, not an accomplishment.
8. **Mobile:** Prove with a simple 360–390px outline that one can inspect current threats, future forecast, available options, and upcoming goals without precision tapping or tiny card text. No polished final UI needed.

## 4. Required Phase 3 mechanical kill-tests

### Storm Engine

- **No-edit / always-Dynamo bot:** If it wins a majority of otherwise fair scenarios and another system order is strictly worse, the economy lacks depth.
- **Module-outage timing:** Scenario where raw `P−N>=2` breaches a system lane; the level is retained but bonus is disabled exactly one following round. Retest when repeated hits extend outages. Check that last-round outages are handled consistently.
- **Hull vs. upgrades:** Find a reached decision where spending 2 to improve Aegis beats spending 2 to improve Dynamo, and another state with the reverse outcome. No fully known optimal purchase recipe should dominate.
- **BUILD purchase timing:** Buying a module just before a collision must **not** give the bonus this round. Losing teams must have a reason they cannot instantly buy out of trouble.
- **Cooperative failure test:** Give four humans the open-information board. If one player naturally makes all purchases and edits while others watch, do not camouflage this using arbitrary per-seat action restrictions; seriously consider rejecting the candidate or changing its shared decision model.

### Storm Operations

- **Real scaling:** Vary player count and arrival count; test surviving sessions under actual card draws, not preselected successful hands. Current `players+1` load may be far too severe at 4p.
- **Hand lock:** Exact tests for same-token SHIFT+HOLD order, SHIFT+FLIP, two SHIFTS, destroyed token+later action, illegal duplicate targeting and timeout PASS. A fizzle consumes a card by design; evaluate whether humans find that reasonable.
- **Passive-farm exploit:** Natural Center pairs can automatically satisfy Deep Capture and Precision Route. If teams can win by drawing good waves and passing, redesign missions to reward deliberate coordination, not ambient collisions.
- **Voice quarterbacking:** With unlimited speech and hands freely revealed, check whether independent commitments actually preserve meaningful choices. A private hand that can be dictated by the experienced player is insufficient.
- **Deck shortage:** Check that a bad early hand never turns the full game into helpless spectatorship. Try public redraw or a weak guaranteed basic SHIFT if needed—but this must **replace** something or earn complexity, not be piled on.
- **Mission order:** If two easiest missions dominate every scenario, redesign the selection and objective interactions before expanding the mission catalog.

### Forecast Market control

Use the real Phase 6 research implementation, not production v0.1, and hold the information horizon and scenario difficulty as comparable as practical. The existing findings are too dependent on short-horizon policies to act as a universal yardstick.

## 5. Honest scorecard before Phase 3

The charter weights are: strategic depth 25%, co-op agency 25%, enjoyment/pacing 20%, replayability 15%, elegance 10%, portrait 5%.

**Do not give false precision.** Without real games and participants, numeric scores create an illusion of objectivity. Instead:

| Question | Engine evidence | Operations evidence | Status |
|---|---|---|---|
| Is the core transition coherent? | Eight-round sanity fixture passes | Two-player eight-round sanity fixture passes | **Provisional yes** |
| Is long-horizon strategy demonstrated? | Investment can affect future production | Card use changes future availability | **Mechanically plausible; not established** |
| Are two different winning strategies verified? | Not yet | Not yet | **No** |
| Are 2–4 players independently valuable? | No structural guarantee | Personal hands make a contribution hypothesis | **Unproven** |
| Is generated content generally fair? | No generator audited | No generator audited | **Unproven** |
| Is the game fun? | No human playtesting | No human playtesting | **Unproven** |

**Provisional choice:** Advance both. Engine is likely more board-game-like in *economic persistence*; Operations is likely more cooperative in *individual option ownership*. Neither advantage is yet demonstrated in play.

## 6. Phase 3 execution order and pivot permissions

1. Implement **one canonical collision/movement kernel** for research parity across A and B: charge entry, HOLD, SHIFT, DAMP, simultaneous matching, raw leakage and deadline. Then add each candidate's independent state wrapper. Avoid polluting production `src/engine.ts`.
2. Implement strict legality, public-view filtering and deterministic scenario hand-off. If the two candidates need different wave arrival rules, keep them versioned rather than fudging data to compare win counts.
3. Replay the Phase 2 smoke fixtures exactly in the new prototypes. Resolve all discrepancies; do not edit fixtures to conceal bugs.
4. Generate complete *reached-state* forks with a bounded exhaustive search or longer-horizon policies; write reproducible winning/loss traces.
5. Compare on strategic variety, decision reversals, rules burden and forecast fairness. Report timeouts and policies' blind spots.
6. **Play both with humans at least informally** as soon as a minimal hot-seat/text interface exists. Quantify whether players want another round and when they become disengaged; don't fabricate this evidence if no testers are available.
7. If neither delivers, pivot before Phase 4. Candidate C might combine Engine's scarce investments with Operations' owned cards, but the hybrid must **replace** redundant mechanisms rather than add two full games together.

## 7. Repository policy

Phase 2 adds **only design documents, JSON smoke fixtures and a small test module**. The historical Forecast Market experiments, production engine, golden traces, rooms, Pages replay viewer and deployment workflow remain untouched. The hotfix must verify a clean `main`, protect diverged remote state, run the complete existing release gate plus new Phase 2 checks, and push only on success. An approved Phase 3 implementation is a separate future hotfix.
