# GAIM redesign — Phase 2 candidate competition brief

**Status:** Starting hypotheses for the *next phase*, **not** accepted rules. The candidate pool may pivot if another premise offers stronger choices. Phase 2 must generate two **complete** implementable board games, not feature lists.

## Candidate A — Storm Engine (persistent strategic position)

**Core question:** Can the charge-collision puzzle supply scarce power to a settlement that the team actually develops and defends, with different viable infrastructure paths?

### Hypothesis to falsify

A compact shared settlement with a small number of development decisions can make early choices change later tactics and create competing uses for power, without accumulating six separate token-manipulation verbs plus a resource spreadsheet.

### First rule experiments to specify in Phase 2

- Keep one clear storm resolution mechanism; define where generated power goes and whether existing three capacitors remain.
- Choose **2–3 persistent systems at most**. Each must have one distinct, active consequence, one vulnerability, and a cost. Candidate functions: production efficiency, defense, mission completion.
- Scarcity: players cannot fully develop everything. The same generated resource must fund different priorities. Specify exactly when upgrades take effect.
- Choose a victory objective **other than just a meter fill**, or prove meter fill is the better choice.
- For co-op, test personal portfolios or conditional promises that influence a *shared* infrastructure decision, not merely four copies of the same edit.

### Test that could kill it

If construction is either always worthwhile early or never affordable, or if the settlement introduces many upkeep rules without changing tactics, reject/pivot. If all meaningful planning can still be dictated by one optimizer, revise the co-op layer rather than adding artificial secrecy.

## Candidate B — Storm Operations (mission-led teamwork)

**Core question:** Can charge timing become the engine of a tightly coordinated 1–4-player board game in which players have complementary options/information without carrying a long-term economy?

### Hypothesis to falsify

A limited common action vocabulary, different genuinely useful player resources, a public mission with an evolving constraint, and simultaneous commitments could create cooperation and replay value with fewer rules than Storm Engine.

### First rule experiments to specify in Phase 2

- Design one **clear mission arc**: setup, commitment, unforeseen but forecastable complication, finale. What changes strategically from the early to late phase?
- Assign each participant a contribution that meaningfully changes the joint plan; do not give 3–4 players token chores. Make 1-player a coherent alternate form, not a four-handed puppet show.
- If information is private, specify what can be communicated via free chat and why simply telling the strongest player the answer isn't enough. Prefer genuine commitment constraints to secret trivia.
- Use a small family of missions that require **different decisions**, not new victory numbers. Specify at least two divergent viable plans in one mission.
- Minimize random failure: every irreversible commitment must have legible risk and available mitigation.

### Test that could kill it

If the game remains a single global puzzle whose solution one player can calculate and dictate, or mission variety only rearranges charges, reject/pivot.

## Third contender: Current Forecast Market v0.5

Use the recorded research rules, NOT production v0.1, as a **no-redesign control**. We should be willing to retain the control if A or B creates more bookkeeping than strategy. Production v0.1 remains the cross-language technical regression control.

## Exact contents required from *each* candidate

1. One-paragraph playable pitch **in verbs**, not setting/theme.
2. Components/board, including portrait mock layout and information layers.
3. Setup for 1/2/3/4 players, including solo controller workload.
4. Complete round sequence with ordering, action and resource costs, tie/conflict resolution.
5. Opponent/storm behavior with either deterministic resolution or explicit probabilistic model.
6. Victory, defeat, stalemate, session end, timing edge cases.
7. Worked first two rounds and a coherent full successful/failing scenario.
8. An **early** fork with two plausible paths that diverge several rounds later.
9. Two mechanically different joint-action situations; one should involve information or commitment, not merely two shifts.
10. Rule burden ledger (verbs, phases, resources, exceptions) and an intentional list of **mechanics removed** versus v0.5.
11. Three likely dominant strategies/exploits to test immediately.
12. How the design meets the charter, or an honest list of contradictions and unresolved choices.

**Phase 2 deliverable:** Two full draft rulebooks plus candidate scorecards and an example-session log; no production migration. Phase 3 builds both before selecting a winner.
