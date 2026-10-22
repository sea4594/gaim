# GAIM / Charge Loom — Mechanics & Rules Audit, Pass 01

**Status:** Design audit, not a rules change. **Code baseline:** supplied Phase 6 + Phase 7 checkpoint (`charge-loom/v0.1`). **Date:** October 22, 2026. **Scope:** Core board-game decisions, cooperation, replayability, difficulty/fairness, teachability and mobile ergonomics. No project files changed or hotfix issued.

## Executive verdict

**Charge Loom is a mechanically coherent cooperative *tactical matching puzzle*, not yet a strategically rich, endlessly replayable cooperative board game.** Its strongest distinguishing mechanic is HOLD: changing both timing and magnitude of a charge can make taking an immediate loss optimal. Exact examples and golden tests establish that this works. The system still lacks a deep resource economy, meaningful private or distributed player agency, scenario variability and alternative strategic routes. In its current state, polish or large numbers of additional fixed scenarios would not solve its central weaknesses.

Preserve: deterministic resolution; readable three-lane geometry; polarity cancellation; a limited shared action budget; risky timed amplification; the possibility of intentionally taking damage to create a better future. Reconsider: power as a static score, four interchangeable edit slots as the only player interaction, nine-round fixed progression, the all-or-nothing 8-of-9 capacitor objective, and the full-information winning-witness definition of “fair.”

## Evidence and limitations

I reconstructed the code baseline from the Phase 6 and Phase 7 checkpoint ZIPs, inspected `src/engine.ts`, `src/rooms.ts`, the game rules, scenario bank and Python reference, and ran `bash scripts/release_gate.sh` locally. **The gate passed**: all Phase 5/6 checks and **15/15** Phase 7 Node tests. This validates conformity and basic behavior, **not entertainment value**. No human players were tested.

Replaying and analyzing the *seven hand-selected winning transcripts* (63 total rounds):

| Measured property | Result | Interpretation |
|---|---:|---|
| Total edits | 150 / possible 252 | 40.5% of slots unused |
| Rounds using fewer than four edits | 50 / 63 | Four-player action ownership often creates idle seats |
| Mean edits per round | 2.38 | Four distinct edit owners aren't generally needed |
| HOLD / SHIFT / DAMP edits | 70 / 64 / 16 | Holds are prominent; damping is marginal in these winning traces |
| Edits in final round | 6 across 7 games (0.86/game) | Finale has little remaining agency in these examples |
| Final capacitors | five `[2,3,3]` permutations, two `[3,3,3]` (all 8 or 9 power) | Victory converges to a narrow end state |
| Average legal individual edits in rounds 3–7 | roughly 25 per board | Many possible clicks can cause analysis burden despite few needed decisions |

These are *selected winning scripts*, not an unbiased distribution of human play or complete optimal solutions. Earlier heuristic comparisons after the final-leak rule change yielded 3/12 wins for a two-turn heuristic versus 2/12 for a one-turn heuristic in each of two small seed sets; insufficient to claim a robust strategic-planning advantage.

## Priority 0 — Fundamental design problems

### 1. Power is not a usable resource; it is only a victory counter

**Evidence:** A match increases one of three capacitors (capped at 3); no action ever spends capacitor energy. The remaining resources are hull (damage budget), coolant (three fixed damps) and optional edit slots. This is not yet a resource *economy* with productive feedback or competing uses.

**Why it matters:** There is little tension between investing in future flexibility, banking for victory, defending the team, and creating new capabilities. After a lane reaches 3, future power from matching there has no scoring utility, although matching still prevents damage. The experience risks becoming “move matching colors until the three numbers are full.”

**Recommended experiment:** Give stored power **exactly one optional, costly, useful expenditure** at first. Run two *separate* A/B prototypes: `BARRIER: spend 1 power from a lane to prevent up to 2 unmatched breach damage in that lane this round` versus `RELAY: spend 1 power from a lane to make one SHIFT in that lane move a charge two lanes instead of one (if destination exists)`. Both consume victory progress and offer a qualitatively different response to danger. Don't implement both without comparative evidence; don't add several currencies or permanent tech trees. Measure how often smart play spends power and earns it back, whether choices diversify, and whether an effect becomes compulsory. Avoid the seemingly easy 'pay power for a fifth edit' approach: most current rounds don't need their fourth edit.

**Risk:** This can cause runaway combos or render DAMP obsolete. Put a hard per-round ceiling on spending and run exhaustive small states and solver trials.

### 2. Four-player mode currently distributes clicks, not strategic responsibility

**Evidence:** The complete state is public and identical for solo and team play. Players control one of four interchangeable optional edit slots; any one strategist can assemble the full plan. In 50/63 replayed winning rounds, at least one slot was unused. A verified two-edit synergy shows that *two actions* interact, not that *two human thinkers* are needed.

**Why it matters:** Quarterbacking and spectatorship are structurally likely. Preventing a player from clicking another's slot doesn't prevent them from directing the decisions. A PASS/READY press isn't a meaningful turn.

**Recommended experiments (competing, not stacked):**
- **Team draft:** At the start of a round, each seat receives two small action options; chooses one to contribute secretly, then all choices are revealed and placed as a shared plan. Test whether individual judgment matters, the solo interface remains smooth, and the reduced public knowledge produces *good* surprises rather than frustration.
- **Functional stations:** Distribute *different necessary decisions*—routing, timing, storm selection, power expenditure—across players, rather than equal interchangeable edits. With fewer players, combine station control without multiplying separate characters. Test only after these decisions exist and are meaningful.
- **Composed commands:** Require a route decision and a timing/resource decision to jointly produce certain high-value interventions. The same composition can be chosen by one person solo; four players can co-author multiple linked interventions. Watch for artificial obligatory confirmation.

**Acceptance gate:** Observe actual four-player groups; each player should originate at least two strategically meaningful contributions/session and 3+ people should influence the plan in most rounds. Compare with one expert solving for the entire team. Don't declare success based on click or ready counts.

### 3. The content is seven fixed, already-solved levels, not a replayable system

**Evidence:** The server selects from seven immutable, explicit nine-round wave schedules. Complete winning action transcripts are in the development artifacts. No production procedural generation or variable objective selection exists. The seven solutions can be memorized. Positive and negative charges use perfectly symmetric rules; left/right lanes mirror each other, decreasing structural variety.

**Recommended experiment:** A scenario composer with **versioned storm-pattern modules** and **two independently variable mission conditions**, followed by solvability checks and blind-policy difficulty grading. An example pair: a pattern with late strong opposing waves versus frequent weak distributed waves; a task rewarding equal charging versus a task requiring one early burst. Generate *different decisions*, not simply shuffled colors. Treat stored winning witnesses as proof of mathematical possibility, not as the entire playable library.

**Risk:** A huge random seed space alone creates arbitrary difficulty, not deep replayability. Track strategy diversity, not just number of seeds.

### 4. The victory condition is excessively narrow and often predetermined by arithmetic

**Evidence:** Each of three capacitors holds 0–3. To win, all must be ≥2 and total ≥8. The only winning sorted triples are `(2,3,3)` and `(3,3,3)`. Extra charge above 3 is wasted; a nearly full lane is nearly irrelevant to scoring. This is a *single* path-shaped score requirement, not distinct strategic approaches.

**Recommended experiment:** Make the default win threshold more forgiving **after power can be meaningfully spent**, and create variable board-game objectives (one core survival objective plus one or two selectable contracts). As a trial, test `each lane ≥1, total stored ≥6` plus two randomly drawn objective conditions from a carefully validated small set. Don't silently ship these numbers; compare difficulty and solution diversity.

**Risk:** Too-lax thresholds remove tension; too many objectives increase rules burden. Avoid adding extra victory conditions as pure busywork.

### 5. Winning witnesses can depend on unavailable future knowledge

**Evidence:** The verified bank provides *complete*, legal, omniscient winning command sequences. The player sees active charges and **only the next wave preview**, not all later arrivals. A trace under complete foresight does not prove a new player could reasonably identify a winning plan at decision time. After the final-leak fix, short-horizon heuristics won few arbitrary seeds (3/12 for one two-step heuristic), which also does not establish impossibility.

**Recommended experiment:** Evaluate content with (1) omniscient full-game search to establish existence, (2) limited-information policies restricted to exactly the public view, (3) uncertainty stress tests involving identical public prefixes and diverging hidden futures, and (4) novice/experienced human play. Introduce agency over uncertainty—for example, choose between two visible storm forecasts with different risk/reward profiles—instead of relying only on raw hidden randomness.

**Risk:** Revealing every wave would merely make the game a deterministic optimization puzzle, increasing quarterbacking. Control *some* uncertainty without eliminating all discovery.

## Priority 1 — Strategic and pacing weaknesses

### 6. The decision loop has too few fundamentally different consequences

SHIFT changes lane; HOLD changes time and magnitude; DAMP reduces magnitude. All three aim mainly to maximize same-time opposing magnitude and avoid unmatched breaches. Hull never heals; coolant never recharges; power doesn't unlock options. There are no build/develop/exploit decisions or competing objectives. A modern medium-weight cooperative board-game experience typically offers more than a single repeated tactical equation, though not necessarily more basic verbs.

**Recommended change:** Make existing successful matches create **future options** and give sessions a mid-game strategy arc. Favor one feedback loop that modifies the value of later SHIFT/HOLD/DAMP choices over piles of special-case abilities.

### 7. Strategic hold risk may collapse into recognizable recipes

HOLD increases size by one and skips movement, once per token. Across winning witnesses, HOLD is 70/150 actions. The high count isn't proof of a dominant strategy; it is a serious hypothesis worth stress-testing. Pairs of matching magnitude-1 charges can both be held and strengthened, creating extra power at the cost of two edits but no damage if they eventually meet. Holding an unmatchable charge is harmful; whether the intermediate judgment remains rich across many games is unproven.

**Recommended change:** Compare a family of HOLD-first bots, no-HOLD bots, and 2–4-turn searchers. Only if HOLD dominates should its price change: possible costs include heat, future mandatory leakage, or a shared hold budget. Prefer rules that introduce an *interesting* future obligation, not a flat tax for the sake of balance.

### 8. The last phase contains provably unhelpful actions and weak tension

All arrivals are in rounds 1–7, and all remaining tokens leak after round 9. Thus HOLDing a newly spawned FAR charge in round 7 keeps it from reaching a normal round-9 breach, so it cannot be matched at the finale; holding a SOON charge in round 8 has the same problem; round-9 HOLD cannot avoid its eventual full leakage. In the seven witness sessions, **round 9 used only six total edits** and four of seven games passed outright. The nine-round game has a long wind-down, not a strong climax.

**Recommended change:** Prototype a finale defined by a **visible final storm** and a last meaningful conversion/defense choice, rather than an arbitrary hard cleanup. Alternatively allow a scheduled 10th resolution beat with no new arrivals, where remaining charges descend and can still match; retune the encounter to avoid making delay free. Explicitly disable nonsensical late HOLD options in teaching UI even before a rules revision.

### 9. Players can be doomed several rounds before the loss screen

Damage can make hull survival impossible, or missing opposite charges in a lane can make the ≥2 target unreachable, but the engine only declares target failure at round 9. This can generate dead-game turns. A successful automatic action isn't always meaningful if the team has already lost mathematically.

**Recommended change:** Detect mathematically *certain* failure conservatively and offer concession/restart (don't spoil hidden information). Design comeback resources or secondary objectives if repeated hopeless endings are observed. Do not let the UI announce impossibility based on unknowable hidden waves.

### 10. Safety versus progress is too binary; surplus victories lack texture

There is no positive end score beyond win or loss. A 9-power, full-hull victory and a barely surviving 8-power victory are both identical. A full capacitor provides no economic benefit; successful late collisions feel wasted after targets are locked.

**Recommended change:** Keep a clear shared win/loss, but optionally score performance with remaining hull, emergency coolant, optional achievements, and risky contracts. These should create meaningful strategic tradeoffs, not grindable bonuses or online leaderboards as a substitute for replay value.

### 11. Storm timing produces slow feedback followed by a constrained ending

The earliest new FAR charge breaches after three rounds (round 3), so rounds 1–2 cannot create normal collision power/damage from fresh waves. Round 9 has no new arrivals and little room to manipulate delayed futures. Core feedback is concentrated in the middle. This is comprehensible but can feel like setup -> arithmetic maintenance -> cleanup.

**Recommended change:** Seed one or two initial NOW/SOON threats to present an immediate learning/tension beat, and add a late storm twist that is forecast sufficiently to remain fair. Test if this actually improves human experience before changing the nine-round duration.

## Priority 2 — Presentation-related mechanical clarity and scaling

### 12. Choice-space and token stacks may overwhelm portrait players

In the selected winning states, rounds 3–7 average ~8–9 active tokens and ~25 legal individual edit selections per round, spread over only nine cells; multiple charges can stack in the same place and time. Four editable slots create a large possible combined-plan space. A 75-second live timer could reward one very fast quarterback while everyone else tries to follow. This is a *mechanics and interaction design constraint*, not merely missing visual polish.

**Recommended change:** Offer exact resulting-state prediction for a proposed joint plan, distinguish pending arrivals, group equivalent charge stacks, and show expected breach/energy. Test an untimed co-op mode first; only introduce timers after observing planning times. Don't hide necessary arithmetic behind animation.

### 13. DAMP may be a purely emergency button

DAMP consumes one of only three coolant to lower a charge by one, and it was used 16 times across seven selected wins, versus 70 HOLD and 64 SHIFT. It can be a meaningful precaution, but no recharge, alternate use or sustained choice engine exists. **Not enough evidence to remove it now.**

**Recommended change:** Ablation-test outcomes with and without DAMP across solvable content, then either integrate coolant into a meaningful tradeoff (perhaps a spendable repair/forecast tool) or simplify. Removing it blindly could make certain scenarios impossible.

### 14. Player-count equivalence is mathematical, not experiential

One, two, three, and four players always have the same four action opportunities and exactly the same game state. Technically this means a given action plan has the same result for each count, which is useful for testing. But it does not establish four enjoyable seat experiences, or an elegant one-player experience after new co-op roles are added.

**Recommended change:** Preserve a fixed team budget *if possible*, while assigning co-authored decisions differently by player count. Test a full session with solo and each group size, not just exact reducer equality.

## Coherent candidate v0.2 direction: “Charge Loom — Stormworks” (NOT yet adopted)

Keep the physical storm matching and all three original verbs. Make **collision energy have a second use**, add **one small variable strategic goal**, and redesign **who contributes decisions**, in this order:

1. **Energy loop prototype:** Give stored energy an optional tactical use that current spare edits cannot replicate. Test **separately**: `BARRIER (spend 1 energy from a lane to block up to 2 damage there this round)` against `RELAY (spend 1 energy to move one charge from a lane two spaces sideways in one SHIFT, when within bounds)`, at most once per round. Victory targets must be retuned because expenditure reduces final power. Evaluate whether BARRIER overlaps with DAMP or RELAY merely makes the center lane less important.
2. **Scenario objective prototype:** deal two public mission tiles at setup; they change *what success asks for* or *which reward is available*, not the underlying storm arithmetic. Example trial tiles: `Balance` (at end, each lane ≥2); `Reserve` (end with ≥2 coolant); `Early Grid` (two lanes each at ≥2 by round 6); `Perfect Shield` (take no hull damage for three consecutive rounds). These are mutually alternative experiments with appropriate target retuning—not simultaneously mandatory victory requirements.
3. **Co-op authorship prototype:** compare public shared planning against a small private action-option draft (two alternatives per person per round) and against station-responsibility planning. Do not combine them until human tests identify a real winner. Solo should be one small draft, not four simulated characters.
4. **Variable storm content:** compose waves from a few reusable timing/strength patterns, generate or select scenarios, and verify each with both full-foresight search and limited-information policies. Ensure difficult scenarios offer multiple reasonable lines, not one precise clairvoyant solution.
5. **Finale prototype:** planned last wave + full clean resolution with no newly introduced hidden storm at the very end. Remove the late-turn trap where HOLD guarantees unusable leakage.

**Design scope guard:** No asymmetric character powers, campaign upgrades, complex enemy AI, four currencies, elaborate card synergies, or meta-progression until the energy economy and multiplayer authorship prove enjoyable. A coherent medium-weight board game is more valuable than a checklist of mechanics.

## Experiment and acceptance plan for subsequent passes

| Pass | Question | Minimal deliverable | Evidence needed |
|---|---|---|---|
| A — Decision quality | Is a meaningful 2–3-round plan usually superior to obvious tactics? | Small exhaustive state suite + intentionally diverse scenarios | Explainable examples, several viable strategies, measurable improvement over one-step policies |
| B — Economy | Does spending generated power create a productive tension? | Exact trial rules + separate engine branch/simulation | Both spend and save can be optimal, no infinite loops, no trivial dominant line |
| C — Cooperation | Can 2–4 humans contribute real agency? | Two rival authorship prototypes, no UI polish | Video/audio-observed decisions and participation, not mere actions; quarterback comparison |
| D — Replayability | Are repeated games strategically different? | Scenario module generator + variable objectives | Multiple distinct successful strategies and better-than-scripted repeat value |
| E — Fairness | Can players reasonably win without knowing hidden future waves? | Full-info solver, limited-info agents, blind human playtests | Solvable instances, understood losses, difficulty levels with measured outcomes |
| F — Pacing and teaching | Do people understand and enjoy 9–15-minute play? | Text/mock interface and playtest logs | Time per decision, comprehension, engagement, endgame drama, desire to replay |

**Provisional targets for evaluation, not current achievements:** Standard scenarios around 40–65% wins for practiced human groups; three or more players meaningfully influencing most four-player rounds; most new players correctly predicting example collisions after a short tutorial; at least three strategically distinct routes to victory in representative scenarios; fewer moments when obvious best play is “do nothing,” unless passing creates deliberate value. Adjust numerical targets through testing.

## Suggested order of changes

**Do first:** 1) redesign the purpose of power; 2) prototype co-op authorship; 3) build limited-information difficulty evaluation; 4) restructure victory/secondary objectives; 5) improve finale pacing. **Do later:** add variation modules and polish after the central choice engine works. Don't implement all suggestions in one patch; it would make the resulting evidence uninterpretable.

### Final assessment

Charge Loom has a worthy core mechanic, not yet a worthy complete game. The next goal should be to make every successful collision open *another interesting choice* and make every person contribute more than a click. If that cannot be accomplished without bloating the rules, be willing to pivot again.

## Comparative references

- [Spirit Island rules and simultaneous spirit-power planning (Dized, publisher-maintained)](https://rules.dized.com/game/zuxKPAGpQWaqnMZgld8YBg/spirit-island)
- [The LOOP — 1–4-player co-op with energy-powered combinations and changing missions (BoardGameGeek)](https://boardgamegeek.com/boardgame/316412/the-loop)
- [The Crew — cooperative mission structure (Thames & Kosmos)](https://www.thamesandkosmos.com/manuals/full/691869_Crew_Deep%20Sea_Manual.pdf)
- [BoardGameGeek — Replayability and non-automatic decisions](https://boardgamegeek.com/blog/5824/blogpost/117149/what-makes-a-game-replayable-and-does-it-matter-if)
