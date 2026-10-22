# Phase 6 — Charge Loom v0.1 engine contract

**Status:** IMPLEMENTATION-READY DESIGN; NOT A PRODUCTION ENGINE. 2026-10-21.  
**Authority:** `docs/design/PHASE-05-DECISION-AND-V01-RULES.md` and the frozen `reference/charge_loom_v01.py`; where prose is ambiguous, this document makes the intended implementation explicit without silently changing the frozen rules.  
**Branch:** `main`. **No graphical interface in this phase.**

## 1. Nonnegotiable invariants

| Area | Required value or behavior |
|---|---|
| Board | 3 lanes `0..2`; 3 bands `0 NOW, 1 SOON, 2 FAR`; no occupancy limit; all charge interactions occur only at breach |
| Start | Completed round `0`, hull `7`, capacitors `[0,0,0]`, coolant `3`, empty board, next token ID `1` |
| Storm | Exactly 18 arrivals on rounds 1–7 with wave sizes `[3,2,3,2,3,2,3]`; rounds 8–9 spawn none |
| Charge | Unique positive integer ID, lane `0..2`, band `0..2`, sign `+1/-1`, magnitude `1..3`, held flag `0/1` |
| Edits | At most **four team-wide**, one per token per round; zero edits permitted; `PASS` is represented by an unfilled slot |
| SHIFT | Move one lane `-1/+1`, no wrap, consumes one slot |
| HOLD | Only if never held; stay in band this round; magnitude `min(3, m+1)`; mark permanently held |
| DAMP | Spend one of initial three coolant; magnitude `m-1`, delete at zero |
| Tick | All non-HOLDed tokens shift band `-1`; band `<0` breaches; stationary held charges remain aboard |
| Breach | In each lane sum positive `P` and negative `N`. Gain `min(P,N)` capacitor (capped at 3). Lose `abs(P-N)` hull. Remove all breached charges. No cross-lane or cross-band cancellation |
| Final | **After** normal round-nine breaches, each still-on-board charge leaks its **entire magnitude** as hull damage; all removed, no extra energy |
| Loss | Hull `<=0` immediately; otherwise round nine fails if any capacitor `<2` or sum `<8` |
| Win | End round nine with hull `>0`, each capacitor `>=2`, sum `>=8` |

**The full collision rule uses signed *totals*, not pairwise token matching.** Example: `+2,+1,-2` breaches produce `min(3,2)=2` power and `1` damage. A full capacitor still neutralizes the positive and negative strengths, but wastes excess power.

**HOLD on a magnitude-3 charge is legal.** It still spends the once-per-lifetime HOLD and skips movement but doesn't increase strength further. This is inherited from v0.1.

**Hull is permitted to become negative** after a lethal breach; the reference does not clamp it to zero. Exact parity requires retaining the signed result. A terminal game never advances again.

## 2. Authoritative state model

The authoritative engine state is immutable for each transition:

```text
CompletedGameState {
  ruleset: "charge-loom/v0.1";
  completedRound: integer 0..9;
  hull: signed integer;
  capacitors: [integer 0..3, integer 0..3, integer 0..3];
  coolant: integer 0..3;
  charges: Charge[];
  nextTokenId: positive integer;
  scenarioId: identifier for an immutable explicit seven-wave scenario;
  outcome: null | "win" | "loss: breach" | "loss: target";
}
Charge { id, lane, band, polarity, strength, alreadyHeld }
```

`completedRound` is the last **resolved** round, not the one currently planned. The server constructs a read-only `PlanningView(completedState)` for round `completedRound + 1` by adding that round's arrivals at FAR and assigning their IDs from `nextTokenId`. This projection **does not modify** the stored state, spend coolant, or advance the clock. It includes all arriving charges as selectable/editable. The next wave is a public preview but has **no token IDs** and cannot be edited yet. Hidden subsequent waves and the original seed must not be sent to clients.

Phase 7 should use an explicit `scenario.waves` data object for engine execution; do not port Python `random.Random` and assume it is TypeScript-compatible. `contracts/scenarios.v0.1.json` contains seven **fully specified** immutable wave schedules, derived and locked from the Phase 5 reference. Each schedule is accompanied by a replay witness and complete golden state snapshots in `contracts/golden-traces.v0.1.json`.

The Python `seed` is **legacy/reference metadata**, never part of a player's view. Selection by `scenarioId` is sufficient for the production engine. Future procedurally generated content must be versioned separately, proof-checked, and must not silently change v0.1 witnesses. IDs are assigned sequentially by spawn order; do not reuse removed IDs.

## 3. Complete state-transition algorithm

The next game-state reducer **must** be a pure function of `(state, scenario, orderedJointPlan)`; it must never read the network, wall clock, player identity, or unseeded randomness.

```text
resolveRound(state, scenario, jointPlan):
  assert state.outcome == null and completedRound < 9
  r = completedRound + 1
  workingTokens = clone(state.charges)
  spawn scenario.waves[r-1] at band 2 in source order (if r <= 7)
  assign fresh IDs incrementally
  validate entire plan against post-spawn tokens:
      0 <= edits.length <= 4
      each token ID occurs no more than once
      all target IDs exist
      legal shift destinations, no second lifetime hold
      coolant suffices for number of DAMP edits
  if invalid, reject atomically; DO NOT advance game or consume resources
  apply legal edits in joint slot order (independent tokens => commutative)
  immediately delete 0-strength tokens
  move each token not held this round down one band
  collect band < 0 as breach; retain other tokens
  simultaneously, for each lane:
      P = sum of breached positive magnitudes
      N = sum of breached negative magnitudes
      capacitor[lane] = min(3, capacitor[lane] + min(P,N))
      hull -= abs(P-N)
  if r == 9:
      hull -= sum of all remaining token magnitudes
      remove all remaining tokens
  if hull <= 0: outcome = "loss: breach"
  else if r == 9:
      outcome = "win" if min(capacitors)>=2 and sum(capacitors)>=8
                else "loss: target"
  else: outcome = null
  return completedRound=r, updated state, outcome
```

The reducer does not need a separate pairwise match algorithm. In particular, tokens entering a cell together **do not** cancel early; cancellation happens only after the band's final descent past NOW. At round nine, tokens retained at different bands never neutralize during final leakage.

The following operations are invalid even if a permissive language might silently coerce them: a boolean token ID, decimal direction, duplicate token edit, unknown verb, extra fields, negative coolant, second HOLD, out-of-bounds SHIFT, edit on a charge that arrives **next** round, submitting to a terminal state.

All fields of an authoritative message must be integers where specified (not floating-point numeric equivalents). Use structural validation, bounded payload sizes, and typed errors at the server boundary.

## 4. Worked deterministic checks (specification, not speculation)

### Cooperative collision (round 8)

Start from `completedRound=7`, hull `5`, capacitors `[2,2,1]`, charges `(+1, lane0, NOW, id1)` and `(-1, lane2, NOW, id2)`.

- No edits: both leak; hull becomes `3`, capacitors unchanged.
- SHIFT only `id1` into CENTER: hull `3`, unchanged capacitors.
- SHIFT only `id2` into CENTER: hull `3`, unchanged capacitors.
- Both SHIFTs to CENTER: hull remains `5`, CENTER capacitor becomes `3`.

### Multi-turn sacrifice (rounds 8–9)

Start from `completedRound=7`, hull `3`, capacitors `[3,2,1]`, coolant `1`, charges `(+1, CENTER/NOW, id1)`, `(-1, CENTER/NOW, id2)`, `(-2, RIGHT/SOON, id3)`.

- No edits on either turn: immediate CENTER match then unmatched RIGHT breach => **target loss**.
- HOLD `id1` on round 8 (now a +2), suffer 1 damage; SHIFT `id1` to RIGHT on round 9 where it cancels `-2` => **win**, hull `2`, capacitors `[3,2,3]`.

### No free end-of-game storage

On the ninth round, holding a NOW +3 still leaves it on the board, so cleanup drains 3 hull. The game cannot be won by hiding danger past the deadline.

All three are automated tests in the frozen Python reference and the Phase 6 contract suite.

## 5. Conformance contract for the Phase 7 TypeScript engine

`contracts/scenarios.v0.1.json` is the input set. `contracts/golden-traces.v0.1.json` is an **independently generated** target from Phase 5's Python reference. It provides the public-view state after initial construction and after every action list in every winning witness.

For every trace, replay the actions against the corresponding explicit scenario and compare **all** fields in each expected view: round counters, capacitors, hull, coolant, remaining tokens, their IDs and holds, previews, outcomes, and slot assignment. For each game action, also compare behavior of invalid inputs and errors semantically.

The sample golden views set playerCount=4, but gameplay is independent of player count. Separately test slot ownership for 1, 2, 3, and 4 players. The system must not 'pass' a conformance run just because one replay wins; **state-by-state exact equality is required**.

Versioning rules:

- Gameplay rules: `charge-loom/v0.1`; do not change these silently.
- Wire protocol: integer `protocolVersion=1`; breaking change requires a new protocol version.
- Scenario content: stable `scenarioId` and immutable wave sequence; changing it is a **new ID**.
- Serialized state: no client-owned canonical game state and no unknown authoritative properties.
- All server transcript logs use an ordered `revision`/round index; a replay must have no skipped, reordered, or double-applied round transitions.

## 6. Release gate (this phase)

From the repository root, `bash scripts/release_gate.sh` runs with Python 3.10+ and no external packages:

1. Compile-check Python reference, Phase 6 adapter, and validation tests.
2. Execute the **unchanged** Phase 5 core tests, including all seven winning witnesses.
3. Execute Phase 6 contract tests for slot assignment, combined plan validation, complementary shifts, public-view privacy, and golden replay.
4. Verify both generated content files match the authoritative reference exactly (regeneration in `--check` mode).
5. Shell syntax-check the release script and run Git whitespace checks when inside a repository.

Phase 7 must **extend the same gate**, never replace or skip it, adding TypeScript typecheck, engine tests, cross-language golden conformance, and network-room tests. This phase does not yet claim a production engine or deployed online co-op game.

## 7. Deliberately unresolved and exit criteria

**Not frozen:** difficulty, content generation, human engagement, need for DAMP, timers beyond provisional operational plan, ranked matchmaking, permanence across a server crash, authentication provider, or commercial platform integration.

**Decision gate to begin deep server build:** Run actual 1-, 2-, 3-, and 4-player sessions (the CLI may be used) and measure individual influence, coordination, total edits, and pass frequency. If the four-player experience is weak, revise the authorship protocol or mechanics **before** expensive multiplayer work. Python traces establish correctness, not fun.

See `PHASE-06-COOP-ROOM-AND-ACCEPTANCE.md` for the room protocol, first draft of slot ownership, concurrency, disconnect policy, and exact experiment design.
