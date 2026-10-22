# GAIM mechanics development — Pass 04: changing the shape of the puzzle

**Status:** Completed opt-in research pass. **Shipping Charge Loom v0.1, TypeScript engine, golden traces and live multiplayer contracts are unchanged.** The provisional research front-runner is **Delayed Bridge + Polarity Flip**, not a production rules promotion. New experiments can be played from a terminal.

## Design brief and standard of evidence

We deliberately challenged the Pass 03 winner (Delayed Bridge). A viable addition must create *multiple defensible decisions* and complementary action combinations, not simply raise win rates. We care about consequences that are explainable to a new player, meaningful power expenditure, a distinct tactical purpose for each verb, and low rules burden on a portrait smartphone.

We compared the same basic 3-lane / 3-time-band / nine-round setup with eight experimental configurations. The source `experiments/phase04_lab.py` is a deterministic headless reducer independent of the TypeScript production engine. All variants preserve the v0.1 charge resolution, caps, hull damage, and objective. This limits confounding changes, but **does not solve the fixed objective or multiplayer quarterbacking problem**.

The research was informed by familiar board-game structures: investment/engine-building, multi-use resource spending, component manipulation, and tactical action selection. Reference: [BoardGameGeek mechanics catalogue](https://boardgamegeek.com/wiki/page/mechanic). Borrow the decision structures, not the games' themes or branding.

## The new mechanical contenders: exact rules

All actions below count as one of the four team edits and obey the existing session duration, arrival order, and victory threshold. Unless otherwise stated, only one edit per existing or newly arriving charge can occur in the same planning round. Spending uses **previously stored** capacitor power, never energy from this round's unresolved collision.

### A. SPLIT — conserved strength, more locations

Select a charge of strength **2 or 3**, and an adjacent lane. Detach **one unit** of its strength into a new same-polarity charge in the adjacent lane, with the **same time band**. The original charge loses one strength. Total charge strength is conserved; this does not generate free energy. The detached unit is marked *already held* so the player cannot keep amplifying a chain of new pieces for free. Both pieces advance normally this round. It consumes one edit.

This converts a spatial choice into an allocation choice: a +2 might be more valuable as two +1s if two separate lanes need matches. It can also be disastrous: by separating a perfectly matched pair, both resulting unmatched portions may damage the hull. **A verified win witness and a verified disastrous counterexample are in the tests.**

### B. FLIP — stored power manipulates polarity

Select any visible charge in a lane with at least one previously stored power. **Spend one power from that charge's lane**, reverse its polarity, leave strength and position unchanged. This counts as one edit to that charge. No other same-charge edit is allowed that round.

It can rescue a board with a severe polarity imbalance; using it reduces a capacitor needed for victory. It directly competes for the *same stored resource* as a Delayed Bridge. Critically, it cannot be used in an empty lane capacitor: energy must first be earned before the team gets tactical flexibility. A poor flip can turn matched energy into *two damaging leaks*.

### C. TRANSFER — emergency power conversion

Spend **two stored power** in one capacitor to add **one power** to an adjacent capacitor (capped at three). One infrastructure edit per round. This salvages otherwise-wasted collision production but is intentionally inefficient. It risks collapsing the spatial objective into a simpler bookkeeping step rather than creating new patterns of charge movement.

### D. RESONATOR — high-threshold engine building

Spend one power and one edit in a source lane to connect an adjacent destination. The link starts **next round** and lasts two resolution rounds. Each round where the source actually matches **at least two charge strength**, the destination receives **two bonus power**, capped at three. No trigger for a strength-one collision. Only one such installation may be active. Compare with Bridge, which pays **one destination power per round containing any source match**, regardless of match size.

Resonator makes HOLD amplification and synchronized big hits particularly valuable. The risk is being too specialized: common small matches pay nothing.

### E. BRIDGE + SPLIT

Combine the Pass 03 Delayed Bridge investment with SPLIT. Both verbs are independent; splitting can create a future source match while also powering another lane. This is an intuitive action-composition idea with a verified three-round combination.

### F. BRIDGE + FLIP

Combine Delayed Bridge with FLIP. Both consume already-earned power from their source lane. Bridge asks whether to buy *future* production, while Flip pays to secure or redirect an *immediate* collision. They can cooperate in successive rounds; or compete for the last unit of power in a capacitor. One additional verb adds a genuine economic alternative rather than another free movement option.

### Controls

- **Unchanged v0.1:** SHIFT / HOLD / DAMP only.
- **Delayed Bridge alone:** the Pass 03 investment rule, starts next round and pays one bonus destination power on source matches over two rounds.

No experimental action affects the online game. All variants are selectable in the CLI for comparison.

## Verified tactical cases (not descriptions alone)

**SPLIT indispensable in a one-round allocation:** Just before the final breach: capacitors `(2,1,3)`; a `+2` and `-1` in Left, plus a `-1` in Center. Split one unit of `+2` from Left into Center. Both lanes now match one; capacitors become `(3,2,3)`, hull unscathed, **win**. Passing cannot fill Center; moving the whole +2 cannot produce two lane matches. This explicitly tests why preserving *total* strength matters.

**SPLIT can be lethal:** With one hull and capacitors `(2,3,3)`, matching `+2/-2` in Left is a safe win. Split the `+2` into Left +1 and Center +1. Two leaks deal two damage; **loss**.

**BRIDGE + SPLIT three-beat combo:** Begin after round 6 with capacitors `(2,2,0)` and full hull. In Left, the SOON band has `+2,-1`; Center SOON has `-1`; Center FAR has a `+1,-1` pair. Round 7: buy Center → Right Bridge, reducing Center from 2 to 1. Round 8: split one unit of Left +2 into Center. Both lanes match one and the Bridge pays Right +1. Round 9: the later Center pair matches and the Bridge pays Right again. Final **(3,3,2), 7 hull, win**. Removing either the purchase or split from the stated script loses. Stronger counterfactual: with the purchase fixed and no round-9 edits, the enumerator found **0 winning round-8 plans without SPLIT versus 2 with SPLIT**, after checking 1,419 and 1,727 legal plans respectively.

**FLIP as real spending:** With `(1,3,3)` and two `+2` charges in Left at the deadline, spend the one Left power to flip one charge to `-2`. The match earns two power, for final `(2,3,3)`: **win**. Without a flip there is no match and the target fails. With `(2,3,3)` and an already perfectly balanced `+2/-2` in Left, the wrong flip removes the match and can cause **hull death** instead.

**BRIDGE + FLIP three-beat combo:** Begin after round 6 with capacitors `(3,2,0)`. Center SOON holds `+2,+2`; Center FAR holds `+1,-1`. Round 7: buy Center → Right Bridge, leaving Center at 1. Round 8: spend that last Center power to flip one `+2` to `-2`; the resulting strength-two collision makes power and triggers the Bridge. Round 9: the second, smaller Center collision triggers the Bridge again. Final **(3,3,2), 7 hull, win**. In the same scripted sequence, **Bridge without Flip fails**, and **Flip without Bridge fails**. Important limitation: this is not a proof that all alternative action scripts fail; it demonstrates a genuine complementary interaction.

**Resonator's narrower payoff:** With `(3,2,0)` and only one future strength-two Center pair, Resonator can invest one Center power and later place two bonus in Right. Bridge would place only one. But Resonator fails to pay on single-strength source matches where Bridge would benefit. Neither purchase is universally correct.

## Reproducible tournament results

All recorded machine-readable results are in `docs/design/pass04-results.json`. No sample result is a player satisfaction score.

### Test 1 — Independent paired final-round decision boards

We generated two independent sets of **120 synthetic final-round states each** (seeds 4606 and 5716), randomly drawing 3–4 NOW charges, signs, strengths, hull, coolant and capped capacitors. The same board is tested under every rule. Every legal *one-edit-per-token* choice, up to four edits, and the allowed special action are enumerated. These are **not naturally occurring states from the scenario generator**. Passive Bridge purchases are not counted as a last-round advantage because they cannot activate before the game ends.

| Rules | Development solvable / 120 | Holdout solvable / 120 | Combined / 240 |
|---|---:|---:|---:|
| Unchanged v0.1 | 18 | 22 | **40** |
| SPLIT | 19 | 24 | 43 |
| FLIP | 19 | 26 | **45** |
| TRANSFER | 18 | 23 | 41 |
| BRIDGE + SPLIT | 19 | 24 | 43 |
| BRIDGE + FLIP | 19 | 26 | 45 |

All new verbs are optional, so they cannot remove the baseline's legal winning plans here. **Extra rescues are not the same as better strategic decisions.** The one-round experiments properly do not discriminate Bridge vs Bridge + another option in the finale.

### Test 2 — Two-round investment, no future hidden waves

In **1,152 reproducible fixed three-beat states** (four adjacent directed links × zero/one/two source matches × pair strength one/two × eligible stored-power configurations), make an investment in round 7 and compare with passing, then perform no further edits through round 9. Players have no hidden arrivals in these fixtures. Note: the experiment design purposely supplies collision opportunities and does not measure their frequency in real games.

| Investment | A loss becomes a win | A win becomes a loss | No win/loss change |
|---|---:|---:|---:|
| Delayed Bridge | **108** | **40** | 1,004 |
| Resonator | 96 | 48 | 1,008 |

Bridge has the better simple-vs-large match robustness and lower memory burden; retain it. These counts are **paired investment decisions**, not head-to-head agent game outcomes.

### Test 3 — One-step automated policies over 80 identical full-game seeds

One-step greedy policy: repeat the currently best immediate-scoring legal edit until no further single edit improves the round, then resolve. All rules face the same 80 wavebook seeds, with no peeking beyond the current round's publicly spawning wave.

| Rules | Wins / 80 | Survived / 80 | Observation |
|---|---:|---:|---|
| Unchanged v0.1 | **17** | 19 | Baseline |
| Delayed Bridge | 17 | 19 | Zero purchases by myopic bot |
| SPLIT | 17 | 19 | 18 splits, no win-rate increase |
| FLIP | **29** | **41** | 58 flips chosen |
| TRANSFER | 19 | 19 | Two extra wins, no broad survival effect |
| Resonator | 17 | 19 | No purchases by myopic bot |
| Bridge + Split | 17 | 19 | Same myopic result as Split |
| Bridge + Flip | **29** | **41** | Same myopic result as Flip |

**The greedy policy cannot properly value delayed investments.** Its refusal to buy Bridge or Resonator is a policy limitation, not evidence that delayed investment is useless. The Flip improvement is more relevant because Flip pays out immediately. **Higher win count alone is not proof of a better game**; it may simply reduce difficulty.

### Test 4 — Is FLIP an almost-always-correct purchase?

In the same greedy-policy 80-seed trajectory, assess all individually legal FLIP actions relative to passing using the existing one-step score. Of **1,635 candidate flips**: **173 improve** immediate score, **551 are neutral**, and **911 make it worse**. In 343 rounds with any flip option, 40 offer both immediately favorable and unfavorable targets; only five have every flip option favorable. The probe measures a particular, explicitly chosen heuristic's score, **not an objective human utility function**.

As a separate stress policy, unconditionally flipping the *first* legal token each round (with greedy supporting edits) wins **0/80**; the selective heuristic wins **29/80**. That reckless policy is intentionally bad, and not a credible experienced player, but decisively refutes the naive assertion that any legal FLIP is automatically desirable.

## Critical rules and design risks

1. **Power-flip economy:** FLIP is very strong because it changes polarity *and* can neutralize up to four points of potential breach. One stored-power cost may be underpriced; test 1 vs 2 energy and/or limited uses, but do not price it arbitrarily without evidence.
2. **Bridge frequency:** The one-step bot never invests. Real bridge opportunities must be common enough to matter, and need a forecast-respecting two- or three-step planning agent plus human play sessions.
3. **Combinatorial player workload:** BRIDGE + FLIP adds more options but does not magically solve 1–4-player engagement. Open information still allows quarterbacking. Model distributed agency in the next pass, not forced filler moves.
4. **Replayability:** This pass leaves wave generation, fixed target `(3,3,2)`-style constraint and 7 verified scenarios untouched. The game is **not endlessly replayable**.
5. **Failure fairness:** Old witness solutions are valid and cross-language parity is preserved, but no claim has been made that random waves are solvable with the player's actual information.
6. **Tempo:** Full nine-round challenge frequency and phase-based dramatic arc still need redesign.
7. **Rule complexity:** Every new action must earn its presence. SPLIT creates novel spatial allocation but gave few additional solvable endgames and no extra myopic full-game wins; keep it as a reserve until broader or human experiments show frequent interesting use.

## Explicit provisional verdict

**Select BRIDGE + FLIP as the Pass 04 *research leader*, not as shipped rules.** It retains delayed investment and introduces a strategically different short-term power sink. An investment can enable a future collision; a flip can compete with that investment or enable it. The combination was verified in exact three-round play. FLIP meaningfully changes complete seeded outcomes but is not a trivial always-use action under the measured heuristic. Its rules are only one verb larger than Pass 03 Bridge.

**Second place: Delayed Bridge alone**, if FLIP proves too powerful or causes same-polarity storms to become harmless once energy is available. **Third: Bridge + Split**, which has elegant strength-conservation and a stronger spatial example but low frequency in measured scenarios. Reject current direct TRANSFER as too much abstraction of the existing lane puzzle; reject RESONATOR as more bookkeeping for a rarer payoff. Do not indiscriminately combine every new rule.

Not an assertion of objective player fun. The design ordering is a reasoned choice under our tests and constraints, with an explicit falsification plan. Production remains v0.1. A release-worthy v0.3 would require a versioned contract, TypeScript parity, multiplayer validation and new golden traces, and must not silently overwrite v0.1.

### Next research pass: try to disprove this winner

- Model an **information-limited two- or three-round planner** for Bridge + Flip and compare with deliberate saving, greedy flipping and reliable-investment policies. Log how often power is scarce enough for Bridge and Flip to compete.
- Vary FLIP cost (1, 2, coolant, restricted token sizes) using shared scenarios and measure both win effects and *strategy diversity*, not just solvability.
- Compare **cooperative choice architectures**: private two-option intervention hands, rotating decision authority, and paired proposals. Measure real agency, talk time and ability to veto an obvious strategy in human 2–4-player sessions.
- Design **variable missions** with different win objectives; test whether they create distinct strategies or merely change thresholds. Establish limited-information solvability of generated storms.
- Run three or more human sessions per player count before claiming improvements in enjoyment; track quarterbacking, downtime, reasons for losses and willingness to replay.
- Promote a new rule only if the benefit survives these tests and a true Phase 7–8 multiplayer implementation, not because one engineered sample looks clever.

## Run and reproduce

```bash
# All baseline Python tests, experiments, golden artifact validation,
# TypeScript compile, multiplayer room and server tests:
bash scripts/release_gate.sh

# Run one mode headlessly by hand:
python3 -m experiments.phase04_play --mode bridge_flip --seed 3

# Individual survey regenerators (more expensive than normal CI):
python3 -m experiments.phase04_survey --final-cases 120 --greedy-seeds 80
python3 -m experiments.phase04_flip_probe
```

The deterministic survey helper `final_survey(n, seed)` was run separately with **seeds 4606 and 5716** for the two final-state datasets. Stored reports are authoritative for the exact claimed numbers; the generic CLI accepts one final-state seed if you want another held-out set. The 80-seed greedy sweep and flip-specific counterfactual diagnostics have their own stored outputs.
