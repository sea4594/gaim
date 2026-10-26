# GAIM redesign — Phase 2A: STORM ENGINE

**Status: complete preliminary design for a Phase 3 prototype; NOT a selected or production ruleset.**  Version `storm-engine/draft-0.1`. A different game from the shipping Charge Loom reducer; no compatibility with its golden traces is implied.

## 1. Game in verbs

Predict descending positive and negative charges; shift, hold or damp them to engineer collisions; use the resulting shared power to restore two of three settlement systems; exploit the strengths you build while defending their vulnerable lanes. You cannot afford to restore all three systems in every scenario. Winning should feel like committing to a style of play and then adapting when your preferred strategy comes under pressure.

**Distinguishing wager:** production, safety and board control compete for the *same* power. Buying development today costs the energy needed for tomorrow's emergency. Permanent settlement improvements change which future charge manipulations are profitable.

## 2. Physical components and portrait layout

- 3 lanes: **Left / Center / Right**, each with 2 visible depth bands, **FAR** and **NEAR**. Charges have a public stable ID, lane, band, sign `+`/`−`, strength 1–3, and `held` flag.
- **Hull:** 6 at setup; when it reaches 0 or less, the team loses immediately.
- **Power:** one *shared* pool, 0–8, starting at 2. Power is not lane-local. Overflow above 8 is lost; shortages never create debt.
- **Coolant:** 2 at setup, 0–2 maximum. Spent only for DAMP; it cannot be replenished in this draft.
- Three settlement systems, fixed to their respective lanes: **Dynamo (Left), Aegis (Center), Switchyard (Right)**. Each has level 0, 1 or 2, and can be **offline for the next round** after a large breach.
- A face-up eight-round storm schedule. At the start of round `r`, players see incoming storm `r` and the next round's storm `r+1`; subsequent storms are unknown. A storm lists zero or more signed charges entering FAR. Scenarios define these lists and IDs; they do not use hidden post-decision randomness.
- A shared action row with **two edit slots** and **one optional construction slot**. The board fits a portrait viewport with storm forecast above and systems/power below; all icons must have sign/number text alternatives.

```
          CURRENT + NEXT STORM
          FAR     L | C | R
          NEAR    L | C | R
          BREACH  L | C | R
    Dynamo 0–2  Aegis 0–2  Switchyard 0–2
       HULL • POWER • COOLANT • ROUND
          EDIT 1 / EDIT 2 / BUILD
```

## 3. Exact setup and objective

- Set `round=1`, `hull=6`, `power=2`, `coolant=2`, all system levels to 0, all offline flags false, and an empty board.
- Select one published eight-round storm schedule; the scenario must specify **all** arrivals in rounds 1–8 and must expose current and next waves exactly. No seeded Python/JS random generation is required at runtime.
- **Victory:** at the end of round 8, hull is positive, *at least two distinct systems are at level 2 and operational*, and no future waves remain. An offline system does not count until repaired automatically after its one-round outage.
- **Defeat:** hull reaches zero at any time, or round 8 ends without meeting the level/operational condition.
- Unresolved FAR and NEAR charges at the close of round 8 each deal hull damage equal to their full strength, ignoring matching; this is the public deadline rule. A HOLD during round 8 cannot erase a liability.
- Early mathematical impossibility is **not** automatically a defeat; that is a known pacing risk to test in Phase 3.

## 4. Systems — costs, permanent consequences and vulnerability

Each upgrade is a separate **BUILD**, costing exactly **2 power**. You may build at most once each round. The new level becomes active at the **beginning of the next round**, never immediately. Build can only increase a system by one level; level 2 is maximum. You cannot build an offline system. Upgrades never decay, and there are no maintenance costs.

| System | Level 1, active next round | Level 2, active next round | Main strategic risk |
|---|---|---|---|
| Dynamo / Left | On the **first successful Left collision** each round, gain +1 bonus power. | On the **first successful collision in any lane** each round, gain +1 bonus power instead. | Powerful if you keep making collisions; useless without them. |
| Aegis / Center | Reduce total breach damage by 1 each round (minimum 0). | Reduce total breach damage by 2 instead. | Helps survival but does not generate victory power. |
| Switchyard / Right | One **free SHIFT of a FAR charge** per round after paid edits. | One **free SHIFT of a FAR or NEAR charge** per round. | Improves positioning but cannot change polarity or timing. |

**Offline rule:** If the *unshielded* unmatched strength **in the system's own lane** is at least 2 during a breach, that system is marked offline for the **following round only**. This happens whether or not Aegis later absorbs some hull damage. Its level is retained. Offline disables its bonus, free SHIFT, and construction for that following round; it clears automatically at the end of that round. A system that was offline **during round 8** (because of round 7 breaches) does not count for victory. An outage newly triggered by round 8 breaches cannot affect a round 9 and does not retroactively disable the round 8 victory check. Multiple breaches in one lane still create only one offline marker for that lane. An offline system can be marked offline again by a new breach, extending the outage one round at a time. **Important:** the pending next-round outage marker and current-round offline status are separate bits so an old outage cannot accidentally clear a newly inflicted outage.

## 5. Individual edits and validation

The team submits **zero, one or two** paid edits per round. Every paid edit selects an existing charge by public ID, and one charge may be targeted by **only one** paid edit that round. PASS simply leaves an edit slot unused.

- **SHIFT(token, LEFT/RIGHT)**: move one lane laterally; must remain within Left/Center/Right. Neither strength nor depth changes.
- **HOLD(token)**: if `held=false`, mark `held=true`, increase strength by 1 up to 3, and stop this token from advancing **for this round only**. A token can be held once in its lifetime. HOLD at strength 3 still uses an edit and stops motion, but adds no strength; this can be strategically wrong.
- **DAMP(token)**: spend 1 coolant and reduce strength by 1. A charge reaching strength 0 is removed before movement. Coolant and edit are spent even if that charge would otherwise have collided profitably.

**Switchyard SHIFT** is a *separate free system action*, applied after both paid edits, allowed once per round while online, and may affect a token already paid-edited. A free SHIFT can never move a token out of bounds; if unused, it expires. Paid edits process in submitted order, then free SHIFT, then movement. BUILD consumes its 2 power before charge movement; bonus systems for this round are the *levels active at the start of this round*, so a new purchase cannot benefit immediately.

There are no attacks, Flip, Accelerate, temporary Bridge, Storm Market, separate lane capacitors, action cards, or enemy health pools. Those are **deliberately removed** compared with Forecast Market v0.5.

## 6. Deterministic round order (authoritative draft)

1. **Start and forecast.** Install exactly the offline markers generated by the *previous* round, activate upgrades bought in the previous round except that an offline system receives no active benefit, and place this round's listed incoming charges in FAR. Publicly display the next wave. There are no hidden events after this point.
2. **Plan.** Submit up to 2 paid edits, 0 or 1 BUILD, and at most one available Switchyard free SHIFT. All choices and card IDs are public. Validate **the whole plan atomically**, including power, coolant, targeting and BUILD legality. If invalid, nothing executes; the team revises the plan.
3. **Purchase.** Spend 2 power for BUILD, record the upgrade as pending next-round activation.
4. **Manipulate.** Resolve paid edits in selected order. Resolve optional free Switchyard SHIFT. Record held token IDs.
5. **Advance.** Remove strength-zero charges; unheld FAR becomes NEAR; unheld NEAR reaches BREACH; held charges remain in place. Reset only their *per-round* stop condition, not the lifetime `held` bit.
6. **Collide and leak, simultaneously by lane.** For each lane, add all breached positive strengths `P` and negative strengths `N`. Generate `min(P,N)` power; the unpaired strength `abs(P−N)` is *unshielded* hull damage and may knock that lane's system offline next round. All breached tokens disappear, whether or not matched. Count one "successful collision" in a lane if `min(P,N)>0`.
7. **System effects.** If Dynamo is active and online, add **at most one** bonus power in its eligible lane(s) per round. If Aegis active and online, reduce the **sum** of unshielded damage across lanes by its level (not per lane). Apply net damage to hull. Clamp power at 8 **after** base collision generation and Dynamo bonus; do not waste production until then.
8. **Finish.** If hull <=0, lose. If round 8, deal deadline damage from all unresolved charges and evaluate hull and victory using the current round's offline markers. Otherwise retain only the newly generated outage markers for the next round and increase round.

**Edge cases:** A fully cancelled lane cannot knock its system offline; `P=3,N=1` gives 1 power and 2 raw damage, not 3 power; Dynamo uses collision existence rather than strength as its bonus condition; overflow cannot be reclaimed later; Switchyard cannot target a charge that has already been destroyed by DAMP; a doomed round's power does not revive the hull; BUILD with exactly 2 power is legal.

## 7. Player counts and cooperation hypothesis

**1–4 players use exactly the same shared two edits, one BUILD and at most one Switchyard free SHIFT.** One player can operate the entire game. With multiple players, proposals can be made concurrently, but only one consensus plan resolves. This deliberately does **not** pretend that splitting control of those three buttons creates good co-op.

One *possible* Phase 5 co-op variant (not part of this preliminary ruleset) gives each player a small private opportunity card; doing so requires demonstrating that the additional information changes independent contributions without turning the game into hidden trivia. In Phase 3 we must log who proposes plans, who revises them, whether a player can quarterback, and whether spending/BUILD debates are interesting at 2–4 players. If multiplayer feels like a group-operated spreadsheet, this candidate may lose to Operations even if its solo strategy is deeper.

## 8. Worked early rounds: exact accounting

This is a deliberately easy **resolver sanity scenario**, not an example of balanced difficulty. Define wave 1 = `[L+2,L−2]`, wave 2 = `[C+2,C−2]`, wave 3 = `[R+2,R−2]`; each enters FAR in the specified round. No edits are required to match tokens in the same lane. Charges entering FAR in round 1 reach NEAR in round 1 and BREACH in round 2.

| Round | Paid decisions / build | Collision | Power calculation | Result |
|---|---|---|---|---|
| Setup | — | — | start 2 | Hull 6, all levels 0 |
| 1 | BUILD Dynamo L1, cost 2 | None | 2−2=0 | Dynamo L1 pending |
| 2 | No build | Wave 1 Left +2/−2 | 0+2+1 Dynamo =3 | Hull 6; wave 2 now NEAR |
| 3 | BUILD Dynamo L2, cost 2 | Wave 2 Center +2/−2 | 3−2+2=3 | Center does **not** activate Dynamo L1; L2 is pending for round 4 |

A level-1 Dynamo only triggers on a **Left** collision. A mistakenly applied Center bonus would contradict the rules; the arithmetic smoke test checks the correct total.

## 9. Whole-session demonstration and meaningful strategic forks

**Eight-round legal-winning *smoke-test fixture* (arithmetic-verified, not yet replayed by a complete engine):** `r1 L±2; r2 C±2; r3 R±2; r4 L±2; r5 C±2; r6 R±2; r7 no wave; r8 no wave`. BUILD choices `r1 Dynamo L1; r3 Dynamo L2; r4 Aegis L1; r5 Aegis L2`; remaining edits PASS. Natural collisions occur rounds 2–7; Dynamo supplies extra after it becomes L2; the team reaches two level-2 systems and survives with hull 6. The control case never BUILDs and loses on the target despite surviving, showing that energy must be invested rather than simply collected. Both outcomes are checked by `tests/test_redesign_phase2_specs.py`.

**Important:** The working example above is a **specified test fixture**, not yet a full engine replay. Phase 3 must verify activation order, power balance, and result with an independent reducer; any discrepancy requires fixing the rulebook or sample, not waving it away.

**Early fork to test:** From a scenario that presents repeated Center collisions and a predictable right-lane breach on round 5, choose between (A) Dynamo first (invest now, generate more power later but take damage) and (B) Aegis first (survive with less output, finish with Switchyard as second level-2 system). These are *hypotheses for distinct viable strategies*, not claimed demonstrated solutions. A scenario generator should seek positions where both routes can succeed but diverge for at least three rounds.

**Complementary-actions example 1 (verified by arithmetic, not a full game):** `L+1 NEAR`, `R−1 NEAR`. One SHIFT into Center fails to match either alone; SHIFT both into Center results in `P=N=1`, yielding power 1 and hull loss 0 instead of 2. The two actions consume the entire team's edit budget.

**Complementary-actions example 2 (investment and timing):** Suppose the team has power 2, Dynamo 0, and next round contains a Left `+2/−2` matching pair. BUILD Dynamo L1 this round spends the 2 power and enables next round's +1 bonus. This plan competes directly with saving the same 2 power for Aegis. This is economic complementarity **between decisions**, not proof of complementary *players*.

**Failure example:** In the sanity schedule, skip all BUILDs, take no damage and generate power until capped at 8; finish round 8 with levels `[0,0,0]` and lose `loss: systems`. This is intentionally a genuine non-hull failure, not a claim that gameplay is engaging.

## 10. Rules-burden ledger and three immediate exploits to attack

- Core verbs: **SHIFT, HOLD, DAMP, BUILD**; optional system SHIFT reuses the same movement verb. 2 paid edits + 1 purchase each round.
- Resources: hull, power, coolant. Persistent state: three levels plus offline status. Temporary state: positions, strengths, held markers, pending activations. One multi-step resolution procedure.
- Principal exception risks: future activation, offline timing, final leakage and Dynamo's first-collision limit. Any one that fails to create worthwhile decisions is a removal candidate.
- **Exploit 1, always build Dynamo:** if the early power bonus reliably pays back, other opening investments may be dominated. Require matched scenarios where Dynamo-first loses and another opening wins.
- **Exploit 2, raw damage tanking:** if 6 hull and Aegis make breaches too forgiving, teams may ignore storm manipulations. Compare no-edit play against intentional routing in seeded games.
- **Exploit 3, two upgrades are bookkeeping:** if "buy two level-2 systems" becomes an obvious fixed purchase order, the economy is decoration. Require multiple competitive upgrade paths and foregone-opportunity explanations.

## 11. Phase 3 implementation contract and unresolved risks

Implement an independent pure reducer with explicit waves and deterministic unit tests covering all eight resolution steps, one-round downtime, overflow, terminal leakage, construction activation, and all player counts. Obtain **two actual replayable wins using different pairs of restored systems on the same scenario**, plus one loss caused by bad investment and one by a storm. That is a research gate, not a current accomplishment.

**Current blockers:** the outlined game may be too economically easy on match-rich scenarios; shields/offline may require too much tracking; and a leader can still fully operate the two edits and BUILD. If removing a system improves clarity without reducing difficult decisions, do so. If strategic development cannot coexist with exciting storm interaction, abandon this structure.
