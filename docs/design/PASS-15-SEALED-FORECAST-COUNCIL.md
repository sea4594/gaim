# GAIM Mechanics Exploration — Pass 15: Sealed Forecasts, Shared Decisions, and Limited Information

**Decision: no new rules promoted.** Forecast Market v0.5 remains the research control; shipping game rules remain v0.1. This pass tests whether *private forecasts can create actual cooperative value*, not merely whether information hiding reduces performance.

## The design problem

The old design gives every player the same complete board and all available actions. This invites one-person quarterbacking. On the other hand, simply hiding public information is not inherently an improvement: it can make a fair tactical problem into a guessing game. A player who has no special decision to make becomes an unpaid messenger, not an interesting teammate.

This pass investigates **advance commitments with divided storm forecasts**. The first implementation deliberately stays an isolated, headless research protocol. It does not modify the game engine or network server.

## Eight materially different design directions

| Idea | Fully specified kernel | Principal risk / disposition |
|---|---|---|
| **1. Sealed Forecast Council** | Storm cards have public token counts, but one player sees routes while another sees polarities. An operator must lock one edit targeting an *already visible* charge before the storm is revealed; a scout chooses an offered storm. A limited truthful signal can precede the lock. | **Implemented and benchmarked.** Meaningful in some situations; observed effect too infrequent. |
| **2. Team contingency orders** | Before opening the storm, two players jointly author an order `IF this lane receives a negative storm, SHIFT token X; OTHERWISE HOLD token Y`. The conditional order occupies two of four edit slots, so it is more adaptive but costs flexibility. | Strong next hypothesis; more rules and harder parsing. Requires independent implementation and measured tradeoffs. |
| **3. Signal as an action** | Instead of manipulating a charge, a player spends an edit to publicly reveal the exact polarity of one offered storm. No free verbal retransmission during the sealed planning phase. | Risks penalizing coordination and being bypassed by voice chat. Reject until conditional precommitments matter often. |
| **4. Shared forecast hand** | Each player privately owns one future storm card; the team chooses which of these arrives, with unchosen cards carried forward. Players may reveal only one public trait per round, but storm ownership rotates to scale 1–4. | May create interesting tension and different storm order, but card ownership and 4p fairness are not established. |
| **5. Open negotiation + silent execution** | Publicly discuss the plan, then deal private storm details and lock actions without talking. All committed actions reveal together. | A playable co-op social experiment, but outside voice/chat can bypass restrictions; cannot claim technological enforcement. |
| **6. Private obligations** | Each player receives a private project goal that adds a collective bonus if achieved. All objectives must be team-aligned; players cannot profit individually at the team's expense. | Increases bookkeeping and may create irrelevant secrets or conflicting incentives. Reject without distinct mid-game strategic paths. |
| **7. Cross-seat risk allocation** | Each player privately selects one of two system pressures to insure; overlapping insurance wastes coolant while uncovered systems remain vulnerable. Plans resolve simultaneously after forecast arrival. | Could be mostly a guessing/coordination tax. Needs a mechanically justified consequence of duplicated coverage. |
| **8. Forecast-shaping vote** | Scout proposes the next storm; one teammate must commit an intervention before seeing the proposal. Another can veto at a known resource cost. | Risks turning a useful market decision into paperwork. Avoid until we have compelling evidence of separate agency. |

This is intentionally not another list of new combat powers. The promising designs change **who knows what, when decisions become binding, and how one contribution affects another**.

## Implemented experimental rules (exact)

**Board and resources:** Retain the v0.5 Forecast Market board, storm and charge physics, and existing action legality.

**Public observation:** All participants see hull, energy in three capacitors, coolant, currently visible charges, current round, and *number of tokens* on each of two offered storm cards. The public data does not include exact lanes, signs or strengths of the offered cards.

**Private observations:** A route sensor sees lane indices for each charge on the two cards; a polarity sensor sees each charge's signs; a strength sensor sees magnitudes. These are deterministic projections of the same authoritative cards. The public view is identical in alternative hidden worlds with identical visible token counts.

**Sealed edit:** One operator can submit `PASS` or one ordinary legal edit targeting an already-visible charge. Editing a newly entering, unrevealed charge is prohibited. The storm scout chooses offer 0 or 1. The two contributions resolve using the *unchanged* experimental Forecast Market reducer. The new mechanic introduces no extra damage or bonus scoring.

**Signals:** Three tested truthful one-bit reports are (a) whether offer 0 has more left-lane charges than offer 1, (b) whether offer 0 has more negative charges, and (c) whether offer 0 has more size-2 charges. These are truthful facts, not an unrestricted codebook of arbitrary signals.

**One player:** The full forecast is available and the single player may make both decisions, with no added administration. **Two to four players:** Role rotation and splitting of the remaining action slots need separate human testing; this laboratory measures one scout/one operator only. It would be misleading to call it a complete 4p rule system.

**Communication:** The design could optionally have a silent lock window. This is unenforceable against off-app voice chat. Rules must remain enjoyable when people share information verbally; an invented prohibition is not a substitute for player agency.

## Reproducible experiment

`python3 -m experiments.phase15_survey --cases 80 --start 210000 --horizon 3 --metric survival`

Repeat with `--start 211000` for an independent seed range.

- Each reached board is produced by playing exactly two rounds of Forecast Market using a fixed deterministic draft choice.
- For each board, sample **four different hidden storm worlds**. They differ only in the two hidden offers. Each storm has the same publicly visible token count, and the underlying current board is identical across all four worlds.
- Enumerate `PASS` and every legal **single edit on already visible charges**, paired with both storm choices.
- Continue the selected outcome through a fixed three-round horizon, with no further edits and the older offer chosen subsequently. This passive continuation is intentionally simple, not a human or optimal planner.
- For each hidden world, the scout is assumed capable of choosing the better offer **after** the operator's edit is fixed.
- **No signal:** one edit must be chosen to maximize mean outcome across all four worlds.
- **One truthful bit:** one action may be chosen for each of the two publicly reported bit values. The receiver is optimized with full knowledge of all worlds: an **upper bound**, not a demonstrated learnable strategy.
- **Two truthful bits:** receiver can act on route+polarity reports. Again, this is an optimistic upper bound.
- **Perfect forecast:** edit may be chosen individually for each hidden world. It is necessarily at least as capable as the limited-information versions; it does not make the game more fun by itself.

The study evaluates both **three-round survival** (interpretable, binary) and the existing **heuristic utility** (sensitive to hull-loss penalties and not a win probability).

### Results: three-round survival (80 boards and 320 hidden worlds in EACH set)

| Measurement | Development | Holdout |
|---|---:|---:|
| Boards where perfect forecast changes best survival decision | 5 / 80 | 5 / 80 |
| Boards where optimally coded one-bit signal could help | 5 / 80 | 5 / 80 |
| Boards where truthful route+polarity signals can help | 4 / 80 | 5 / 80 |
| Boards with strictly complementary two-sensor information | **1 / 80** | **1 / 80** |
| Mean survival-probability gain from two reports | 0.015625 | 0.015625 |

See `docs/design/pass15-results.json` for the disaggregated individual signals and replay witnesses. The fraction is **expected survival across synthetic worlds under a passive continuation**, not human survival, a game win rate, or a confidence interval for actual play.

### Heuristic comparison: why naive metrics mislead

Under the same three-round continuation, the heuristic reports larger benefits because some changes prevent an early hull-loss state, which scores around -1200. Perfect information matters in 36/80 development boards and 29/80 holdout boards by that score; the two factual signals are strictly complementary in only 3/80 and 4/80 boards. This is not convincing evidence of a broad social gameplay improvement. The survival-based result is the more grounded comparison.

### Concrete example

At development seed 210022, the same public round-two board contains an approaching +2 charge in Right and two smaller positive charges in Center. In some hidden worlds `HOLD` on that +2 is the best advance edit; in others moving a different token one lane is better. The private market offers are the only differences. The witness contains exact token positions, offered cards, and counterfactual survival results. **This is a real information-dependent strategic choice**, but it appears too rarely under the current storm system to justify hiding every future forecast.

## Design verdict

**Reject Sealed Forecast Council as a mandatory new rule at this time.** It creates occasional meaningful information dependencies, but its measured effect on survival is modest, and it restricts the ability to respond to newly spawned storm tokens. It has not solved quarterbacking or demonstrated satisfying four-player agency. Introducing it now would increase complexity without clear evidence of fun.

**Keep for the next pass:** A stronger **two-step conditional commitment** where one player can make a valuable, risky promise and another can enable or rescue that promise. To deserve promotion it should meet all of these gates:

1. In at least a substantial minority of reachable mid-game boards, two *different* player decisions interact to change the best plan, not merely the absolute score.
2. Both using and withholding the commitment can be correct in reproducible, understandable examples.
3. With two and four players, independent contributions matter beyond merely learning then transmitting hidden facts.
4. Solo mode is equally coherent without playing four separate characters.
5. Forecasts are fair under **only** the information actually exposed to the players.
6. At least one meaningful rule could be removed if the new mechanic survives; we should not keep growing the action list.
7. Test real people, including voice-chat groups. Simulations cannot prove perceived agency, tension or enjoyment.

## Important scientific limitation

There is no theorem that limiting player information makes a strategy game better. In an otherwise identical game, giving the team strictly more information cannot make the mathematical best achievable outcome worse. What limited information may improve is **the process of cooperative discovery and communication**. We have not measured that process with people. Prior tests showed that arbitrary action-menu restrictions made the game worse; these results counsel the same caution with secrecy.

**No files in production `src/`, `server/`, `contracts/`, or the existing release gate are changed.** This pass is reproducible research only.
