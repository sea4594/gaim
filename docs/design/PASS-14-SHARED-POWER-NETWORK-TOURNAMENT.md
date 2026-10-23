# GAIM mechanics research — Pass 14: shared power networks

**Decision: no promotion.** The unchanged Forecast Market v0.5 remains the research leader. All three network experiments are additive research code only; the shipping Python reference, TypeScript engine, server, protocol and golden traces remain unchanged.

## Design question

Our previous passes exposed a structural problem: energy is mainly a victory counter. A temporary Bridge invests it to create bonus energy, but does not make the existing stored energy flow through a shared system. Could a genuinely *transport-based* economy replace Bridge and create decisions with longer consequences, richer use of surplus, and stronger coordination?

This pass borrowed three ideas from board games: **network building**, **switchable routing**, and **contract fulfillment**. We implemented a reducer rather than relying on written pitches. Crucially, all variants **replace** the Bridge action rather than accumulating a seventh or eighth charge verb.

## Explicit rules of the three challengers

The board, nine-round deadline, 1–4-player four-edit budget, Shift/Hold/Damp/Flip/Accelerate, collision timing, capped capacitors, hull damage, and two-offer Storm Market remain unchanged unless explicitly superseded below.

### A. Conduit — paid persistent investment

- One directed connection may exist, chosen from `Left→Center`, `Center→Left`, `Center→Right`, `Right→Center`.
- `WIRE(source,destination)` uses one shared edit **and** one already stored energy from the source. Choosing a new wire replaces the old one. There are no diagonal connections.
- A purchased wire activates **next round**, not immediately. A wire survives until replaced or the game ends.
- Once a round, before charge collisions, the *previously active* wire automatically transfers exactly one power from source to destination **if** the source has at least two and destination has less than three. This leaves at least one source power.
- Transferring preserves total energy. Its possible payoff is freeing source-capacitor capacity **before** a fresh collision adds production. The wire never produces energy on its own.
- The existing victory condition stays `at least 2 per lane and 8 total, survive`.

### B. Switch — free but action-consuming configuration

Identical directed-link routing, except WIRE costs **no power**, just a shared edit. This is a deliberate control to isolate the difference between a consequential investment and a low-friction movement utility. Otherwise no special bonuses.

### C. Service Grid — transport economy plus consumptive objectives

Uses paid Conduit rules plus `DELIVER(lane)` at a cost of **two previously stored energy from that lane and one edit**. Each lane can be delivered once. The end goal **replaces** the original capacitor target: finish alive, with any **two distinct lanes served** and at least **four total power retained**. The spent energy does not return. This is not directly comparable on raw win rate to the original game because victory conditions differ.

Purchases, deliveries and routing effects are deterministic and immutable. No existing action is allowed to spend energy generated later in that same round. Only one infrastructure action is allowed per round, but the usual overall four-edit budget remains.

## Verified interaction — production through freeing capacity

We constructed an exact three-round witness. At the beginning of round 7 (zero-based state round 6), capacitor levels are **3–1–2**, and three successive rounds have one strength-1 positive/negative pair naturally arriving in Left.

- **Without Conduit:** all three Left collisions arrive at an already-full Left capacitor. The team ends at **3–1–2**, losing.
- **With WIRE Left→Center now:** pay one Left energy immediately, temporarily reducing Left from 3 to 2. The current Left collision refills it. During the following two rounds, the wire carries one Left power to Center *before* each collision; the collisions replenish Left. The game ends at **3–3–2**, winning.

This demonstrates a genuine conditional return rather than a flat power bonus. Conversely, in an exact final-round fixture starting at **3–3–2** with no future collisions, spending one power on WIRE loses when passing wins. Both witnesses are automated tests, not hypothetical gameplay descriptions.

## Objective tests

Two independent reproducible synthetic test sets, **700 two-round states each**, compare all legal one-edit wire purchases against passing. They use the same starting positions, include both beneficial and harmful purchases, and do **not** simulate optimal later edits. This isolates the **one-purchase decision**, not overall game quality.

| Metric | Paid Conduit: dev / holdout | Free Switch: dev / holdout |
|---|---:|---:|
| States examined | 700 / 700 | 700 / 700 |
| Purchases evaluated | 2,121 / 2,110 | 2,800 / 2,800 |
| States where some purchase rescues a loss | **2 / 1** | **4 / 4** |
| States where some purchase spoils a win | **12 / 11** | **2 / 3** |
| Total automatic transfers after tested purchases | 310 / 321 | 608 / 597 |

**Interpretation:** Paid Conduit is a costly investment with a low probability of paying off in a *two-round terminal* context, although the constructed three-round witness shows its intended strategic return is real. Switch provides more rescues in this narrow comparison mainly because it is free. Neither outcome demonstrates deeper cooperation or engaging human planning. In each 700-state set only 15 passes were baseline wins, which limits interpretation of spoiling counts. Many synthetic states were unwinnable regardless of any single action.

A separate passive four-to-five-round probe tried an initial purchase followed by zero further edits, using an explicit reproducible future wave schedule. There were **no wins in 350 states per variant**, with or without a wire. This tells us that the *no-edit policy is much too weak* to evaluate long-term network play; **it is not evidence the network cannot support good play**. We retain this failed test transparently rather than use it for a conclusion.

The same synthetic states with an already-active link showed that energy transfers really occurred (532/1,400 active-wire round opportunities in development; 539/1,400 on holdout). However, an active link was **gifted** in that probe, so those data are only an upper-bound opportunity diagnostic, not an investment profitability result.

### Service Grid finding

In the developmental final-round sample there were 85 states with at least two legal delivery choices and **zero** states where the different deliveries changed the win/loss outcome. The independent holdout had 91 comparable states and **one** differing outcome. This is a warning: the simple service objective largely reduces to a count of delivered lanes and an aggregate power threshold, making destination choice surprisingly interchangeable. It does not yet generate the desired portfolio strategy. Its win counts cannot be compared with Forecast Market's, and Service Grid is rejected in this form.

## Where these rules fail the standard

1. **Conduit's cost is front-loaded, and endgame opportunities are scarce.** Many purchases merely redistribute already limited points without returning the investment.
2. **Switch has fewer costs but little strategic commitment.** It risks becoming routine bookkeeping: put the wire wherever power is missing.
3. **Service Grid replaces a narrow victory condition with another narrow arithmetic condition**, without demonstrated differences in medium-term planning.
4. **Four-player agency is unchanged.** One skilled player can choose every route, storm and charge edit. The network offers a topic for discussion, not a proven reason for independent contribution.
5. **Additional state and order-of-operation rules are real costs.** Players must remember wire orientation, activation delay, automatic threshold, transfer order, and delivery flags. We did not demonstrate enough improvement to justify them.
6. **Our agents remain weak for persistent investments.** Exact three-round witnesses establish possibilities, not frequency or enjoyment. A network-aware multi-turn solver and actual human sessions are prerequisites for promotion.

## Winner and next exploration

**Keep Forecast Market v0.5 unchanged as research leader.** No production mechanics changed. Preserve Conduit as a research candidate because *redirecting power before generation* is meaningfully different from Bridge's extra generation. Reject current free Switch and current Service Grid unless a substantially new objective makes them valuable.

A better next structural experiment may require **simultaneous competing consumers with limited throughput** rather than another resource purchase: for example, a public priority-setting problem that determines whether scarce energy protects hull, powers objectives, or permits token edits. Such a system should *replace* several existing rules, not sit on top. Equally importantly, we must design a test where multiple human players regularly contribute valuable independent assessments, rather than just cooperate in pressing buttons.

## Reproduce

```bash
python3 -m unittest tests.test_phase14_network -v
python3 -m experiments.phase14_survey --states 700 --seed 14700
python3 -m experiments.phase14_survey --states 700 --seed 16200
bash scripts/release_gate.sh
```

Numbers and counterexample states are saved in `docs/design/pass14-results.json`. The test scenario bank and shipping rules remain untouched. This is a **mechanics laboratory**, not a playtest or claim of improved fun.
