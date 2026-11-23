# GAIM improvement roadmap — Phase 1, iteration 2: Beacon network and active Switchyard

Status: **CONTINUE Phase 1**. Reducers and gate can be tested automatically; engaging strategic decisions and novice comprehension cannot be demonstrated without human players.

## Why this iteration

The initial Beacon prototype permitted a late upgrade that satisfied the final objective without providing meaningful earlier capability. A project-schedule audit of the existing scenarios found complete winning plans with upgrades built in rounds 6–7 (using unmodified archived tactics and the previous rules). The Switchyard's level-1 free move was limited to FAR charges even though most meaningful paid Shift actions in the published winning plans occurred on NEAR charges.

## Rules and product changes

- Beacon orders now require an **upgraded, online system** at the start of the round, plus at least one **opposite-polarity charge collision** in that round. If the planned collision is absent, the live preview flags the plan as invalid rather than allowing a charge to be purchased automatically. A Beacon still costs 2 Power and competes with system construction and shielding.
- All three Beacon cells must be charged **by the end of round 7**. Round 8 is a dedicated survival finale, with no new Beacon or construction projects. The victory requirement remains positive Hull and at least one online upgraded system entering round 8.
- Switchyard level 1 can Shift **any FAR or NEAR charge one lane for free**; level 2 can Shift one charge **one or two lanes**. It is one free move per round and is still disabled by an outage. The free-move control is expanded automatically, and the published First Watch example demonstrates using it on urgent NEAR charges.
- On-screen mission text, warnings, selectable projects, system descriptions, preview, and rules page now communicate the new constraints.
- The older `site/play-engine.mjs`, research reducers, and previous multiplayer implementation remain unchanged.

## Evidence from this iteration

The deterministic project-scheduling audit (`node scripts/audit_phase1_routes.mjs`) holds archived storm tactical edits and current published shielding fixed, and tries every one-build / three-charge schedule. It is deliberately **not** a search for optimal tactics or a proof of strategic balance.

| Storm | Dynamo winning schedules | Aegis winning schedules | Switchyard winning schedules | Latest successful first build |
|---|---:|---:|---:|---|
| First Watch | 19 | 13 | 13 | Round 4 |
| Tough Current | 16 | 7 | 7 | Round 4 Dynamo; Round 3 others |
| Power Surge | 13 | 13 | 13 | Round 4 |

These counts measure feasibility under one fixed action sequence, not win rate or difficulty. All three existing published witness plans still win after the rule changes (sample Hull: 2, 1, 3), and their states agree between the independent Python and JavaScript reducers. The tests explicitly check the Beacon system/meeting requirements, final-round project lock, and Switchyard urgent- and cross-lane movement.

## Remaining Phase 1 validation

1. Conduct five independent, uncoached novice playtests. Do not give participants the sample-plan button initially. Record duration, confusion, decisions, and independent desire to replay.
2. Assess whether each upgrade path actually feels different, whether Switchyard's free movement is too strong, and whether the Beacon/network collision condition feels intuitive or overly restrictive.
3. Evaluate the final-round survival-only pacing, difficulty without sample plans, and whether the preview supports rather than replaces player reasoning.
4. Expand the competitive-strategy and holdout-scenario analysis before declaring strategic balance. Phase 4 later covers final cross-content balance.

A passing release gate is a necessary software condition, not evidence of fun. **Recommendation remains CONTINUE Phase 1** pending human evidence.

## Roadmap remaining

- Phase 1: Core-game strategy, learnability and novice playtests (current).
- Phase 2: Interdependent 1–4-player cooperation.
- Phase 3: Missions, scenarios and replayability systems.
- Phase 4: Balance, difficulty and pacing across content.
- Phase 5: Single authoritative engine and reliable online rooms.
- Phase 6: Visual quality, responsive mobile UI and tutorials.
- Phase 7: Repeat-session validation, targeted content expansion and release readiness.

## Technical verification (November 2026)

- Full `scripts/release_gate.sh` passed locally: 8 reference tests, 255 Python tests, vendored TypeScript build, and 23 Node tests (including the new project-route audit).
- Real Chromium browser checks in an isolated harness (because localhost/data navigation is blocked by the execution environment) replayed all 3 eight-round example victories at 390px viewport. Final-round project locking and open Switchyard controls were exercised; no JavaScript runtime errors or horizontal overflow occurred. This does not verify the deployed GitHub Pages site.
