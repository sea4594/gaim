# GAIM redesign — Phase 2B: STORM OPERATIONS

**Status: complete preliminary design for an independent Phase 3 prototype, not promoted.** Version `storm-operations/draft-0.1`.

## 1. Game in verbs

Each participant manages a tiny personal deck of interventions and secretly chooses a tactical commitment. The team discusses threats and options, then reveals its orders simultaneously; certain combinations rescue an operation, while badly coordinated plans waste scarce cards. The group tries to complete **two of three public missions** before its settlement is breached. This game is about joint operations and mutual commitments, **not** building an economic engine.

**Distinguishing wager:** Each round participants control different scarce actions that recycle only after their personal deck runs out. Players have influence over how to deploy their own options; the team cannot freely choose any sequence of actions. Limited information is **about what teammates can afford next**, not arbitrary secret enemy stats. Players may talk freely, including voice chat; hidden hands are not treated as magic anti-quarterbacking protection.

## 2. Board, cards and setup

- Same portrait-friendly **three lanes × two time bands** as Storm Engine: FAR / NEAR, with breaches at the bottom. Charges have an ID, sign, strength (1–3), lane, depth, and lifetime `held` flag.
- **Hull:** `4 + number_of_players` (1p=5; 2p=6; 3p=7; 4p=8). The higher hull is an *unvalidated scaling hypothesis* to test, not a balancing claim. There is **no stored power, coolant, capacitor, BUILD, Bridge, or upgrade**.
- Each human player owns a personal 9-card command deck: `SHIFT-L ×2`, `SHIFT-R ×2`, `HOLD ×2`, `FLIP ×1`, `DAMP ×2`. DAMP costs no coolant here; card depletion is its opportunity cost. Each card has **one simple effect**. Players draw a private hand of **three** (solo draws **four**) at setup.
- Each round has **one normal commitment per player**, except solo has **two commitments** from one four-card hand. Players may use the **same charge as a teammate**, within the two-order-per-charge composition limit below; this is how actions combine instead of merely filling different slots.
- Each deck is independently shuffled by a scenario-supplied seed; draw/discard are deterministic once the seed is fixed. When a draw is needed and the deck is empty, shuffle that player's discard pile; the just-played card does not re-enter the pile until the end of the current round, preventing same-round recycling. If fewer cards exist, draw what is available. No draw occurs during planning.
- There are always exactly **three** public mission cards from a six-card mission pool, chosen at setup by scenario. The team must complete **any two different missions** by the end of round 8, and keep hull >0.
- Incoming storm waves are explicit public scenario content; current and next waves are visible. Rounds **1–6** each bring exactly `players+1` new charges (maximum 5 at 4p); rounds **7–8** bring zero new charges so the last arrivals can resolve and the deadline can be evaluated. The deck generator must produce corresponding content for each player count. This creates more hazards with more player interventions but does **not** guarantee balanced difficulty. In solo, two threats and two orders are the intended experience, not one person puppeting four hands.

### Portrait map

```
       CURRENT STORM / NEXT STORM
           FAR L | C | R
          NEAR L | C | R
        BREACH L | C | R
           [THREE MISSIONS]
        HULL • ROUND • OPERATION LOG
      [YOUR 3 CARDS] • COMMIT • READY
```

Players see their own hands and the **counts** of cards in teammates' hands, but not their card identities unless communicated; the shared board and missions are always public. This must not require a tiny drag-and-drop interface to play.

## 3. Cards and exact semantics

A player selects a card from their hand, a current charge ID (for all card types), and an optional SHIFT direction implied by the card. A player may instead **PASS** (keep their hand intact, commit no action). All chosen card actions must be legal on the shared board **at the start of planning**: charge IDs must exist, and SHIFT cannot move outside the board *at submission time*. A direction that later becomes impossible because another order moved the charge resolves as a **fizzle** (card still spent).

| Card | Effect | Consequence / constraint |
|---|---|---|
| SHIFT-L / SHIFT-R | Move chosen charge one adjacent lane; same depth | May fizzle if target exits board after a prior SHIFT |
| HOLD | If charge never held, increase strength by 1, max 3; stop advancement this round | Charge can be held only once during entire life; targeting an already-held charge at submission is illegal |
| FLIP | Reverse charge sign without changing strength | Can create or ruin a future match |
| DAMP | Reduce charge strength by 1; remove at 0 | Might prevent damage or destroy a useful match |

**Important composition rule:** Up to **two** different players may target the same charge in a round; solo may use both commitments on that charge. A single charge can receive two actions, including two cards of the same kind (e.g. SHIFT then SHIFT), but never more than two. This limit is checked against the full team plan before locking the round. At resolution, all submitted cards are sorted by **current round's rotating initiative seat**, and applied sequentially; the target charge may change before the second card. Invalid-at-resolution effects fizzle but are discarded. HOLD's stop marker persists through this round even if a later SHIFT/FLIP occurs. DAMP at strength 1 destroys the charge immediately and any later order on that token fizzles.

**Communication:** Teammates can say anything, even list their exact cards. Simultaneous submission is designed to create commitment ownership and uncertainty about teammates' final choice, not to police chat. Every participant can revise until all are READY. When everyone is ready, choices become irrevocable, are revealed simultaneously, and resolve by rotating seat order. A player may unready and revise only before the last participant readies. Disconnection retains a pre-submitted order; if missing by a planning deadline, that player automatically PASSes without losing a card. (Timers themselves are a UI/server rule, not a randomness source.)

**Solo:** One player privately sees four cards, commits 0–2 different cards, and has a single 9-card deck. No virtual teammates, hidden hand simulation, or extra role bookkeeping. End-of-round refill returns the hand to four if supply allows. Solo's two slots resolve in card selection order.

## 4. Mission board: six concrete cards

At setup pick **three distinct** missions; all six below have deterministic counters/markers and require no individual mission actions. Completing any two counts once; extra events after completion do not award additional points. Counters start zero, except Fortify's `clean_streak` starts zero.

1. **Three Stations:** achieve **at least one matched collision in each of Left, Center and Right** during the session; track three lane marks.
2. **Double Pulse:** on **two different rounds**, achieve matched collisions in **at least two distinct lanes** within the same round; track two pulse marks.
3. **Deep Capture:** achieve a single-lane collision worth **at least two matched strength** at least once; one marker.
4. **Clean Passage:** finish **three consecutive rounds with zero net hull damage**; increment clean streak on each such round, reset to 0 on a damaged round. (A successful DAMP of dangerous charges counts as clean.)
5. **Precision Route:** on **two different rounds**, achieve a matched collision in **Center and no unmatched breach in Center** that round; track two marks.
6. **Last-Moment Save:** at least once, a charge that was in NEAR at planning time is modified by an action this round, AND its lane achieves a matched collision from at least one modified token that round; one marker. This forces timely action, not merely naturally matched storm pairs. The token's ID must appear in the collision's breached set.

**Scoring is evaluated from actual resolution events, not player claims.** If a mission is completed during round 5 it remains completed even if the team later loses hull. The team can switch priorities if a desired contract becomes difficult. Any two of the chosen three are enough—no mandatory mission is allowed.

## 5. Complete round sequence

1. **Arrival:** At round start, place the wave's `players+1` charges in FAR. Show the next wave's full list. The current board and mission counters are public.
2. **Discuss:** Players may freely exchange forecasts, intentions or the contents of their personal hands. There is no secrecy enforcement and no out-of-game communication punishment.
3. **Commit:** Each player privately selects 0 or 1 card plus target; solo selects 0–2 cards. Validate submission-time legality; show a public preview of target IDs and the number of commitments, but keep verbs private until lock. Validate the whole team's target multiplicity <=2; otherwise do not lock and allow revision. No card is consumed before lock.
4. **Lock/reveal:** When all players are READY (or timed out), cards become public. Resolve in rotating player-seat order: round 1 `0,1,2,3`, round 2 `1,2,3,0`, etc., skipping nonexistent seats. Solo follows its own selection order. Movement/flip/damp/hold apply immediately. A card that fizzles is discarded anyway.
5. **Advance:** All unheld FAR tokens advance to NEAR; unheld NEAR tokens reach BREACH. Held tokens stay at depth and retain their lifetime `held=true`. Removed tokens cannot breach.
6. **Collide and damage:** In each lane, aggregate breached positive and negative strength. Matched strength is `min(P,N)`; unmatched strength `abs(P−N)` damages hull. All breached charges disappear. All collisions and identifiers are logged. No capacitor or energy generation is stored: successful collisions are an *event* for missions, not a commodity.
7. **Mission events:** Update all three public missions using the just-resolved breach event, net hull damage and changed-token IDs. Then if hull <=0, immediately lose. If round 8, unresolved charges each cause full-strength deadline hull damage; if hull positive and >=2 missions complete, win, otherwise lose. If game continues, discard played cards, refill hands (reshuffling personal discards as needed), rotate initiative, increment round.

**Fizzle and legality edge cases:** SHIFT from center into a now-occupied lane is legal (there is no cell capacity); a charge moved to edge by an earlier order makes a later outward SHIFT fizzle; HOLD at strength 3 is still legal on a never-held token but doesn't add strength; if a token is DAMPed to 0 before its second order, that second order fizzles and is discarded; no mission can be credited from a fully cancelled token without an actual breach event; deadline leakage is *not* a matched collision, cannot complete any mission, and cannot be cleaned by a late HOLD.

## 6. Designed cooperation and how it differs from Forecast Market

- **Real ownership of options:** One participant's SHIFT or FLIP is not fungible with another's DAMP, because using a card affects that participant's future hand composition. The team must plan around individuals' available options.
- **Simultaneous owned commitments:** Everyone submits something (or deliberately passes); a proposal can become a teammate's opportunity via token composition. Turn order and future personal resources create local judgments.
- **No special seat skills:** card distribution is random, disclosed through voluntary speech, and recycles. A player can openly tell everyone their hand; anti-quarterbacking comes from choices with future costs and independent commitment, **if** human testing supports that claim. It is not a guaranteed property of the rules.
- **No artificial silence:** There is no rule restricting voice or typed chat, and the engine will not attempt to enforce secrets after players speak.

**Combination A — paired action rescue:** `L +1 NEAR` and `R −1 NEAR`. If player 1 holds a SHIFT-R and player 2 holds SHIFT-L, coordinated placement puts both in Center before descent: 1 matched strength, 0 damage, perhaps fulfilling Three Stations (Center). Either action alone causes 2 damage and no collision. With one player lacking their SHIFT card the combination isn't available; their hand materially matters.

**Combination B — multi-stage single-token action:** A `+2 NEAR` in Center and `+2 NEAR` in Center would deal 4 damage if unmodified. One player's FLIP on one token yields a `+2/−2` match, preventing 4 damage and progressing Deep Capture. A second player's SHIFT of that same flipped token into Right changes the outcome and may complete a different mission but can reintroduce 4 damage. This is a concrete *disagreement* over strategic priorities; two actions on one token compose according to initiative. In a scenario with a `−2` NEAR in Right, however, the FLIP+SHIFT sequence creates a Right collision and may satisfy a Right-lane mission. The value of the second action depends on the player's mission judgment.

**Private-hand communication example:** A player declares "I can HOLD your near charge, but then I have no HOLD card for the next storm." Another offers a SHIFT to make today's match instead. This is an individual economic tradeoff only if hand depletion proves consequential in reached states; otherwise this feature fails its gate.

## 7. Worked opening and eight-round examples

### Worked opening (three players)

Use an explicit scenario with round 1 wave `L+1, R−1, C+1, C−1` (4 charges for 3 players). All four enter FAR. Suppose player hands permit `HOLD, SHIFT-L, FLIP` this round; the team PASSes all three. All four move to NEAR; no breach, hull remains `7`.

Round 2 wave again enters FAR. The round-1 charges are now NEAR and will breach. Player A has SHIFT-R and targets `L+1`; Player B has SHIFT-L and targets `R−1`; Player C PASSes. Both land Center. Combined with existing Center `+1/−1`, the Center totals become `P=2,N=2`, yielding a matched-strength-2 collision, no hull loss. Deep Capture completes, and Three Stations marks **Center only**. Round 2 incoming cards remain NEAR for round 3.

If only A had shifted, the Center signs would be `P=2,N=1` (1 hull damage), while Right `−1` would breach (1 more hull damage): Deep Capture would **not** complete. The second player enables the result, not merely an extra point.

### Full-session fixture (valid two-player win and loss)

Scenario for **2 players**: rounds **1–6** each add exactly three charges, `C+2,C−2,L±1`, alternating the lone Left charge `+1,−1,+1,−1,+1,−1`. Rounds **7–8** add none as required by the six-wave scenario rule. Mission set `[Deep Capture, Precision Route, Three Stations]`. Give Player A a DAMP card in their initial three-card hand (an admissible order of their 9-card deck). Both players PASS unless noted. Hull starts at 6. This fixture needs **one deliberate intervention**, so it's not simply all-pass play.

| Round | Orders | Breached wave | Hull after round | Missions |
|---|---|---|---:|---|
| 1 | both PASS | none | 6 | no progress |
| 2 | both PASS | wave 1: Center +2/−2, Left +1 | 5 | Deep Capture complete; Precision 1/2 |
| 3 | Player A **DAMPs the wave-2 Left −1 at NEAR**, B PASS | wave 2: Center +2/−2; Left token was removed | 5 | Precision completes; 2/3 missions complete |
| 4 | both PASS | wave 3: Center match, Left +1 | 4 | unchanged |
| 5 | both PASS | wave 4: Center match, Left −1 | 3 | unchanged |
| 6 | both PASS | wave 5: Center match, Left +1 | 2 | unchanged |
| 7 | both PASS | wave 6: Center match, Left −1 | 1 | unchanged |
| 8 | both PASS | no arrivals or residual tokens | 1 | **WIN: hull positive and two missions complete** |

**Counterfactual loss using exactly the same input waves and hands:** if Player A also PASSES on round 3, there are six Left breaches (one in each round 2–7), reducing hull 6→0 in round 7. The team **LOSES on hull**, although both missions completed. A real deterministic Phase 3 reducer must reproduce these totals and card-discard bookkeeping.

**Alternate tactical path to seek in Phase 3:** Replace a Center pair in round 4 with Left or Right charges, forcing the team to use FLIP+SHIFT or a coordinated two-player placement to complete the missions. That is a design challenge, **not a current verified winning strategy**.

**Edge-case check:** DAMP removes a strength-one token immediately; the card is discarded on round 3, and Player A draws one replacement after round resolution. PASS consumes no card and draws none. There are never fewer than three arrivals on rounds 1–6 or extra arrivals on rounds 7–8 in this fixture.

## 8. Exploits, complexity budget, and research requirements

| Risk | Why it matters | Required Phase 3 test |
|---|---|---|
| Quarterbacking survives private hands | Players can fully reveal their hands via voice | Human sessions with/without an experienced leader; count nontrivial independent proposals |
| Always-pass or always-FLIP strategy | Natural matches can satisfy missions automatically | Simulate deliberately passive policy; require wins where at least one coordinated pair is essential |
| More players become less effective | Charges per round grow with player count; card quality is random | Paired benchmarks at 1–4 players, tuned scenarios; no claim of balance yet |
| Combo resolution confusion | Two actions on one token can fizzle / cross a lane | Exact unit tests for ordering, legality, destruction, HOLD+SHIFT, double SHIFT |
| Missions are cosmetic | Deep Capture may be easy in naturally matched waves | Find reached states where mission choice reverses best action |
| Card draw feels unfair | Two players' available interventions may be too weak | Guaranteed playable starter hands / mulligan experiment; reject if strategy is dominated by luck |

- Core verbs: **SHIFT, HOLD, FLIP, DAMP**; no BUILD, power or coolant. One round has arrival → commit → reveal/resolve → advance/collide → mission update/draw.
- Temporary complexity: 1 personal hand/deck/discard per player, up to 2 orders/token/round, three mission counters, rotating initiative, charge state. Compared with Engine: less economy, but more information/card-management burden.
- **Removed relative to v0.5:** Accelerate, Bridge, capacitors, stored power, coolant, two-offer Storm Market, shared four-slot planning. Mechanics must earn their removal or reintroduction in later phases.

**Non-negotiable Phase 3 gate:** at least one full legal winning witness with the specified `players+1` arrivals in rounds 1–6, plus a failing witness for each count; reach-state examples where two different hands require different coordinated plans; measure active decisions per player, and verify limited-information fairness based on actual hands and public next wave. If wins rely on contrived low-threat exceptions, revise before comparison with Engine.

**Current judgment:** Operations has the more distinct 2–4-player interaction hypothesis, but a significantly greater balance and randomness risk. It is not selected merely because everyone holds cards. If independent hands do not produce valuable strategic autonomy, choose a leaner co-op model in Phase 3 instead of adding more secrecy.
