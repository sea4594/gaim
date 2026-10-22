# GAIM — Mechanics Tournament, Pass 03

**Decision: select *Delayed Capacitor Bridge* as the next isolated gameplay prototype.** Do **not** yet change the authoritative Python v0.1 reducer, the TypeScript multiplayer game, the Phase 6 contracts, or the victory condition. The other experimental mechanics remain runnable. Nothing in this report is a human-playtest finding.

## Design brief and precedent

We intentionally forced several common board-game mechanisms into Charge Loom, rather than merely inventing more storm-themed abilities. We looked at the strategic value of (1) engine-building/capital investment, (2) area-of-effect control, (3) push-your-luck, (4) objective commitments, (5) incoming-event manipulation, (6) set-collection/combination bonuses, and (7) two mechanisms together. Each became an executable, deterministic rule variant in `experiments/rules_tournament.py`; `experiments/play_tournament.py` is a manual headless playground.

Useful precedents include the fast/slow planning rhythm and resource-based power economy in **Spirit Island**, plus the order-sensitive, prepared spell systems in **Aeon's End**. These are inspirations for *design structures*, not novelty claims or attempts to reproduce those games.

## Six mechanic trials, one combination, one unchanged control

All alternatives retain the baseline 3×3 vertical board, 9 rounds, HP 7, three capacitors (capacity 3 each), three coolant, a shared budget of four edits per round, SHIFT/HOLD/DAMP, collision/leakage, and 8 power with at least 2 in each capacitor to win. Unless an experiment explicitly changes it, the original state transition is preserved. The new rules are not combined by default.

| Variant | Borrowed board-game concept | Exact rule / tension | Diagnosis |
|---|---|---|---|
| **Unchanged v0.1** | Tactical spatial puzzle | No additional action | Simpler, but energy is only a victory counter |
| **Delayed Bridge** | Engine-building; capital investment | Pay **1 power from source** and **1 action** to join adjacent source→destination. **Only during the NEXT TWO resolutions**, a source-lane match gives destination +1 power, once per round, cap 3. One bridge team-wide; cannot renew until expiration. No current-turn benefit | Distinct forecastable risk; best trial |
| **Sweep** | Area-control / shared manipulation | Pay **1 coolant, 1 edit**, move **all charges in one chosen time band** one lane left/right, wrapping around at the edge. Normal token edits may precede the sweep | Can solve novel states, but wraparound adds topology exception and strong AoE complexity |
| **Overcharge** | Push-your-luck | Pay **1 existing power** in a chosen lane and 1 edit. If that lane's imminent matched strength ≥2, receive **+2 extra power** (subject to cap); otherwise take **2 hull damage** | Creates risk, but little strategic value at current capacity |
| **Public Contract** | Betting / simultaneous commitment | Use one edit to pledge a source-lane collision in the **next round**. If fulfilled, adjacent destination gains **+2 power**; otherwise hull loses **1**. At most one pending | Too forgiving as priced; frequently free energy when source match is visible |
| **Storm Front** | Event drafting / weather control | Use one edit to rotate **the next round's newly arriving storm** by one lane, wrapping left/right. Subsequent arrivals unaffected | Agency possible, but value depends on untested forecasting and lane-rotation interface |
| **Harmonic** | Set-collection synergy | If **two or more lanes match in the same resolution**, each matching lane gets +1 extra power, up to its cap. Passive; no edit | Makes winning easier without adding a decision or an investment |
| **Bridge + Sweep** | Engine-building + area manipulation | Delayed bridge and costly whole-band sweep both available. Only one special action per round | Potential combo, but unnecessary complexity / no improvement under tested greedy policy |

**Timing clarification:** A link purchased while resolving round `r` is inactive in `r`. It grants power in rounds `r+1` and `r+2`, then disappears. It is impossible to buy on round 9, since no resolution remains. A round-8 purchase can activate only in round 9 and is usually poor, though not necessarily illegal. It costs one power that was in the source capacitor **before** resolving the current round. If the source does not match on a later round, no bonus occurs; there is no refund. This timing is intentionally *different* from Pass 02's immediate bridge.

### Why delayed investment matters

A 3-band charge takes three resolutions from arrival to breach. Consequently, the charge pairs that *could pay off a newly purchased two-round bridge* are already on the visible board when the player makes the investment. Newly spawned charges in the following round cannot reach the bottom soon enough. This preserves informed planning **without revealing the entire procedural wavebook** or requiring blind predictions. Teammates' subsequent HOLD/SHIFT choices may still create or destroy the match the bridge needs.

**Exact verified win:** At the beginning of round 7, Center holds 2 power, Left 3, Right 0. Two positive/negative pairs are queued to breach in Center in rounds 8 and 9. Buy `BRIDGE(Center→Right)` in round 7, paying Center down to 1. Center's collisions restore power and the link places one in Right each time. Final `3–3–2` wins. Without the link, Right ends at 0 and loses. In a separate verified instance, one planned match only occurs if a second edit shifts a positive charge into Center; removing *either* that SHIFT or the prior bridge results in defeat.

**Exact verified loss:** Start round 7 with `2–3–3`, and no later matches. Do nothing: the team wins 2–3–3. Buy a needless Left→Center link: Left falls to 1, there is no payout, and the team loses 1–3–3. Thus the extra button is not a free upgrade.

## Reproducible experiments and results

### A. Fully enumerated immediate endgames

`python3 -m experiments.tournament_survey --final-cases 300 --greedy-seeds 24`

Generated **300 deterministic synthetic round-9 states**, each with 3–4 NOW charges, randomized small HP/capacitors/coolant. Exhaustively enumerated per-token edits, optional single special, four-edit cap, and only legal resource spends. These are deliberately *not* samples from the actual mission scenario generator.

| Rules | States with any winning plan / 300 | Gain over unchanged |
|---|---:|---:|
| Unchanged v0.1 | 50 | — |
| Sweep | 58 | +8 |
| Overcharge | 50 | 0 |
| Harmonic | 63 | +13 |

A larger number is **not necessarily better**: this test mostly measures added rescue options or rewards, not tension, novelty, difficulty, fairness or fun. Deferred links/contracts/front choice would be improperly penalized by a *last-round-only* test and are therefore excluded.

### B. Genuine two-round capital-investment tradeoffs

`python3 -m experiments.commitment_survey`

Built **576 fixed three-beat states per variant** (varying source/destination, whether 0/1/2 prepositioned source matches occur, and all combinations of starting stored power 0–3 where the source can afford a link). No hidden wave arrivals in these fixtures. Compared precisely one purchase in round 7 against doing nothing, then no edits in rounds 8–9. **This is not a search for the best possible actions**, and the states are not drawn from a realistic distribution.

| Investment | Turns losses into wins | Turns wins into losses | All other states |
|---|---:|---:|---:|
| Delayed Bridge | **44** | **24** | 508 |
| Public Contract | **88** | **0** | 488 |

The Bridge result is significant in one limited sense: the purchase can be *correct or incorrect*, so it creates a genuine tradeoff when the team considers current energy, source collisions, and destination demand. The Contract's zero detrimental states reflect the overly cheap contract in this tested fixture with hull=4; **do not assert a contract can never be bad** in a real run. It is especially vulnerable to automatic purchase whenever a queued match is nearly guaranteed.

### C. Full nine-round control with a shortsighted policy

On **24 identical wavebook seeds**, an immediate-score hill climber won:

- Unchanged: **8/24**.
- Delayed Bridge: **8/24**, and it purchased **zero bridges**.
- Sweep: **5/24**.
- Overcharge: **8/24**, and it used that move zero times.
- Contract: **8/24**, and it pledged zero contracts.
- Front: **8/24**, and it routed zero storms.
- Harmonic: **8/24**.
- Bridge + Sweep: **5/24**.

This policy only values immediate next-round state. It is **structurally incapable of recognizing a delayed payout**. Therefore the unchanged Bridge result is not evidence against the mechanic; it demonstrates why a future-aware, *information-limited* planner and real people are mandatory in the next pass. The sweep losses are also policy-dependent and shouldn't be mistaken for conclusive balance analysis.

### D. Core regression guard

The independent trial reducer reproduced all seven original winning witnesses, round for round and state for state, with no new special action selected (all active variants except the intentionally passive Harmonic). It also matches the original reference reducer over 20 unedited seed runs. The new test suite pins the commitment outcomes, one-round survey, winner/loser witnesses, rule validation, and hybrid behavior. The shipping engine/rooms are unchanged and remain protected by the full Phase 7 release gate.

## Selection criteria and decision

We *do not* rank mechanics primarily by how many extra synthetic states they make winnable. A candidate must (1) create a meaningful **reversible or irreversible strategic commitment**, (2) be capable of being the wrong choice, (3) add multi-turn decisions instead of only scoring, (4) allow complementary actions between players, (5) remain understandable in portrait mode, and (6) be testable with public information.

**Winner: Delayed Capacitor Bridge alone.** It meets the most criteria with only **one new verb**, has an investment payoff across turns, and directly converts earned energy into a resource allocation question. It is substantially better motivated than a package of every new rule. Retain the unaltered v0.1 production game as the baseline and `bridge` as the **provisional v0.2 research ruleset**.

Second-tier: Sweep (strong tactical possibilities, but demanding geometry and poor simple-policy performance). Front choice (plausible procedural agency, but fairness and visibility are not solved). Harmonic (good reward-pattern candidate for future missions, not a core rule). Reject current Overcharge and Contract pricing; do not merge them. Reject the Bridge+Sweep bundle until human sessions demonstrate that a group wants that extra routing responsibility.

## The honest limits of this decision

- **No human playtests**; the label “best” means best *tested design direction*, not proven most enjoyable.
- **All 576 ROI fixtures are selected fixed structures**; they are not an estimate of how often Bridge matters in normal nine-round games.
- A two-turn investment could still be almost automatic whenever profit is obvious. Stronger agents must search for globally dominant policies and forced actions.
- 1–4-player compatibility remains technical only. Shared and perfectly visible decisions still permit one quarterback. The verified Bridge + SHIFT combo establishes *action synergy*, not independently motivated players.
- The capped 3–3–2 victory condition, emergency DAMP, HOLD concentration, wave fairness, nine-round finale, and seven-scenario content limitation remain unresolved. Do not claim endless replayability yet.
- The independent experimental reducer is written in Python. Before merging into production, it must be ported to TypeScript, versioned, tested against a new golden contract, and exercised end-to-end in the room server.

## Specific next pass: falsify the winner

1. Build a **two-turn and three-turn planner** restricted to the information genuinely shown to users; compare to a no-investment baseline and a policy that automatically buys whenever a source match is visible.
2. Generate fresh scenarios and measure **profitable purchases, harmful purchases, and turns a purchase meaningfully changes the recommended action**; stratify by difficulty and board saturation.
3. Challenge Bridge against a cheaper alternative: **permanent storage expansion** or **once-per-game hand-off** so it's not selected solely because it's the only investment offered.
4. Create explicit multiplayer allocation experiments where players can propose different investments/route alignments and test whether a second person has *meaningful authority*, not just a confirm button.
5. Review objectives: permit either several viable resource distributions or a changing mission requirement, without relaxing the fairness criteria.
6. Run human games in headless or lightweight debug clients. Ask whether players notice why an investment succeeded and whether everyone was able to contribute.

If these fail, promote another experimental direction or revert to baseline. No production balancing commitments have been made.
