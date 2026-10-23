# GAIM — Mechanics Tournament Pass 09: Mission Structure, Forecast Breadth, and Cooperation

**Decision: Keep Forecast Market v0.5 as the leading research ruleset. No new rule earns promotion this pass.**

This investigation addresses two of the project's enduring weaknesses: different sessions should produce genuinely different worthwhile plans, and multiplayer should benefit from coordinated thinking rather than just assigning shared clicks to different users. The current shipping TypeScript/room code remains untouched. All code below is opt-in Python research using the existing Phase 6–8 engine.

## Evaluation standards

A feature only deserves promotion if it creates **understandable new strategic tradeoffs** at a reasonable rules burden. In particular:

- Different win conditions alone are insufficient; they should lead to different **winning actions on the same board**.
- More storm choices can improve success rates while worsening analysis paralysis and portrait usability.
- Pairwise action complementarity is a necessary opportunity for teamwork, **not proof of engaging cooperation**. A solo player can still execute both edits.
- Short-horizon bot results measure the specified bot. They are not game quality, player win rates, or human playtesting.
- The one-, two-, and three-offer comparisons use the same seven storm cards and same four-edit budget. No cards are skipped.

## Mechanics designed and implemented

### A. Mission modules: borrowing scenario objectives from cooperative board games

Choose one *public mission* at game setup; it changes the victory test, not the six available action verbs, storm generator, or nine-round deadline. Candidate objectives:

| Mission | Exact victory condition, after nine rounds | Intended strategic pressure |
|---|---|---|
| **Grid** (control) | Hull > 0, at least 2 energy in every lane, at least 8 total | Concentrated but balanced power production |
| **Fortress** | Hull at least 6, at least 1 energy per lane, at least 6 total | Protect the settlement; accept lower production |
| **Voltage** | Strength-2-or-greater collisions in at least **two distinct lanes** during the game; at least 1 energy per lane, 7 total | Favor amplified collisions and spatial spread |
| **Concord** | At least **two different rounds** with successful collisions in two or more lanes; at least 1 energy per lane, 6 total | Synchronize distributed arrivals |
| **Circuit** | At least **one actual collision in each lane** during the game; at least 1 energy per lane, 7 total | Don't rely solely on a Bridge to power untouched lanes |

A collision counts from *matched incoming positive and negative strength*, even if a capacitor is already full. Bridge bonus power by itself does not count as a collision in its destination. These requirements and state-history bookkeeping are implemented in `experiments/phase09_lab.py`.

Also implemented: reproducible two-mission *public offers* at game setup. **Not promoted:** players would likely just take whichever mission is easier for the revealed forecast, and the current objectives are unequally difficult. Offering missions is not intrinsically better than designing good ones.

### B. One, two, or three storm offers: borrowing variable draft width

Preserve all seven storm cards. Initially offer 1, 2, or 3 in FIFO order. At each of the first seven rounds, select one current card; refill the selection with the next card in the deck. On rounds 8 and 9 there is no new storm. The two-offer version is the current control.

This is a low-rules-overhead test of *decision breadth*. Three options may help a long-range planner but put more visible information and choice burden on a phone. One option removes meaningful storm-order agency. `experiments/phase09_market.py` implements all three, validated not to skip or duplicate cards.

### C. Coordinated plans versus isolated actions: test the current co-op engine before adding roles

Do not impose arbitrary private hands or per-player action restrictions yet. Instead count **strictly complementary legal action pairs** in existing Forecast Market states: neither action individually improves the same-round utility, but combining both does. Such pairs identify opportunities for team communication and compound plays without adding new rules.

The test is conservative about interpretation: these are **not** proven multiplayer-only outcomes, and the numeric utility has heuristic weights. The strict-complement metric cannot reveal quarterbacking, fun, communication costs, or how many of four humans contribute meaningfully. Those require human testing.

## Reproducible evidence

### Mission outcomes and exact action divergence

First exploratory set: 220 independently sampled final-round states with **zero or one edit**. Grid is winnable in 22. Fortress in 6, Voltage in 26, Concord in 26, Circuit in 14. In cases where both Grid and a challenger were winnable, **no challenger required a disjoint set of winning one-edit plans**.

Second, more discriminating holdout: 150 different seeded final-round states, **zero, one, or two edits**, with sampled prior mission history. Grid is winnable in 17; Fortress 11, Voltage 24, Concord 16, Circuit 13. Of the states where both objectives were winnable, just **one** required mutually exclusive winning moves for Concord, and **one** for Circuit. There were **zero** such cases for Fortress and Voltage.

One exact counterexample, included in `pass09-results.json`: with energy `(3,1,3)`, hull 5 and four visible terminal charges, Grid is won by SHIFTing token 1 into Center and token 4 into Center, finishing `(3,2,3)` with 2 hull. Concord is won instead by DAMPing token 3 and FLIPping token 1, finishing `(3,1,3)` with 5 hull and a second synchronized round. These are *genuinely different plans*, just too rare so far.

The sampled history counters are not proven reachable at those exact frequencies in full matches. This experiment establishes mechanical possibility, **not realistic scenario prevalence**.

On 14 full-game development seeds, the per-mission heuristic won Grid 8, Fortress 6, Voltage 10, Concord 4, Circuit 10. On 16 independent holdout seeds it won Grid 12, Fortress 7, Voltage 14, Concord 7, Circuit 15. Different victory conditions and heuristics make those counts **not directly comparable**. The mission-aware one-round policy produced exactly the same first-round plan as Grid for all challenger missions across both sets. That is an especially weak start for a system intended to differentiate strategies immediately.

**Verdict:** Missions are implementable and occasionally strategic, but the current set is not yet a compelling replayability subsystem. Preserve research; **do not ship mission drafting**. Future missions should add public *mid-game decisions with irreversible costs*, not just different numbers on the final victory check.

### Market size: two sets of 24 identically seeded games

| Visible storm choices | Development wins / 24 | Holdout wins / 24 | Total wins / 48 |
|---|---:|---:|---:|
| 1 | 12 | 9 | 21 |
| **2 (control)** | **21** | **13** | **34** |
| 3 | 17 | 13 | 30 |

A three-offer draft created more choice but **not better performance** for the tested one-round planner; the held-out wins were tied, and the three-offer version required assessing an extra storm card each planning round. It may do better under longer search, but no evidence currently justifies adding that complexity. One offer removes a meaningful planning lever and performed noticeably worse. The early-ending loss rate differs between the modes (not every game lasted all nine rounds).

**Verdict:** Keep **two** storm offers and one queued preview (the v0.5 forecast). Do not increase board/UI complexity now.

### Pair synergy without inventing player restrictions

In 110 seeded *opening positions*, considering both draft choices, there were **8,258 legal pairs of token edits** and **135 strictly complementary pairs**, spread across 65 of the 110 seeds. The pair types were:

- ACCELERATE + ACCELERATE: 69
- HOLD + HOLD: 28
- SHIFT + SHIFT: 22
- HOLD + SHIFT: 16

Example seed `44000`, older offered storm: accelerating token 2 alone scores `60.95`; accelerating token 3 alone also `60.95`; passing scores `63.5`; doing **both** scores `64.4` under the *same explicit heuristic*. This is actual *non-additive action value*.

**Verdict:** Shared planning already contains a modest amount of complementary structure. Don't try to manufacture a co-op solution using arbitrary action ownership, uncommunicative constraints, or a new action type. Next build an **actual 2–4-player test protocol** measuring meaningful authored decisions, quarterbacking, round duration, coordination breakdowns, and willingness to replay.

## Tournament decision

**Keep Forecast Market v0.5 unchanged.** It is still the best-supported option among tested candidates. In this pass, neither mission choice nor draft-width changes clearly improve *decision quality per unit of rules*. The cooperation diagnostic shows interesting action relationships without justifying a new enforced multiplayer system.

This is explicitly **not** a finding that v0.5 is the best possible game, or that its six actions should remain forever. It is the best provisional option *under today's evidence*.

### Next mechanical experiments worth paying for

1. Public **mid-game project forks**: a choice between two investments with incompatible costs and delayed payoffs, chosen before enough energy is available to guarantee success. Test a reachable full-game state where plans truly diverge.
2. **Two/three-round information-limited planners** for the current storm draft and Bridge, evaluated on the same visible forecast. Reject content requiring clairvoyance.
3. **Human co-op playtests** at 2 and 4 players using a temporary non-graphical shared action-plan log. Compare number of independent ideas adopted, consensus reversals, quarterbacking incidents, and round deliberation time against solo.
4. If co-op still plays like one player using four hands, consider a fundamental co-op redesign before investing further in incremental rules.

## Reproduce

```bash
python3 -m unittest discover -s tests -p 'test_phase09_lab.py' -v
python3 -m experiments.phase09_survey --cases 220 --games 14
python3 -m experiments.phase09_market_survey --games 24
python3 -m experiments.phase09_coop_probe --cases 110
bash scripts/release_gate.sh
```

Some extended holdout surveys use the callable functions with explicitly different seeds; those exact results are saved in `pass09-results.json`.

**Release scope:** The Phase 09 hotfix is entirely additive to `experiments/`, `tests/`, and `docs/design/`; it does not change source `src/`, the Node server, the shipping reference rules, or any multiplayer protocol.
