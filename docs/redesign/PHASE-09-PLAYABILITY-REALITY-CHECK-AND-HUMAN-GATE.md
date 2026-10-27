# GAIM — Phase 9: Playability Reality Check and Human Gate

**October 26, 2026. No multiplayer/production rules promoted.**

## Why this phase replaces the original balance sprint

The project has accumulated about eight redesign phases and many prior mechanics tournaments but still hasn't shown the user a full playable game or complete accessible rules on their published homepage. Older Pages builds emphasize v0.1 replay clips and research scoreboards. This made the project appear much more finished than it is. Before optimizing more systems, expose the full loop and subject it to human scrutiny.

## Delivered on the published-site pathway

- `play.html` — complete **solo** eight-round, no-login browser game using the Phase 3 experimental Storm Engine rules. Choose a three-climate-independent, fixed-seed wavebook; select charges and SHIFT/HOLD/DAMP, buy upgrades, use the optional Switchyard free action, resolve damage and collateral effects, win or lose. An example plan can be loaded for any round if the user's path still exactly matches the verified witness. This is manual game state progression, *not* a click-through replay.
- `rules.html` — complete human-readable rules, costs, turn sequence, outage/deadline edge cases, example collision, and explicit bounds of the prototype. Homepage now makes PLAY and RULES the first actions. The nine-round v0.1 replay remains clearly labelled historical.
- `site/play-engine.mjs` — isolated JavaScript port of the existing Phase 3 Python reducer (research only). No network gameplay, no account backend, no dependency lock-in, no change to authoritative production TypeScript v0.1.
- `site/play-cases.json` — three independently regenerable eight-round wavebooks (5000, 5009, 5011) with full Python replay witnesses. Hints are **not** AI suggestions under alternate game states. Their availability is guarded by exact state equality.
- `tests/test_redesign_phase9_browser_play.py` — full-script replay parity plus 35 randomized, full-session independent cross-language comparisons; asset build/rules integrity; invalid-order safeguards. Existing historical replay tests remain in force.
- GitHub Pages artifact allowlist updated with just the public html/css/js/JSON assets. `build-info.json` identifies the browser as `playable=true`, `play_mode=solo-experimental-storm-engine`. The source GitHub Pages deployment workflow can publish this without a server.

## Exactly what the tests prove

1. Three complete sample victories replay byte-for-byte at the state-data level in both the Python and JS reducers.
2. Thirty-five additional randomized full-game decision sequences produce identical outcomes and complete states in both languages. These include all three tactical action kinds, system construction, and Switchyard opportunities.
3. Chromium executed the real interactive UI at a 390-pixel mobile viewport, loaded a sample plan, resolved eight rounds to victory with no page JS errors and no horizontal overflow. Browser navigation to a localhost URL is blocked by the test environment; the assets were injected unchanged into `about:blank` with the normal scenario fetch stubbed from the generated JSON. Therefore the result validates the UI/gameplay path, not actual external GitHub Pages publishing.
4. Full project gate passes: v0.1 Python mechanics, Python research contracts, TypeScript compilation, golden traces and Node room/server tests. The installed Pages app remains an experimental local JS reducer rather than production logic.

## Serious game-design weaknesses *not* fixed by the demo

- The v0.1 production game and experimental Storm Engine are distinct rulesets. There is still no integrated, online-playable Storm Engine, even though a production network engine exists for the old v0.1 ruleset.
- Solo Storm Engine has centrally controlled edits and construction: **no cooperative human interaction**. Any claim that two/four players enjoy it would be fabricated.
- Only three fixed wavebooks are in the playable UI; replayability beyond those scenarios is unproven.
- Aegis remains frequently dominant under existing heuristic tests; Switchyard's potential remains under-explored.
- No controlled novice tutorial sessions, board-game-level rulebook usability testing, engagement surveys, session-time studies or desire-to-replay measurements have been completed.
- The browser implementation is deliberately small and functional; interface polish is not evidence of game quality.
- The selected Phase 3 economic goal (restore 2 systems to level 2) may be too mechanical or monotonic to anchor a compelling eight-round narrative.

## Strong acceptance tests before claiming a compelling modern cooperative board game

**A — Learnability:** At least 5 genuine first-time testers complete a game without developer facilitation and can correctly explain movement, cancellation, construction delays and victory. Note rule ambiguities, confusion, and elapsed time. This cannot be simulated by code.

**B — Enjoyment:** After play, participants independently rate tension, agency and desire to replay. Require credible evidence that people want a second game; negative feedback must trigger rule simplification, not visual polish.

**C — Strategic variety:** Across matched seeds and two competent planning policies, show that at least two materially distinct long-term investments have non-trivial winning opportunities; no automatic defensive purchase order dominates. Track costly choices and counterfactuals instead of just win frequency.

**D — Genuine multiplayer:** Build a minimal shared-room four-seat prototype only after the solo rules are comprehensible. Test with 2, 3 and 4 actual people. Track each player's initiated proposals, active independent choices, role passivity, and whether one player narrates every move. No fake private information just to limit communication.

**E — Rules economy:** If a rule (three systems, outages, coolant, delayed build, free shift) does not repeatedly create an interesting tradeoff in human sessions, cut it rather than justifying it with mathematical rarity.

## Adapted roadmap

1. **Next — Structured novice solo playtests plus economic balance/simplification.** Play from the live page. Collect real evidence; investigate the dominant Aegis pattern; remove unintuitive systems. This gate is not passed until genuine testers play.
2. **After that — Prove a multiplayer turn.** Move only the accepted prototype into minimal shared room play, validate simultaneous individual contributions and cooperative opportunities with humans, including 1–4-player scaling. Do not promote a cosmetic four-role interface.
3. **Then — Variety and balance.** Only after the core is enjoyable, test missions and scenarios that make different plans viable and produce a satisfying arc.
4. **Then — Production integration.** Implement accepted rules and multiplayer in the TypeScript canonical engine with deterministic parity, robust online rooms, and the portrait-first UI.
5. **Finally — Board-game-level review.** Audit fun, replay demand, strategic variability, communication, clarity, pacing, and failure explanations. If the design remains a tactical puzzle rather than a satisfying co-op board game, pivot instead of claiming completion.

**Current status:** Research prototype playable solo; no evidence yet of a good multiplayer board game. Honest green: software parity and interface. Honest red: human engagement and team agency. Neither UI nor win percentages are substitutes for those gates.
