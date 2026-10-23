# GAIM mechanics pass 16: conditional plans and a disposable public preview

## Decision

**No gameplay mechanic promoted.** Forecast Market v0.5 remains the leading research design; the production engine is still v0.1. Do not interpret this as proof that Forecast Market produces better human cooperation; that remains unverified.

## Motivation

Our last experiments showed that simply splitting forecasts into private pieces very rarely improved survival. The next hypothesis was that teammates could *use* hidden information to build a joint contingent plan, rather than merely report their forecasts.

The site addition is deliberately separate from this rule research. It visualizes canonical v0.1 replay data, not v0.5 or a fabricated online client.

## Proposed conditional edit (research-only, exact rule)

1. Two virtual team edit slots are reserved this round for one **Sealed Pair**.
2. An operator selects one of three public Boolean conditions: `left` (selected incoming storm contains >=2 charges in Left), `negative` (>=2 negative charges), or `large` (>=2 strength-2+ charges).
3. The operator precommits two DIFFERENT legal edits targeting already-visible tokens: **IF true** and **OTHERWISE**. `PASS` can be one branch.
4. After a *previously hidden* storm is selected and revealed, the truth of the condition automatically determines the one action executed. The other committed branch is discarded. Branch actions must be valid in the precommitment state, so hidden charge IDs cannot be targeted.
5. Resolution is delegated to the existing Forecast Market reference reducer. A Sealed Pair is not a new damage/energy rule and cannot edit a token twice.

This rule is **not compatible with the current public-information timing as written**: today's Forecast Market shows the actual offered cards, making a conditional order pointless. The experiment requires a separate and deliberate advance-information schedule. It would also require a server-authoritative commitment lock and guarded trigger verification. Those were NOT added to production.

## Experimental comparison

Used four synthetic hidden-storm worlds for each reached board, with the same public board in every world. Compared the best fixed precommitted edit against the best truthful guarded two-branch edit. The scout can select the better storm offer after the hidden world is revealed. Each outcome was evaluated using a three-round passive continuation and the existing heuristic.

| Dataset | Reached boards | Strict conditional improvement | Best available evidence |
|---|---:|---:|---|
| Development (`261600` onward) | 16 | 4 | Example: if Left-heavy, DAMP #1; otherwise HOLD #4 |
| Holdout (`269600` onward) | 16 | 4 | Example: if Left-heavy, HOLD #5; otherwise ACCELERATE #5 |

Exact machine-readable results: `docs/design/pass16-development.json` and `pass16-holdout.json`. Independent replay/equality tests: `tests/test_phase16_conditional.py`.

### Why no promotion?

- The selection of the conditional *branches* was optimized using knowledge of all hidden worlds. That gives an **upper bound**, not a player-achievable strategy.
- The two reserved edit slots (one executed action) were not subtracted from the heuristic. A strict numerical advantage may disappear when opportunity cost is modeled properly.
- The future cards were synthetic, not the game's balanced official wave generator.
- The current public storm offers already disclose the trigger. To make the mechanic meaningful, we would need to redesign the reveal schedule, which is a serious rules change.
- Information splitting does not stop voice-chat collusion or quarterbacking, and a multiple-choice branch planner could add cumbersome bookkeeping on a phone.

**Takeaway:** conditional commitments have measurable potential, but the current evidence is not sufficient to spend rules complexity. More useful next test: compare interactive human teams with a sealed-commitment structure to teams using open planning, recording independent contributions and frustration as well as win rates.

## GitHub Pages: a temporary mechanics window

New files: root `index.html`, `site/style.css`, and `site/replay.js`. The page reads the actual canonical `contracts/golden-traces.v0.1.json` and allows replaying all seven verified nine-round wins on a portrait screen. It also shows the current research direction with an explicit disclaimer.

- No new server, WebSocket, package dependency, build framework, account system, or gameplay state.
- The UI has **zero authority** to make moves. It is a replay/structure explainer, not a playable game.
- Removing the three page files removes the preview. `contracts/golden-traces.v0.1.json` remains the independent engine conformance fixture.
- Page scripts never import research experiments or game-server modules.
- GitHub Pages currently serves the repository from `/gaim/` and renders the README. A root `index.html` should take precedence on its next successful publish. The user still must run the local hotfix to push changes. If Pages is configured in a way that does not publish from the root of `main`, repository Settings → Pages may require an adjustment.

## Tests and gates

- Exact branch resolution via production-equivalent research step; invalid guards, nonexistent tokens, duplicate branches, and incorrect offer index rejected.
- Paired deterministic development and independent holdout evaluations.
- Site audit verifies source file, seven complete golden traces, clear v0.1/research distinction, and no new network runtime dependency.
- `node --check site/replay.js` and a browser-rendered smoke check of the replay stepper at 390 px width performed in the development environment.
- The existing full release gate continues to protect all historical Python, TypeScript, golden replay, and multiplayer behavior.

## Future research candidates, not implemented

1. **Deferred mutual commitments** — each player proposes one action and a teammate supplies a trigger. Must demonstrate it helps more often than a single open-planned action, after the reserved-slot cost.
2. **Shared storm hand** — players hold different upcoming storms; the team negotiates which cards to release into the shared queue. Must be robust to voice-chat information sharing.
3. **Public emergency protocols** — a few predefined IF/THEN patterns selected by consensus, potentially less bookkeeping than arbitrary conditionals.

The standard is still to accept **no** rule unless it improves the frequency and quality of strategic and genuinely cooperative decisions.
