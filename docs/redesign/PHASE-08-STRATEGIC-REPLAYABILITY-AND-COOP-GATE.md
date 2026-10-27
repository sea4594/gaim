# GAIM Redesign Phase 8 — Strategic scenarios, live-site experiment, and cooperation gate

## Decision

**Experimental scenario framework accepted as a tool; no new game rules promoted.** Storm Engine remains the provisional strategic chassis and Forecast Market remains an older research control. The game's four-person cooperation gate remains **OPEN**: no human test session took place.

This phase creates three public storm climates while keeping **the Storm Engine reducer, starting hull (6), power (2), coolant (2), two edit slots, eight-round length, construction costs, and victory requirements identical**. Wave characteristics change; upgrade capabilities do not. Each climate admits every build path, and seed lists remain public. This is a fairly small, falsifiable test of whether the *same* strategic priorities work everywhere.

## Complete scenario definitions

- **Resonant Harvest:** seven arrival rounds of opposite-polarity pairs that share a lane with probability 0.83, plus a strength-1 extra charge with probability 0.20. The normal strength distribution is `[1,1,2]` for each paired charge. The eighth arrival is empty. A prolific collision environment should increase the value of power growth.
- **Fractured Currents:** seven rounds of opposite-polarity pairs *always* starting in different lanes; a single extra strength-1 charge occurs with probability 0.40. All strength distributions unchanged. This stresses positional choices. **Caveat:** the policy does not use Switchyard's free shift, so this test substantially understates the system's tactical potential.
- **Shatter Siege:** seven rounds of opposite-polarity pairs sharing a lane with probability 0.55, each strength 1 or 2; an extra charge with probability 0.70, also strength 1 or 2. This stresses hull and defenses.

The deterministic generator is seeded by climate and integer seed; each profile is fully disclosed. They are **not equivalent-difficulty** climates: assessing *variation* is not the same as assessing fairness or balance. No secret information is introduced or simulated.

## Fully reproducible paired tournaments

The same 3 fixed upgrade sequences are tested under the same seed per climate, with the same Phase 3 one-ply edit agent. The policy does not dynamically switch strategic goals, optimize free Switchyard shift, or emulate independent teammates. Numbers are full-match **wins out of 40**, *not* human win rates.

| Climate | Development: Dynamo+Aegis | Development: Aegis+Switchyard | Development: Dynamo+Switchyard | Holdout: Dynamo+Aegis | Holdout: Aegis+Switchyard | Holdout: Dynamo+Switchyard |
|---|---:|---:|---:|---:|---:|---:|
| Resonant Harvest | 36 | 24 | 32 | 35 | 25 | 33 |
| Fractured Currents | 32 | 30 | 24 | 33 | 29 | 20 |
| Shatter Siege | 26 | 30 | 18 | 28 | 28 | 15 |

Development seeds: `81000–81039`. Untouched holdout seeds: `82000–82039`. The holdout maintains the broad divergence in Dynamo+Switchyard survivability: **33/40 in Harvest vs 15/40 in Siege**. In Siege, Aegis+Switchyard rises relatively, although it only ties Dynamo+Aegis on holdout.

**Counterevidence to promotion:** Dynamo+Aegis is best or tied for best in **all three holdout climates**. Aegis is still generally overvaluable, and the simple policy can fail to exploit its Switchyard purchases. These climates do not yet demonstrate three comparably viable strategies. They are only a valuable *test distribution* for subsequent tuning.

### Two named counterfactual examples

All examples use exactly the same storms inside each row, changing only which pair of upgrades is pursued:

- Harvest seed `82002`: Dynamo+Aegis and Dynamo+Switchyard both **WIN**; Aegis+Switchyard **LOSS_SYSTEMS**.
- Harvest seed `82001`: Aegis+Switchyard **WIN** while the two Dynamo-containing orders lose (different failure reasons). This prevents an inaccurate claim that Dynamo is a guaranteed best plan in Harvest.
- Siege seed `82000`: Dynamo+Aegis **WIN**; Aegis+Switchyard and Dynamo+Switchyard **LOSS_SYSTEMS**. This is counterevidence to claiming the defensive opening is universally superior on any specific Siege seed.

The complete eight-round state and decision replay for five fixed holdout seeds per climate is available on the **GitHub Pages website**. Each screen state derives from `experiments.redesign_phase3.engine.step()` and is checked back against that reducer in automated tests; the website contains no duplicated game rules.

## Human cooperation: acceptance gate remains open

A precomputed strategy chart is not a human multiplayer test, nor is a seat-specific dropdown genuine agency. Phase 7 supplied an 8-round terminal human playtest harness and interactive public seat-contribution examples, but no recorded 2–4-human sessions are available for analysis. The team cannot yet assert: resistance to quarterbacking, fair player contribution, satisfying disagreements, multiple compelling strategic paths, acceptable cognitive load, or desire to replay.

Suggested future playtest method (run as an in-browser multiplayer prototype in Phase 10, not a terminal-only demo): sample unfamiliar seeds, individually elicit early investment preferences **before** team discussion, record how proposals evolve, note whether all four people can change the actual outcome, collect personal enjoyment/replay/clarity feedback, and log round elapsed time. Do not treat surveys as automated evidence or write fictitious player feedback. These protocols remain proposals until actually performed.

## Pages preview: directly on the live site

`https://sea4594.github.io/gaim/strategy-lab.html` is a static interactive **research exhibit** with climate choice, development path, scenario seed, eight-round board snapshot, hull/power/upgrades, actual edits, and win/loss, plus held-out 40-game comparisons. The GAIM homepage directly links to the exhibit. It requires **no download, local server, or CLI** for visitors after deployment. Existing Phase 7 crew lab and verified v0.1 replay remain available. Website build intentionally includes only whitelisted public HTML, CSS, JS and checked-in simulation data; it does not ship Python experiments or the server.

The public URL will not change until the user applies the hotfix to GitHub and the Pages deployment succeeds. If the public site continues showing the old Phase 6 README, inspect repository **Settings → Pages → Source → GitHub Actions**, then Actions → **Deploy verified GAIM preview**; the deployed `build-info.json` marker should read `gaim-pages/redesign-phase08`. No response can claim this has been deployed without verifying the live URL.

## Gate and next phase

- Phase 8 research tooling **done**: deterministic climates, 80 seeds per climate across two sets, same-seed three-strategy matchups, exact full-game witness replays, browser-only preview, and release-gated site artifact.
- Phase 8 strategic variety acceptance **partly unmet**: still an overpowered generally safe build, no human evidence; do not promote any climate as official gameplay content yet.
- **Phase 9 — Balance and Simplification:** improve defense/production tradeoffs, implement and test a competent free-shift policy, revisit construction discount and inactive workstations, reduce invalid commitments, and run controlled head-to-head tournaments. Human co-op gate still required.
- **Phase 10 — Production Multiplayer and Live UI:** implement accepted (not merely promising) rules with deterministic TypeScript parity and an actual browser-based multiplayer client accessible from the GitHub Pages homepage. GitHub Pages is static; online rooms require a separate deployed server or an explicitly different architecture. Do not claim the current Pages prototype supports network rooms.
- **Phase 11 — Whole-Game Review:** human playtests across 1–4 players, replay desire, difficulty, quarterbacking, session arc, rules elegance, and a final acceptance or further-pivot decision.

**Research verdict:** useful, visibly explorable test distributions; not yet the compelling cooperative board game we need.
