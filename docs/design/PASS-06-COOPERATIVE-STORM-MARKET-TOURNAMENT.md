# GAIM / Mechanics pass 06 — Who Chooses the Storm?

**Status:** Independent research. No production game rules or online-room protocol changes.  
**Recommended next candidate:** Storm Market layered over Bridge + Flip + Accelerate.  
**Evidence level:** Mechanically verified interactions and two small paired seeded test sets; no human playtests.

## Research question

Past passes added and tuned actions. But they left the fundamental input stream of problems fixed: players could modify tokens *after* their arrival, not choose the sequence of challenges. This pass deliberately borrows board-game mechanisms from **open drafting**, **action-selection hands**, **resource conversion**, and **asymmetric activation costs** to test bigger structural changes.

The strongest candidates were evaluated against the *same* open-action research game: Shift, Hold, Damp, Bridge, Flip, and Accelerate, four total shared edits per round, nine rounds, three capped capacitors, same hull/coolant and storm seeds. For context, the production shipping v0.1 remains unchanged and more limited than this research control.

## Tournament entries: precise rules

### A — Control: open commands (Bridge + Flip + Accelerate)

Each round, players see all legal uses of Shift, Hold, Damp, Bridge, Flip, and Accelerate. They may submit up to four mutually compatible edits. The next normal wave arrives from the seeded deck. No additional decisions. This is the baseline for our tournament; it is **not** the current shipping v0.1.

### B — Storm Market: two eligible waves, one queued preview

At the start of rounds **1–7**, reveal two storm cards that contain exact incoming signed charges. Also show the *next card in the queue* as a forecast. The team chooses one of the two eligible cards to arrive this round. The unchosen card stays eligible; the next queued card becomes eligible for the following round. Every storm card must enter exactly once by the end of round 7. Rounds 8 and 9 get no new cards. Nothing is discarded and no charges are created by the draft. Choosing a card costs **no one of the four shared edits** in this trial. Reordering affects which charges can meet in both position and time.

The three-card forecast is **public** in both market and nonmarket comparison games for a fair two-round information window. Any later cards must remain hidden from a player-facing implementation. `public_forecast()` exposes the intended contract; it does not claim to be a security boundary in the Python lab.

**Interaction example (exact test):** Start at (3,1,3) capacitor energy, with +1 already traveling in Center. Two wave cards are queued, an unmatched +1 Left and a matching −1 Center. Playing the old Left card first finishes as `loss: target` (3,1,3); choosing the newer Center card first finishes as `win` (3,2,3). Both cards ultimately arrive. The difference is their *meeting time*.

**Risk:** A free public choice can make the game easier without deepening it. Three cards visible above an already dense portrait board may tax readability. It also creates a new group decision, not yet genuine independent player agency.

### C — Paid Storm Market: draft as a worker-placement sacrifice

Same two offers and public next preview, except choosing **the newer card** consumes one of four shared edits. Choosing the oldest is free. This models the opportunity cost of deviating from the default storm schedule: use three edits instead of four. In a verified crisis with four required Shifts, the free-market team avoids a lethal breach, while the paid-market team cannot both reorder and perform all four. Yet in seeded games, many edits are unused, so the fee is often inconsequential.

**Risk:** If teams frequently have idle edits, the fee looks significant in the rulebook but rarely matters. It does not automatically outperform the simpler free choice.

### D — Operator Menus: co-op action drafting

The team has four virtual consoles each round, irrespective of player count. Every console shows two action types; it can submit at most one edit of either type. A rotating deterministic arrangement uses these pairs: Shift/Hold, Shift/Damp, Flip/Accelerate, Bridge/Hold. Menus rotate round by round. For 1–4 humans, the four consoles are distributed in a rotating round-robin; a solo player operates all four. All action choices and menus are public. Passing remains legal. Neither slot count nor energy budget changes with player count.

**Finding:** While ownership mechanically matters, the menus do not solve quarterbacking: one person can still tell other players what to do. The constraints reduce strategic freedom and do not reliably increase player activity. Reject as a core rule.

### E — Storm Market + Operator Menus

Combine B and D. Result: not a synergistic co-op improvement. The action-menu restriction erases much of the strategic gain from choosing storm timing. Reject.

### F — Recycle: stored power for coolant

Once per round, spend one stored energy from a chosen lane and one edit to regain one coolant, up to the normal cap of three. This can protect the hull later through Damp, but it can also pull a lane below the victory requirement. It creates a genuine spend-or-save choice in exact examples, but in full seeded heuristics the planner rarely needed it. Retain only as a small experimental idea, not a new standard rule.

### G — Regulator: extra coolant cost on large Flips

Flipping a strength-two-or-greater charge also consumes one coolant. This is an attempted counterbalance to large Flip rescues. It has a measurable effect on some games but adds an exception and did not demonstrate improvement. Reject for now.

### H — Paid Market + Recycle

A multi-system hybrid. It adds two rules, but seeded gameplay did not demonstrate proportional strategic benefit. Reject.

## Testing methodology and limitations

- Engines and fixtures: `experiments/phase06_lab.py` and `tests/test_phase06_lab.py`. The original production engine is not imported by the multiplayer code from these experiments.
- Paired seeded games use the same storm seeds within each set, the same simple sequential greedy action selector, and the same two-round lookahead. This selector **is not optimal**. It has a hand-written utility function and does not represent human planning.
- Three incoming storm cards are assumed public for the two-round comparison, so the lookahead does not need to rely on a secret forecast. Later cards remain unknowable by the intended player rule, even though the reference simulator necessarily stores the full deck.
- Different generated state trajectories after round 1 mean the plans aren't paired move-for-move. Wins measure one particular policy's behavior, not relative difficulty, replay value, cognitive load, or fun.
- The one-round negative control shows why comparing Storm Market with a one-step planner is invalid: it never chooses the newer wave.
- Neither game is tested with real players. No benchmark proves that four players have equally satisfying contributions.

### Paired experimental results

| Variant | Two-step set A (24 seeds, 9000–9023) | Two-step set B (12 seeds, 9300–9311) |
|---|---:|---:|
| Open-action control | 14 / 24 wins | 7 / 12 wins |
| Free Storm Market | **20 / 24** | **9 / 12** |
| Paid Storm Market | not run in set A | 9 / 12 |
| Operator menus | 10 / 24 | 6 / 12 |
| Market + operator menus | 12 / 24 | 8 / 12 |
| Recycle only | 14 / 24 | 7 / 12 |
| Regulator only | 13 / 24 | 6 / 12 |
| Market + recycle | 20 / 24 | 9 / 12 |
| Paid market + recycle | not run in set A | 9 / 12 |

The free market used the **second offered storm** 35 times in set A and 21 times in set B, so it was not just reproducing the original order. On 12 seeds using a *one-round* greedy strategy, open and market both won 7 / 12, with no newer-storm choices—an intentional negative control.

Even the improved 20/24 result could simply reflect having more opportunities to avoid losses. Do not call it "80% fun" or an estimate of human success. See `pass06-results.json` for detailed counts and action usage.

### Verified counterexamples

1. **Storm timing matters.** A two-offer game starting at 3–1–3 can win by advancing the matching −1 storm; accepting the default first offer loses, although both arrive eventually (`test_selected_newer_storm_changes_win_from_loss_to_victory`).
2. **Paid draft really spends time.** Four charges require four separate Shifts to avoid a lethal leak. Choosing the newer wave leaves capacity for only three, and every three-Shift omission is fatal (`test_paid_market_cannot_replace_a_necessary_fourth_edit`).
3. **Consoles allow complementary shifts** when separate consoles have Shift, but they also forbid otherwise legal actions; there is no demonstrated benefit in reducing the team action space.
4. **Recycle can be a trap.** In a 3–2–3 endgame, spending Center energy for coolant reduces the target from a win to a loss.
5. **A stricter large-charge Flip** consumes coolant, but the complexity is not justified by the results.
6. A complete seeded two-step policy replay is saved in `pass06-replay-witness.json`: in seed 9001 the control fails with a breach, while the two-offer-market policy wins. This is policy evidence, **not** a proof the original game is unwinnable.

## Design decision

### Select: **Charge Loom — Forecast Market** (working research v0.5)

Use Bridge + Flip + Accelerate on the normal 3×3 time/lane board, retain the standard four shared edits, and introduce the **two-offer / one-preview storm market** for rounds 1–7. The team makes its free choice before submitting token edits. The unused card stays in the queue; all seven cards arrive. Existing Shift/Hold/Damp/Bridge/Flip/Accelerate costs otherwise remain as in the Pass 5 experimental rules.

This version wins the prototype research slot because it adds an **upstream strategic decision about how to sequence threats** rather than adding another tactical rescue button. It is a more promising source of variable game plans, and the two-step experiments actually used the market. It is *not* justified as production-ready or proven co-op.

### Do NOT select

- **Operator menus:** reduce success and restrict legitimate actions, without solving quarterbacking.
- **Market + operators:** added complexity and much smaller improvement over control.
- **Recycle:** usefully tests spending, but contributes little in the paired full-game benchmark.
- **Regulator:** another exception to remember for weak demonstrated benefit.
- **Paid market:** clear cost in an exact tactical witness, but negligible impact in typical heuristic games where action slots are often unspent. Keep as a cost hypothesis, not an adopted rule.

### Critical unresolved requirements

1. **Four-player agency:** Redesign through shared-but-conflicting responsibilities, simultaneous commitments or complementary private capabilities—without merely rationing what legal buttons each participant may press. We have *not* found that solution.
2. **Scenario fairness:** Limit test agents to the exact public three-card forecast; run information-set planners with uncertainty over the remaining deck, not omniscient searches of all seeded future arrivals.
3. **Replayability:** Develop mission goals whose optimal plans genuinely differ and validate many varied storm decks, not simply permute seven familiar cards.
4. **Depth vs overload:** We now have six action verbs plus a draft choice. A rules-pruning tournament must demonstrate that all six are valuable; otherwise remove the redundant one.
5. **Cost choice:** Revisit whether Storm Market should be free, consume an edit, or have a resource cost only after increasing the meaningful scarcity of action opportunities.
6. **Player feedback:** Obtain direct 1-, 2-, 3-, and 4-player human trial observations; solver wins alone can't answer the main product question.

## Reproduce

From the repository root after installing this hotfix:

```bash
python3 -m unittest tests.test_phase06_lab -v
python3 -m experiments.phase06_survey --games 12 --draft-cases 100 --lookahead 2
bash scripts/release_gate.sh
```

The first two commands reproduce targeted mechanics and a seeded survey. The third is the **complete existing Phase 5–7 release gate**, which also tests the original Python rules, TypeScript parity and network multiplayer. It does not replace human playtesting.
