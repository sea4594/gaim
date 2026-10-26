# Redesign Phase 7 — Human-Operable Cooperative Turn Lab

**October 26, 2026. Gate: NOT PASSED.** The playable phase is implemented, but we have **not conducted human cooperative playtests** and therefore cannot claim the game is enjoyable, resists quarterbacking, or gives everyone satisfying autonomy. No research mechanic is approved for production. Storm Engine remains the provisional chassis; Flexible Crews remains a research candidate.

## The question this phase actually tests

Phase 6's staffing system could make four work units available, but in only 49 of 320 holdout rounds did all four automated seats perform an active action. Mere station assignment was not meaningful participation. Phase 7 changes the method: make *seat-specific decisions inspectable and playable* and quantify when replacing an individual seat's commitment changes the actual outcome. Do not inflate the economy again or add fake secret information to manufacture interaction.

## Delivered: two complementary tools

### A. Static portrait cooperation sandbox (publishable on GitHub Pages)

`crew-lab.html`, `site/crew-lab.css`, `site/crew-lab.js`, `site/crew-lab-data.json`, published via the **existing GitHub Actions Pages workflow**, show two experimental Storm Engine situations. All four seats choose independently between Navigation, Control, Engineering, and Dispatch. The four-worker staffing choices are enforced as in the Phase 6 reducer: no station may receive three workers, and construction and Dispatch must both be paid from power already stored at the start of the round. The browser does **not** implement a new reducer or calculate rules outcomes: every one of its 512 allocations was precomputed from the Python reducer in `experiments/redesign_phase7/decision_lab.py`. No login, backend, account storage, or permanent UI framework is introduced.

There are two dilemmas:

- **Finale crisis (round 7):** one remaining hull, two stored power, Aegis at level 1, an imminent strength-2 threat to the unprotected Right lane. Engineering must finish Aegis while someone else prevents a fatal leak. Round 8 is executed with no further actions to test the actual terminal result and leftover-charge deadline.
- **Junction (round 4):** productive lane collision, an exposed lane, three stored power, an incomplete Dynamo. The team can develop production or cover the hazard. This is a midgame economy/tradeoff demonstration, not a terminal victory evaluation.

**Important limitation:** Within each staffed duty, the browser uses **one fixed disclosed order** (e.g. Navigation shifts a particular token). This means it is a *decision sandbox about workforce allocation*, not a complete playable game or four human-selectable tactical hands. Many selections are invalid because they oversubscribe a duty or cannot pay for their intended orders. The UI correctly shows those failure reasons rather than silently repairing a team's plan.

### B. Full eight-round local human pass-and-play

`experiments/redesign_phase7/pass_play.py` supports one to four people at a shared terminal. Every player chooses their worker's station; tactical workers select an actual legal token edit or PASS, Engineering chooses build/service/PASS, and Dispatch chooses protection/recharge/PASS. The experiment uses the **unchanged Phase 6 crew reducer** and the Phase 3 waves. The player count does not alter total work resources. Actions, outgoing results, and the seeded full wavebook are saved only to a requested local JSON file; the saved decisions can be verified by replay. No hidden forecast is shown ahead of time in the interactive prompts, even though the full wavebook is retained for deterministic reproduction.

From the repository root:

```bash
python3 -m experiments.redesign_phase7.pass_play --players 4 --seed 7001 --out /tmp/gaim-human-playtest.json
python3 -m experiments.redesign_phase7.pass_play --verify /tmp/gaim-human-playtest.json
```

Human playtesting must occur **after** this package is installed. Automated terminal fixtures verify that all player counts function and session logs reproduce; those fixtures do not stand in for real people.

## Exact exhaustive allocation results

For each scenario, all `4^4 = 256` seat allocations were generated and checked. Changing one seat's duty creates a *directed* comparison: reversing a pair is counted separately, and only transitions between two legal allocations count toward the denominators. **Changing a stored statistic is not the same as strategic agency**; players may never prefer those choices. Even a win/loss reversal is a curated fixture, not population-level co-op success.

| Comparison | Round-7 crisis | Round-4 junction |
| --- | ---: | ---: |
| Combinations checked | 256 | 256 |
| Legal combinations | 132 | 204 |
| Invalid/oversubscribed/unaffordable | 124 | 52 |
| Unique recorded outcomes | 7 | 9 |
| Legal directed one-seat alternatives | 792 | 2,016 |
| Alternatives changing the recorded state | 504 | 1,536 |
| Alternatives changing win vs loss | 168 | 0 |

### Actual reversible result

The published fixture contains two **legal** four-seat assignments differing only in seat 3:

- `Navigation / Navigation / Control / Engineering`: the Control worker damps the imminent charge, allowing Aegis to protect the settlement while an upgrade completes. The eighth-round test ends in **WIN**.
- `Navigation / Navigation / Engineering / Engineering`: doubling Engineering discounts construction, but nobody damps or covers the threat. The settlement is destroyed (**LOSS_HULL**).

This proves a seat's decision can matter even though the payoff of a second Engineer is tempting. It does **not** mean the interaction remains interesting once the solution is known, or that human players prefer it over a centralized plan.

### Counterexample to hype

In the junction scenario, **1,536** directed choices change the recorded state, but **zero** change the eventual game outcome because it is not yet evaluated (the simulation stops after one midgame round). If we advertised those changes as 1,536 meaningful human decisions, we would repeat the flawed interpretation that Phase 6 exposed.

## Small, practical human-playtest protocol (not yet run)

Play with **2, 3, then 4 people**, in addition to a solo controls session. Use new random seeds rather than rehearsed best outcomes. Before the round, ask each player to write a preferred objective (defend, build, produce, or reposition) without discussing it. Then allow open discussion, assign workers, submit actual station orders, and resolve. Every two rounds, quietly ask each participant:

1. Did you propose or change a plan, rather than merely agree with one?
2. Were there at least two *plausibly good* choices for you?
3. Did someone else's choice make your intended action more or less valuable?
4. Did you have to wait for a role or action to become useful?
5. Did any participant dictate the plan while others simply executed it?
6. How long did explanation, discussion and the actual turn take?

After the session, have everyone separately rate engagement, clarity, and desire to replay. Record action ownership, actual changes of mind, individual decision proposals, periods of passivity, and time per round; don't accept a nominal station count as a proxy. **No human metrics or endorsements have been fabricated.**

## Rejection risks already visible

1. **Procedural overhead:** staffing choices + station orders require extra steps. The browser demonstrates this sharply: some plans are invalid solely because they cannot afford both jobs. An intelligent human interface may need to show opportunity costs *before* commitment.
2. **All-public quarterbacking:** one skilled solver can still assign all four stations; separate dropdowns do not fix the social dynamic.
3. **Dependent participation:** two workers can staff Engineering but only one chooses the building. The other may contribute a tangible cost discount while having no independent decision about the upgrade.
4. **Scenario cherry-picking:** the finale is deliberately a high-pressure, solvable example. Its many win/loss-changing alternatives cannot be generalized to whole matches.
5. **No tested limited information:** introducing private information without a payoff would risk making discussion and fairness worse.

## Phase verdict and roadmap

**Deliver the human-operable test harness; do not promote the crew architecture.** Phase 7's implementation and machine-verification objectives are met. The **cooperative-quality gate remains OPEN** until human testing produces evidence of individually useful judgment and positive engagement. Do not spend months designing content around the current four-duties system without that evidence.

- **Phase 8 — Replayability and strategic variation:** develop scenario/missions that change which long-term Engine investment is sensible. Keep a parallel checkpoint for human-turn evidence; do not mislabel replayability as solved cooperation.
- **Phase 9 — Balance and simplification:** explicitly address Aegis dominance, overly easy staff discounts, rule load, unequal round utility, and decision friction. Evaluate action ownership as well as outcomes.
- **Phase 10 — Production multiplayer and portrait UI:** only after the board-game chassis and co-op architecture pass their acceptance criteria; implement in canonical TypeScript and the online room system.
- **Phase 11 — Whole-game review:** comprehensive human/automated audit of strategic depth, accessibility, replay desire, quarterbacking and 1–4 players.

This is intentionally not a claim of a complete modern cooperative board game. It is the first GAIM phase in which the actual co-op choices can be inspected on a phone and exercised by people through a complete headless ruleset.
