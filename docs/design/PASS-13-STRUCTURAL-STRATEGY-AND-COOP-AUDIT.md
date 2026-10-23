# GAIM / Charge Loom — Mechanics Exploration Pass 13

**Status:** research only. **Result:** no promoted rule. Forecast Market v0.5 remains the research control; the shipping TypeScript engine remains v0.1.  **Frozen timestamp:** October 23, 2026.

## The question changed

After twelve explorations, the main bottleneck is not lack of verbs. It is lack of reasons to prefer one multi-round plan to another, along with unresolved cooperative agency. This pass screened *structural* ideas: changes that might turn immediate storm-matching into an evolving strategic relationship. The acceptance criterion was not win rate; it was *repeated, understandable tradeoffs, action interaction, and a credible path to cooperative agency per rule of complexity*.

## Divergent brainstorming and first-pass elimination

| Hypothesis / familiar inspiration | Exact decision it might create | Preliminary verdict |
| --- | --- | --- |
| **Aftershock** / damage-as-resource | Deliberately allow a large leak now to create a small opposite charge two turns later | Prototype and test; ultimately reject as written |
| **Emergency Shunt** / output allocation | Sacrifice capacitor power from an actual collision to cancel hull damage this round | Prototype and test; reserve the concept, reject the current rule |
| **Shared packet network** / route-building | Spend a command to route a newly generated energy packet across a shared, capacity-limited link versus store locally | Unbuilt candidate; merits a separate *replacement economy* prototype, not an extra action |
| **Two-key planning** / cooperative simultaneous programming | Separately authored, conditional storm-selection and charge-routing commitments; each teammate can improve or invalidate another's plan | Unbuilt co-op hypothesis; game-value cannot be inferred from a bot win count |
| **One constrained public objective** / campaign scenarios | Choose which recurring settlement service is funded at the cost of longer-range capacity | Hold; older Council/Dispatch/Project Fork tests were mixed or punitive |
| **Rotating personal power cards** / asymmetric hands | Each player has an ability nobody else can use | Reject for now: prior operator menus restricted useful actions and did not prove agency |
| **Debt-financed extra edits** / push-your-luck | Borrow next-round actions to solve a four-edit emergency | Reject for now: existing action capacity is underused |
| **Permanent passive feeder** / engine-building | Spend heavily now for automatic future production | Reject current formulation: prior Gridworks was rarely purchased |
| **Storm Surge** / push-your-luck | Accelerate two whole storms for an immediate match, risking later bad tempo | Prior trial already suggested opportunistic overuse; no retest warranted |
| **Secret forecasts** / hidden information | Two players have complementary future information and must talk | Reject as default: fairness, quarterbacking, and comms overhead uncertain |
| **Lane origin history** / provenance | Power type depends on route taken, not just collision strength | Deferred: high rule cost until there is evidence the existing economy needs such granularity |
| **Changing player-control seats** / co-op roles | Give everyone one compulsory vote each round | Reject as solution: voting quotas do not produce useful decisions by themselves |

Only Aftershock and Shunt were mechanically novel enough **and** small enough to merit immediate coding. Neither is a proposed shipping change. Bigger structural systems warrant isolated follow-up prototypes instead of being bolted onto the six-action game.

## Tested concept A: Aftershock

*Rule*: An unmatched breach of net strength 2+ still damages the settlement normally. If the hull survives, create one opposite-sign charge in the same lane, placed at SOON after the round, with strength `min(2, net_leak // 2)` and its HOLD already used. It advances normally, interacts with shifts, flips and damping, and counts against the round-9 unresolved-charge deadline. Strength-one leaks do not echo; matched energy does not echo. There is no extra player action.

**Exact rescue**: From round 7, hull 5, energy `2-3-2`, a `+2` in Left breaches and a `+1` in Left is two bands back. Under baseline rules, the +2 deals damage now and the +1 leaks at the finale; Left remains at 2 and the team loses its energy target. Under Aftershock, the +2 produces a returning `-1`. It meets the later +1 on round 9, producing the final energy point and avoiding one damage. Result: **loss → win**, verified with three exact reducer steps.

**Exact cost**: A large leak without a matching later positive returns an extra threat; in an otherwise identical state, it loses an additional hull by the deadline.

**Why it fails the current standard:** The strong move is often still to prevent damage; Aftershock increases delayed liabilities but rarely changes victory paths. It adds a positional token, exceptional generation rules, another delayed hazard and a hidden-feeling endgame tax if not forecast correctly. Human comprehension matters here. We should not make losing HP *sometimes* a useful investment until the surrounding economy deliberately supports that tradeoff.

## Tested concept B: Emergency Shunt

*Rule*: During a round in which at least one actual collision happens **and** a distinct charge produces hull leakage, the team may choose ONE matching lane to spend one of its stored power. This prevents up to two points of the **same-round** breach damage. It does not prevent deferred round-nine liability. There is no extra edit. The source lane must really collide; the capacitor must contain power after collision. This is a conversion of the very resource required to win, not a free shield.

**Exact rescue**: Round 8, hull 2 and energy `3-3-2`. A genuine collision in Left coincides with an unmatched strength-two leak in Center, while a new Left collision is already aligned for the final round. Without Shunt, the settlement is destroyed immediately. With Shunt, Left loses one stored power, both hull damage are blocked, and next round Left refills: **loss → win**. Exact tests verify both continuations.

**Exact cost**: On a final-round board that already satisfies the victory target, using Shunt to block a minor leak can drop a critical capacitor from 3 to 2; the hull survives but the energy target fails: **win → loss**.

**Why it does not earn promotion:** It interacts with matches, but largely functions as emergency hull repair paid out of a capacitor. Previous repair and Vent experiments were already weak. The current Shunt may produce attractive survival without any compelling earlier decision; the short-horizon policy often purchases it after knowing the same-round outcome. That is not the mid-game investment tension or multiplayer authorship the game is missing.

## Reproducible evidence

Files: `experiments/phase13_structural.py`, `experiments/phase13_survey.py`, `tests/test_phase13_structural.py`, `docs/design/pass13-results.json`.

### Synthetic, no-edit exact counterfactuals

Across **600 seeded round-7 synthetic states** (with no future storms), Aftershock spawned **237** charges. Base and Aftershock both won **22** cases: there was **one loss→win and one win→loss**. Final hull was higher in 13, lower in 114 and identical in 473. This comparison deliberately **does not optimize edits to exploit the returned charge**; it tests the passive rule's isolated effects.

Across **600 seeded final-round synthetic states**, Shunt was legal in **96** cases (104 source-lane choices). There were **10 survival rescues**, **one loss→win**, and **one win→loss** among available choices. It cannot be evaluated as a 104/600 win improvement: these are mutually alternative choices from the same states, examined with perfect knowledge of the current round, and most did not change terminal victory.

### Paired whole-session diagnostic

A single identical **one-step planner** was run on **64 seeded nine-round games** (13,400–13,463), with public storm-draft access. Results:

| Variant | Wins / 64 | Edits | Final positive HP sum | Purchases / echoes |
| --- | ---: | ---: | ---: | ---: |
| Forecast Market control | 33 | 743 | 189 | — |
| Aftershock | 33 | 754 | 188 | 27 echoes |
| Shunt | 33 | 761 | 231 | 27 Shunts / 51 HP blocked |

The planner optimizes immediate utility; it **does not plan around future echoes**. In the Shunt variant it selectively buys Shunts when immediate utility improves. This is a policy diagnostic, **not proof** of strategic superiority, equal difficulty or human fun. Shunt raised retained hull dramatically but did not create more wins for this planner. Aftershock did not improve either measure appreciably.

All reducer tests, the existing Python and TypeScript release checks, and golden-state regressions passed locally. The tests validate exact rules, not enjoyment, interactive fairness or human collaboration.

## Recommendation: no promotion

Forecast Market v0.5 remains the research control. The current production game remains v0.1. Neither Aftershock nor Shunt is more compelling than simply retaining the present rules. Adding either now would spend cognitive complexity on a problem it does not solve.

**More fundamental next experiment: jointly controlled *routing* of production, not another survival ability.** Build a separate chassis, not a compatibility layer, in which a matched pair creates energy at an origin and the team must decide how it travels through a constrained common network. The location, capacity and topology of the network should compete with how storm tokens are positioned. Importantly, use the network **instead of** temporary Bridges or isolated capacitor victory counts—not in addition. Compare against current Forecast Market on multi-turn reversal examples, strategic diversity, catastrophic dominant strategies, public-information fairness and rules explanation length.

**Co-op criterion:** A planner should be able to explain one meaningful contribution made by each of four humans in a typical round, *without making unused edits compulsory*. Proposed human test: four participants separately mark their intended edits or forecasts before seeing others' proposals, then jointly agree on a plan. Count independent useful discoveries, negotiation reversals, who originated the final plan, idle player-rounds and whether solo play still feels natural. A headless bot cannot establish these social outcomes. The game may still require rearchitecting planning authority after these tests.

## Selection standard for future passes

Do not select a rule merely because (1) more actions are legal, (2) an optimized agent wins more often, (3) a new option can be bad, or (4) the new mechanic appears in a memorable hand-constructed example. Require **frequent** mutually compelling decisions in states reached through reasonable play, important choices 2–4 turns ahead, distinct viable strategies across sessions, clean teachability comparable to a modern medium-weight board game, and plausible improvement to real 1–4-player cooperative agency. If these criteria are not met, promote nothing.
