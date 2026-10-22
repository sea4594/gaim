# GAIM — Phase 5: Finalist Decision and v0.1 Rules Freeze

**Status:** Phase 5 complete; **Charge Loom** selected as the next engine implementation target.  
**Date:** October 21, 2026.  
**Scope:** Headless rules and design decision, **not** a polished or human-validated cooperative game.  
**Repository target:** `~/Desktop/gaim`, branch `main`; not mounted in this environment. No GitHub push has occurred.

## Executive decision

**Build Charge Loom v0.1**, a cooperative, nine-round crisis game about synchronizing opposite storm charges across **three lanes and three time bands**. Each round, the team can change the course of at most four charges by shifting them sideways, holding them one turn (thereby strengthening them), or damping them using a limited coolant supply. Charges that arrive simultaneously in the same lane partially neutralize, making scarce power; the unmatched strength damages the settlement.

It wins this design comparison **because its interesting tradeoffs are both explainable and reproducible in code**. In one verified two-round situation, the tempting immediate match loses, while sacrificing a hull point and increasing a charge's strength enables a later victory. In a separate verification, neither player's shift has a useful effect alone, but two shifts together prevent damage and generate power. Both examples survive the v0.1 deadline correction.

This **does not mean the game is demonstrably fun, unique in an absolute sense, or solved for 1–4 human players**. In particular, the four-player action economy is not yet acceptable as proven. Phase 6 should test it early, before implementing the multiplayer server in earnest. This is a decision about the strongest **prototype candidate**, not a claim that commercial-quality gameplay has been established.

## 1. What competed, and why the others did not win

| Criterion | Charge Loom | Echo Orders | Ecosystem Siege | Law Loom challenger |
|---|---|---|---|---|
| Core rule teachability | Three manipulations + one collision arithmetic rule | Recurring command queue and upkeep | Feeding cycle, migration scoring, breeding, habitat, tides | Conditional global effects with interaction ordering |
| Exact strategic reversal | Demonstrated and mechanically enumerated | Zap-before-Harvest mistake demonstrated, but strategic depth not established | Gate/bait extraction reversal demonstrated; myopic policy succeeded often | No robust executable rules prototype |
| Two-action cooperation | Two shifts needed to create a match | Multiple echoes can help or interfere | Gate/attract interactions | Could be joint law composition but unproven |
| Planning across turns | HOLD changes timing **and** magnitude | Repeated actions create future obligations | Consequences depend on ecological migration | Temporary laws influence multiple beats |
| Portrait-native board | 3 × 3 visible matrix | Three defense lanes, units and echoes | 3 × 4 habitats with three species each | Law grammar could consume space |
| Main unresolved weakness | Some four-player idleness; shallow matching risk | Dominant basic command patterns; precedent in command-programming | Comprehension and near-term control dominance | Cognitive load, rules explosions |

**Decision:** Charge Loom is the clearest testable foundation, *not* necessarily the most ambitious fiction. Echo Orders is archived as a backup for temporal commitment ideas. Ecosystem Siege is archived as a possible later expansion mechanic, but should not be inserted into v0.1. Law Loom is not sufficiently specified to displace the tested alternative.

### Novelty audit

*Into the Breach* already demonstrates complete-information tactical consequence management; *SpaceChem* has deep spatial-and-temporal synchronization; *Space Alert* uses cooperative timed joint planning. These precedents matter. Charge Loom's distinctive hypothesis is **timed opposite-charge matching with an option to voluntarily amplify the danger you are postponing, while meeting distributed lane goals**. We cannot assert that no existing game shares this exact arrangement without a much broader review. Links: https://store.steampowered.com/app/590380/Into_The_Breach/ ; https://zachtronics.com/spacechem/ ; https://czechgames.com/files/rules/space-alert-rules-en.pdf .

## 2. Complete provisional rules — **Charge Loom v0.1**

The final Phase 4B prototype was labeled v0.3 **within its experimental sequence**. Here we freeze the game's first **implementation specification** as v0.1; it has one important difference from that experiment: unresolved charges at the final deadline now cause damage instead of disappearing.

### 2.1 Objective and physical state

- **Lanes:** Left, Center, Right; indexed 0, 1, 2.
- **Time bands:** FAR (2), SOON (1), NOW (0). All charges move one band toward breach each round unless held.
- **Charge:** unique ID, polarity `+` or `−`, integer magnitude 1–3, lane, band, and a one-time `already_held` flag.
- **Starting hull:** 7 HP. At 0 HP or below, lose immediately.
- **Three capacitors:** one per lane; all start at 0, each holds at most 3 power.
- **Coolant:** three units total for the full session. It does not regenerate.
- **Rounds:** nine. New storm charges arrive in rounds 1–7. Rounds 8–9 are cleanup/finalization.
- **Victory:** Finish round 9 with positive hull, **each** capacitor at least 2, and total stored capacitor energy **at least 8**. All requirements must hold.
- **Loss:** Hull reaches zero, or the final victory check fails at the end of round 9.

### 2.2 Incoming storm and information

There are exactly 18 arrivals spread as `3, 2, 3, 2, 3, 2, 3` across rounds 1–7. A deterministic seed defines nine positive and nine negative tokens, shuffled subject to avoiding a completely one-sided three-round window, with each charge in a random lane and initial magnitude sampled from `[1, 1, 2]`. This balance is **by count**, not total strength, and does **not** guarantee a winnable session.

The current round's arrivals appear at FAR **before** the team commits actions. All active charges are public. The next round's arrivals are visible as a preview; later waves are not revealed in the intended UI. The underlying seed provides determinism for replay and debugging, not secret actions.

**Important content policy:** Until a full scenario generator/solver exists, the normal playable pool must consist of **witness-verified scenarios** only. We have seven (`3, 8, 10, 14, 15, 17, 18`) with re-executable winning command histories. Raw arbitrary seeds are an experimental developer mode, not guaranteed-fair levels.

### 2.3 Actions — only three verbs

A shared team may submit **zero to four edits** for a round. Each token may be edited **at most once in that round**, including if different players submit edits. Actions are selected against the post-arrival state and applied as one joint plan; editing order cannot change the outcome.

| Action | Cost | Exact effect | Tradeoff |
|---|---|---|---|
| **SHIFT(token, direction)** | One edit | Moves the token by exactly one lane left or right, remaining on the board's 0–2 lanes | May route into another charge or leave a different lane unprotected; cannot also HOLD it this round |
| **HOLD(token)** | One edit; once per token's lifetime | The token skips this round's downward movement; magnitude increases by **one** to a maximum of 3; set `already_held=true` | Gains time and possible energy yield, but increases its potential damage and creates next-round liability |
| **DAMP(token)** | One edit **and** one coolant | Decrease token magnitude by exactly one; if reduced from 1 to 0, remove it | Prevents present damage at the cost of scarce emergency capacity and possibly lost future power |

There is no attack verb, no shop, no hidden player class, and no special character abilities in v0.1.

### 2.4 Complete exact round sequence

1. If already terminated, reject further edits.
2. Increment to the next round and **spawn** that round's charges at FAR (if within rounds 1–7).
3. Accept a joint plan of 0–4 edits. Reject as a unit if the plan contains any bad token ID, prohibited direction, repeated target, second HOLD on a token, insufficient coolant, or excess edit count. Do not silently resolve only the good parts.
4. Apply legal edits atomically. Each HOLD increases magnitude and flags its token; each DAMP reduces magnitude (delete 0-strength tokens); each SHIFT moves one lane.
5. All tokens not held **this round** descend one time band. Held tokens remain where they are.
6. For tokens that exit past NOW, resolve **each lane independently and simultaneously**. Let `P` equal the sum of positive magnitudes in that lane's breach, and `N` equal the sum of negative magnitudes:
   - Matching strength `C = min(P, N)`.
   - Lane capacitor becomes `min(3, current_capacitor + C)`.
   - Hull loses `abs(P − N)` HP.
   - Remove every breached token, matched or unmatched.
7. **Mandatory final cleanup, v0.1 change:** At the end of round 9, all tokens *still on the board*, including tokens held through the deadline, **leak their full magnitude as additional hull damage**, **without producing power**. They cannot disappear for free or match across different time bands. Remove them all.
8. If hull is now 0 or lower, lose. Otherwise, at the end of round 9, check the three capacitor conditions; win only if all hold. If it is not round 9, continue.

A ROUND-9 HOLD cannot dispose of danger for free. Earlier game experiments inadvertently allowed such a loophole and their victory statistics should not be carried over to this corrected ruleset.

### 2.5 Exact examples

**Breach math:** `+2` and `−2` exiting together in the Center generate 2 Center capacitor power and deal 0 damage. `+3` and `−1` together generate 1 power and deal 2 damage. `+2` on Left and `−2` on Right do not interact: together they deal 4 damage. A matching pair in a full capacitor still neutralizes safely but yields no additional stored energy.

**Multi-turn sacrifice wins:** At the start of round 8, hull 3, capacitors `(3,2,1)`, Center NOW contains `+1` and `−1`, Right SOON contains `−2`. Doing nothing yields an immediate Center match, but leaves Right below target at the deadline. Instead, HOLD Center `+1`. It grows to `+2`, remaining at NOW; the Center `−1` breaches and costs 1 hull. On round 9, SHIFT the held `+2` into Right as the Right `−2` arrives. They cancel, yielding final capacitors `(3,2,3)` and hull 2: **victory**. Exact executable verification included.

**Two-person action interlock:** With one `+1` in Left NOW and a `−1` in Right NOW, shifting either charge into Center alone does nothing useful: both leak. Shifting **both** to Center in the same plan produces 1 Center energy and saves 2 hull. This is strict complementariness, not simple parallel work. Exact executable verification included.

**End-turn exploit removed:** At round 9, hull 3, capacitors `(3,3,2)`, and a solitary Left NOW `+3`, the previous experiment would award victory if that token were held, because it remained on the board past the ending. Under v0.1, holding that charge results in a final leakage of 3 HP and **loss**. No free storm disposal.

## 3. Multiplayer contract for implementation

The game has one shared authoritative board, hull, coolant reserve and set of capacitors. Players should **co-author a plan** rather than act in arbitrarily ordered realtime clicks. Edits are tentative until team lock. The server validates the merged plan and applies all changes simultaneously.

| Players | Ownership of up to four edits per round |
|---|---|
| 1 | Solo player can author any/all four; no artificial team-mate management |
| 2 | Each player owns two slots |
| 3 | Distribute 2/1/1; the extra slot rotates from round to round |
| 4 | Each player owns one slot; PASS is permitted |

Show everyone a shared prediction of the consequences of the *currently proposed merged plan*. Use a state-version number so stale edits and reconnection replays cannot be committed twice. Server-side resolution must remain independent of client ordering. Timers, readiness votes, and player replacement semantics belong to Phase 6.

**This ownership scheme is provisional and has a genuine flaw.** In seven verified winning bot sessions, only 13 of 63 rounds used all four edits; in the other **50**, at least one person would have no edit to make. Passing or merely pressing a readiness button is *not* the same as an interesting player choice. Four-player engagement is a **go/no-go design gate**, not a solved requirement. The open-information board also permits quarterbacking; neither a cooperative label nor equal slot ownership cures it.

Do **not** add cosmetic roles just to make the game feel like co-op. In Phase 6, first evaluate (a) richer incoming scenarios that produce more meaningful simultaneous edits, and (b) an alternative plan-authorship mechanic in which every participant has a strategic commitment, without making solo a tedious four-character game. Any new mechanism must be tested with actual people before becoming part of the permanent rules.

## 4. Adversarial verification in Phase 5

All tests below are **machine simulation**, not estimates of enjoyment. Scripts and results are in this package.

### 4.1 Worked scenarios

- **150** seeds passed deterministic replay and state-bound checks (wave signs, strength caps, coolant, capacitor caps, final cleanup).
- **Four** classes of invalid-action plans were rejected.
- Two-player action synergy example was reproduced exactly.
- Multi-turn sacrifice-to-win example was reproduced exactly.
- Finale loophole reproduced on the old engine and blocked on the new engine.
- Enumerating **all legal two-turn edit sequences** from the designed dilemma finds **25 winning command sequences, all containing HOLD**. These are distinct raw command sequences, not necessarily 25 distinct human strategies; many are variants with extraneous actions. The important result is that a winning path requires the risky temporal action, not simply the immediate match.

### 4.2 Recalibrated bot comparisons

The stronger **Phase 4B** capped model had reports of 12/24 and 12/24 wins by its two-step heuristic, but it still contained the finale loophole. Those results **do not** validate v0.1.

Re-running the *unchanged* approximate policy on the corrected v0.1 model:

| Independent scenario set | One-step heuristic | Two-step heuristic |
|---|---:|---:|
| Seeds `0–11` (development) | 2/12 | 3/12 |
| Seeds `100–111` (held aside) | 2/12 | 3/12 |

The two-step policy is modestly ahead in these tiny samples, but the difference is **not conclusive**. Both agents are imperfect, hand-authored search heuristics, not humans or optimal solvers, and neither proves that the other policy's failures were inevitable. The overall low win rate of these bots suggests tuning and solvability work remain necessary.

### 4.3 Verified playable content

Using the corrected engine, we found and replayed seven full winning transcripts for initial seeds **3, 8, 10, 14, 15, 17, and 18**. A seeded scenario joins the initial playable pool **only if a complete legal action trace actually wins on replay**. This is a constructive *existence witness* for those scenarios, not a proof that every random seed is solvable or that the levels are properly balanced.

From these seven **selected winning transcripts**, average usage is ~**2.38** edits per round (150 actual edits over 63 rounds): 64 shifts, 70 holds and 16 damps. Four slots were used in only 13 of the 63 rounds. Those frequencies are a warning about four-player participation; they are not representative of all gameplay or human behavior.

## 5. The provisional game promise

**Pitch:** “You can't destroy the storm. You need to make opposite charges collide to power your settlement. Every delay makes the storm stronger.”

**Likely delight:** A team sees one safe power pair right now, rejects it, deliberately lets a different pulse strike the hull, and collaborates on a riskier future collision that feeds a critically empty lane. Mistakes are legible because the state is visible and arithmetic deterministic. Success can feel earned, not rolled.

**Target experience:** Short sessions with many simultaneous planning decisions; rules teachable in minutes, decisions requiring multi-beat reasoning. Portrait presentation: three tall lanes, three visible depth bands, capacitors and hull below, next-wave preview above, minimal controls. No art direction or interface implementation is frozen.

**Don't add yet:** permanent upgrades, character classes, items, asynchronous player action resolution, arbitrary abilities, monetization, enemy AI, story, tech trees, or visual effects. Every added mechanic must answer a demonstrated need.

## 6. What is frozen and what remains open

### Frozen for Phase 6 engine specification

- Three lanes × three time bands; nine rounds; 7 initial hull; lane capacitor cap 3 and target `>=2` each plus `>=8` total.
- Charge fields and seeded reproducibility; seven spawning rounds, 18 incoming charges in the experimental generator.
- Three verbs, costs, one-edit-per-token, four shared edit budget, and once-in-lifetime HOLD.
- Simultaneous breach rule `min(P,N)` energy + `abs(P−N)` damage.
- Mandatory final leakage of unresolved charges (fixes a verified exploit).
- Team-owned joint plan and authoritative deterministic resolution.

### Deliberately **not** frozen

- The exact random-wave distribution beyond the early verified content bank, long-term difficulty curve, and full procedural generator.
- Four-player authorship and engagement solutions.
- Choice of timers, matchmaking, reconnection policy, or technology stack.
- Long-term content progression, alternate mission goals, and rule variants.
- The eventual need for DAMP: it's a useful emergency action in examples, but its aggregate strategic necessity remains uncertain.
- Any claim of fun, novelty absolute, fairness, session length, or human-suitable difficulty.

### Phase 6 acceptance gates before real online buildout

1. **Explainability:** A human can predict at least three of four illustrated outcomes after a brief rules explanation (hypothesis, not yet run).
2. **4-player agency:** In facilitated four-player rounds, all participants regularly contribute a meaningful choice, not just a PASS. If not, restructure the action economy and re-test **before** full network implementation.
3. **Scenario fairness:** Only expose levels with an executable winning witness; preserve witness verification in CI. Never treat balanced polarity count as sufficient.
4. **Planning depth:** Curate multiple states in which an immediate benefit conflicts with multi-turn gains; include examples where HOLD is *wrong* as well as essential. Avoid creating a universal HOLD-everything policy.
5. **Simplicity:** No fourth verb without evidence that it creates a new kind of decision rather than redundant complexity.
6. **Traceability:** The implementation must reproduce the same outcomes as the v0.1 reference tests and verified seed bank.

If these gates fail, **change the mechanics and revisit the decision**, not just the UI. Phase 5 selects the best current design for disciplined iteration, not a sunk-cost obligation.

## 7. What comes next (Phases 6–9)

**Phase 6 — Formal rules and architecture.** Express the frozen v0.1 as a transport-independent state machine and typed game commands, including strict validation, provenance of seeds and witness traces, server ownership rules and reconnect semantics. Run early co-op involvement experiments before finalizing action authorship. Solve conflicts between public preview, arrivals, and lock order.

**Phase 7 — Build the real engine.** Implement authoritative TypeScript/Node core, tests, deterministic RNG, a CLI harness, and eventually the lightweight online room server. No polished UI. Sync only the joint plan and resulting authoritative state, with idempotency and replay.

**Phase 8 — Validate and challenge.** Simulation search, proven-playable generated levels, fairness by difficulty, action ablations, strategy diversity, edge cases, player-count participation and human co-op sessions. Revise the engine if the gates show structural flaws.

**Phase 9 — Handoff.** Deliver repo commits, rules, example transcripts, automated results, known gaps, and a well-scoped next iteration roadmap; defer UI and full polish until the mechanics earn it.

## 8. Files and repository status

- `charge_loom_v01.py`: executable v0.1 reference rules with final-leakage correction.
- `tests_v01.py`: self-contained mechanical test and winning-witness verification suite.
- `verified-scenario-bank.json`: seven complete replayable winning sessions.
- `phase5-test-results.json`: scenario enumeration and development-seed policy comparison.
- `holdout-results.json`: additional independent-seed policy comparison.
- `play_cli_v01.py`: simple terminal runner.
- `README.md`: getting started and scope.

Target repository: `~/Desktop/gaim`, branch `main`. That path is **not mounted** in this session, so no local or GitHub commit was performed. These are transfer-ready files, not a claim of a published implementation.
